#!/usr/bin/env python3
"""Build records: what went into each finished video, so it can be checked and rebuilt from the assets.

  python3 kit/builds.py list
  python3 kit/builds.py show c3-Aplus-landscape
  python3 kit/builds.py check c3-Aplus-landscape --data path/to/5bx-charts.json     # up to date, or exactly what changed
  python3 kit/builds.py rebuild c3-Aplus-landscape --data path/to/5bx-charts.json    # same inputs, same settings -> a new video in out/

build.py writes builds/<id>.json after every full render (not previews, not --only). The video files themselves are not kept in git
(too big, and they can be remade); the record is. Id = c<chart>-<level>-<format>[-<tag>], so each chart has one name per variant:
  c3-Aplus-landscape        chart 3, level A+, landscape        c3-Aplus-landscape-mat    the same with a tag (--tag mat)

A record holds: the plan file (name, hash, where it lives), the look/scene/strip settings (hashes), every strip sheet used per slot with its
hash and its library id, the fonts, the code version, the ffmpeg version, the exact arguments, and the result (length, size, hash).
Only the plan file lives outside this kit: pass it with --data, or set FIVEBX_DATA.
"""
import argparse, hashlib, json, os, re, subprocess, sys, datetime

HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE); BUILDS = os.path.join(ROOT, "builds")
def jload(p): return json.load(open(p))
def h12(b): return hashlib.sha1(b).hexdigest()[:12]
def fh(p): return h12(open(p, "rb").read())
def rel(p): return os.path.relpath(os.path.abspath(p), ROOT) if os.path.abspath(p).startswith(ROOT + os.sep) else os.path.abspath(p)
def absp(p): return p if os.path.isabs(p) else os.path.join(ROOT, p)
def git(*a, cwd=ROOT):
    r = subprocess.run(["git", *a], cwd=cwd, capture_output=True, text=True); return r.stdout.strip() if r.returncode == 0 else ""


def build_id(chart, level, fmt, tag=""):
    lv = level.replace("+", "plus").replace("-", "minus")
    return f"c{chart}-{lv}-{fmt}" + (f"-{re.sub(r'[^A-Za-z0-9]+', '-', tag).strip('-')}" if tag else "")


def inputs_now(data_path, theme_path, scene_path, chart, slots, reg, theme, code_version):
    """Everything a build depends on, as hashes. The same function writes a record and checks one, so they cannot disagree."""
    lib = jload(os.path.join(ROOT, "library", "index.json"))["entries"] if os.path.exists(os.path.join(ROOT, "library", "index.json")) else []
    out_slots = {}
    for slot, name in slots.items():
        st = reg["strips"][name]; sheet = os.path.join(ROOT, "sheets", st["file"]); sh_ = fh(sheet)
        twin = next((e["id"] for e in lib if e["measured"].get("sha") == sh_ and e["measured"].get("row") == st.get("row")), None)
        out_slots[slot] = {"strip": name, "sheet": f"sheets/{st['file']}", "sheet_sha": sh_, "rows": st.get("rows"), "row": st.get("row"), "library_id": twin,
                           "settings_sha": h12(json.dumps(st, sort_keys=True).encode())}
    fonts = {k: {"file": theme["hud"][k], "sha": fh(absp(theme["hud"][k]))} for k in ("font", "mono")}
    return {"data": {"file": os.path.basename(data_path), "sha": fh(data_path)}, "theme": {"file": rel(theme_path), "sha": fh(theme_path)},
            "scene": {"file": rel(scene_path), "sha": fh(scene_path)}, "fonts": fonts, "code_version": code_version, "slots": out_slots}


def data_source(data_path):
    d = os.path.dirname(os.path.abspath(data_path)); top = git("rev-parse", "--show-toplevel", cwd=d)
    if not top: return {}
    return {"repo": git("config", "--get", "remote.origin.url", cwd=top), "path": os.path.relpath(os.path.abspath(data_path), top), "commit": git("log", "-1", "--format=%h", "--", os.path.abspath(data_path), cwd=d)}


def ffmpeg_version():
    r = subprocess.run(["ffmpeg", "-version"], capture_output=True, text=True); return (r.stdout.splitlines() or [""])[0]


def record(args, theme_path, scene_path, chart, slots, reg, theme, code_version, out_path):
    """Called by build.py after a full render has passed its decode check."""
    tag = getattr(args, "tag", "") or ""; bid = build_id(chart, args.level, args.format, tag); inp = inputs_now(args.data, theme_path, scene_path, chart, slots, reg, theme, code_version)
    dur = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", out_path], capture_output=True, text=True).stdout.strip()
    path = os.path.join(BUILDS, bid + ".json"); os.makedirs(BUILDS, exist_ok=True)
    old = jload(path) if os.path.exists(path) else {}
    rec = {"id": bid, "chart": chart, "level": args.level, "format": args.format, "tag": tag, "created": datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d %H:%M UTC"),
           "args": ["--chart", str(chart), "--level", args.level, "--format", args.format, "--theme", rel(theme_path), "--scene", rel(scene_path)] + (["--no-fade"] if args.no_fade else []),
           "inputs": inp, "data_source": data_source(args.data), "kit_commit": git("rev-parse", "--short", "HEAD"), "kit_dirty": bool(git("status", "--porcelain", "--", ".")),
           "ffmpeg": ffmpeg_version(), "result": {"file": os.path.basename(out_path), "seconds": round(float(dur), 2) if dur else None, "bytes": os.path.getsize(out_path), "sha": fh(out_path)},
           "history": (old.get("history", []) + [{"created": old["created"], "code_version": old["inputs"]["code_version"], "sha": old["result"]["sha"]}]) if old else []}
    json.dump(rec, open(path, "w"), indent=1); open(path, "a").write("\n")
    idx = sorted((jload(os.path.join(BUILDS, f)) for f in os.listdir(BUILDS) if f.endswith(".json") and f != "index.json"), key=lambda r: (r["chart"], r["level"], r["format"], r["tag"]))
    json.dump([{"id": r["id"], "chart": r["chart"], "level": r["level"], "format": r["format"], "tag": r["tag"], "created": r["created"], "seconds": r["result"]["seconds"],
                "slots": {s: v["strip"] for s, v in r["inputs"]["slots"].items()}} for r in idx], open(os.path.join(BUILDS, "index.json"), "w"), indent=1)
    print(f"recorded build {bid} -> builds/{bid}.json"); return rec


def load_rec(bid):
    p = os.path.join(BUILDS, bid + ".json")
    if not os.path.exists(p): sys.exit(f"no build {bid}. Try: builds.py list")
    return jload(p)


def need_data(a):
    d = a.data or os.environ.get("FIVEBX_DATA")
    if not d or not os.path.exists(d): sys.exit("pass --data path/to/5bx-charts.json (or set FIVEBX_DATA)")
    return d


def diff(rec, data_path):
    """What differs between the record and the files as they are now. Empty list = a rebuild would match."""
    sys.path.insert(0, HERE); import build
    theme_path, scene_path = absp(rec["inputs"]["theme"]["file"]), absp(rec["inputs"]["scene"]["file"]); theme = jload(theme_path); reg = jload(os.path.join(ROOT, "config", "strips.json"))
    names = reg["charts"].get(str(rec["chart"]), {}); slots = {s: names[s] for s in rec["inputs"]["slots"] if s in names}
    missing = [s for s in rec["inputs"]["slots"] if s not in slots]
    now = inputs_now(data_path, theme_path, scene_path, rec["chart"], slots, reg, theme, build.CODE_VERSION); was = rec["inputs"]; out = []
    if now["data"]["sha"] != was["data"]["sha"]: out.append(("plan file", "the plan (5bx-charts.json) is not the version this video was built from"))
    for k, label in (("theme", "look and wording (theme.json)"), ("scene", "props (scene file)")):
        if now[k]["sha"] != was[k]["sha"]: out.append((label, "changed"))
    if now["fonts"] != was["fonts"]: out.append(("fonts", "changed"))
    if now["code_version"] != was["code_version"]: out.append(("builder code", "changed (kit/build.py, keyer.py or recolor.py): every part re-renders"))
    for s in missing: out.append((f"slot {s}", "no longer mapped to a strip for this chart"))
    for s, v in now["slots"].items():
        w = was["slots"][s]
        if v["strip"] != w["strip"]: out.append((f"slot {s}", f"now uses {v['strip']} (was {w['strip']})"))
        elif v["sheet_sha"] != w["sheet_sha"]: out.append((f"slot {s}", f"strip image changed ({w['library_id'] or w['sheet']} -> {v['library_id'] or v['sheet']}); only this part re-renders"))
        elif v["settings_sha"] != w["settings_sha"]: out.append((f"slot {s}", "strip settings changed (anchor, cycle or timing); only this part re-renders"))
    return out


def cmd_list(a):
    if not os.path.exists(os.path.join(BUILDS, "index.json")): print("(no builds recorded yet)"); return
    for r in jload(os.path.join(BUILDS, "index.json")): print(f"{r['id']:28s} chart {r['chart']} level {r['level']:3s} {r['format']:9s} {r['seconds']:>7}s  {r['created']}")


def cmd_show(a):
    r = load_rec(a.id); i = r["inputs"]
    print(f"{r['id']}  ({r['created']}, kit {r['kit_commit']}{' + uncommitted changes' if r['kit_dirty'] else ''})")
    print(f"  result   {r['result']['file']}  {r['result']['seconds']} s  {r['result']['bytes'] / 1e6:.1f} MB  hash {r['result']['sha']}")
    print(f"  plan     {i['data']['file']} hash {i['data']['sha']}  from {r['data_source'].get('repo', '?')} {r['data_source'].get('path', '')} @ {r['data_source'].get('commit', '?')}")
    print(f"  look     {i['theme']['file']}   scene {i['scene']['file']}   fonts {i['fonts']['font']['file']}")
    for s, v in i["slots"].items(): print(f"  {s:5s}    {v['strip']:38s} {v['sheet']}{' row ' + str(v['row']) if v['rows'] else ''}  library {v['library_id'] or '-'}")
    print(f"  rebuild  python3 kit/build.py --data <plan> {' '.join(r['args'])} --out out/{r['id']}.mp4" + (f" --tag {r['tag']}" if r['tag'] else ""))


def cmd_check(a):
    r = load_rec(a.id); d = diff(r, need_data(a))
    if not d: print(f"{a.id}: up to date. A rebuild uses exactly the inputs this video was made from."); return
    print(f"{a.id}: out of date")
    for k, v in d: print(f"  - {k}: {v}")
    sys.exit(1)


def cmd_rebuild(a):
    r = load_rec(a.id); data = need_data(a); out = a.out or os.path.join(ROOT, "out", r["id"] + ".mp4"); os.makedirs(os.path.dirname(out), exist_ok=True)
    d = diff(r, data)
    for k, v in d: print(f"  note: {k}: {v}")
    cmd = [sys.executable, os.path.join(HERE, "build.py"), "--data", data, *r["args"], "--out", out] + (["--tag", r["tag"]] if r["tag"] else [])
    print("running:", " ".join(cmd)); rc = subprocess.run(cmd).returncode
    if rc: sys.exit(rc)
    new = jload(os.path.join(BUILDS, r["id"] + ".json")); same = new["result"]["sha"] == r["result"]["sha"]
    print(f"rebuilt {out}: {new['result']['seconds']} s (was {r['result']['seconds']} s); " + ("identical file to the recorded one." if same else "not byte-identical to the recorded video (expected if anything above changed, and encoders can vary by version); the record now describes this one."))


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter); sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("list").set_defaults(fn=cmd_list)
    for n, fn in (("show", cmd_show), ("check", cmd_check), ("rebuild", cmd_rebuild)):
        p = sub.add_parser(n); p.add_argument("id")
        if n != "show": p.add_argument("--data")
        if n == "rebuild": p.add_argument("--out")
        p.set_defaults(fn=fn)
    a = ap.parse_args(); a.fn(a)


if __name__ == "__main__": main()
