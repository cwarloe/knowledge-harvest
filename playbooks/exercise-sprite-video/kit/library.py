#!/usr/bin/env python3
"""The strip library: every generated strip we keep, indexed, measured and graded, so the best one for an exercise is easy to find.

  python3 kit/library.py add FILE --chart 3 --slot ex1 --tool chatgpt --view angle --notes "front view, 5 poses"
  python3 kit/library.py grade c3-ex1-01 --form 4 --legibility 5 --character 5 --angle 5 --key 4 --notes "reversal pose is clear"
  python3 kit/library.py choose c3-ex1-01          # marks it the pick; the previous pick becomes a candidate
  python3 kit/library.py reject c3-ex1-02 --notes "knees straight in the squat"
  python3 kit/library.py list [--chart 3] [--slot ex1] [--verdict candidate]
  python3 kit/library.py best                      # the pick (or the best candidate) for every chart and slot
  python3 kit/library.py import-chosen             # register the strips already wired in config/strips.json

Everything lives in library/index.json (the record) and library/images/ (the files). Nothing here is read by the video build:
a pick only reaches a video when it is copied to sheets/ and named in config/strips.json (see the README, "Add an exercise").

Grades are 1 (unusable) to 5 (exactly right) on five questions that cost nothing to answer by eye:
  form       does it match the booklet's wording for this exercise (the 'check' list in prompts/strips.json)?
  legibility can a viewer tell what the body is doing, near limb from far limb, start from end?
  character  same boy, same clothes, blue sneakers, same scale in every pose?
  angle      one camera angle across all the poses?
  key        does the background cut out cleanly (measured too: 'fringe' below)?
A grade is a person's or a model's reading of a picture, and the entry says which. Only an expert reviewer clears 'expert_reviewed'.
Measured for every image: figures found, fringe (half-see-through pixels as a percent of the figure), and stray green pixels
(the author's rule: no green shoes).
"""
import argparse, colorsys, datetime, hashlib, json, os, shutil, sys
import numpy as np
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE); sys.path.insert(0, HERE)
LIB = os.path.join(ROOT, "library"); INDEX = os.path.join(LIB, "index.json")
GRADES = ("form", "legibility", "character", "angle", "key")
VIEWS = ("side", "angle", "front", "above", "mixed")
SLOTS = ("ex1", "ex2", "ex3", "ex4", "run", "jump")


def jload(p): return json.load(open(p))
def load():
    return jload(INDEX) if os.path.exists(INDEX) else {"_about": "Strip library. See kit/library.py. Edit with the tool, not by hand.", "entries": []}
def save(db):
    os.makedirs(LIB, exist_ok=True); json.dump(db, open(INDEX, "w"), indent=1); open(INDEX, "a").write("\n")
def find(db, i):
    for e in db["entries"]:
        if e["id"] == i: return e
    sys.exit(f"no entry {i}. Try: library.py list")


def measure(path):
    """What can be counted without judgment. Uses the same key and shape-splitting as the build."""
    from keyer import key, has_real_transparency
    import build
    im = Image.open(path); rgba = key(im); a = np.array(rgba); op = a[..., 3] > 128
    lab, ds = build.components(op); area = np.bincount(lab.ravel())[1:] if lab.max() else np.array([])
    figures = int((area > 400).sum())
    semi = int(((a[..., 3] > 16) & (a[..., 3] < 240)).sum()); fringe = round(100.0 * semi / max(1, int(op.sum())), 2)
    rgb = a[..., :3][op].astype(np.float32) / 255; green = 0
    if len(rgb):
        hsv = np.array([colorsys.rgb_to_hsv(*p) for p in rgb[:: max(1, len(rgb) // 40000)]])
        green = round(100.0 * float(((hsv[:, 0] > .22) & (hsv[:, 0] < .45) & (hsv[:, 1] > .45) & (hsv[:, 2] > .3)).mean()), 2)
    return {"size": list(im.size), "figures": figures, "fringe_pct": fringe, "green_pct": green, "real_transparency": bool(has_real_transparency(im)),
            "sha": hashlib.sha1(open(path, "rb").read()).hexdigest()[:12]}


def next_id(db, chart, slot):
    n = 1 + sum(1 for e in db["entries"] if e["chart"] == chart and e["slot"] == slot and e["id"].startswith(f"c{chart}-{slot}-"))
    return f"c{chart}-{slot}-{n:02d}"


def spec_for(strip):
    if not strip: return None
    p = os.path.join(ROOT, "prompts", "strips.json")
    return jload(p)["strips"].get(strip) if os.path.exists(p) else None


def cmd_add(a):
    db = load(); src = os.path.abspath(a.file)
    if not os.path.exists(src): sys.exit(f"no such file: {src}")
    m = measure(src)
    for e in db["entries"]:
        if e.get("measured", {}).get("sha") == m["sha"]: sys.exit(f"already in the library as {e['id']} (same file).")
    spec = spec_for(a.strip)
    chart = a.chart or (spec or {}).get("chart"); slot = a.slot or (spec or {}).get("slot")
    if not chart or slot not in SLOTS: sys.exit("give --chart N and --slot ex1|ex2|ex3|ex4|run|jump (or --strip KEY from prompts/strips.json)")
    i = next_id(db, chart, slot); ext = os.path.splitext(src)[1].lower() or ".png"
    os.makedirs(os.path.join(LIB, "images"), exist_ok=True); shutil.copy(src, os.path.join(LIB, "images", i + ext))
    e = {"id": i, "file": f"library/images/{i}{ext}", "chart": chart, "slot": slot, "exercise": (spec or {}).get("exercise", a.exercise or ""),
         "strip": a.strip or "", "tool": a.tool, "view": a.view, "poses": a.poses or m["figures"], "added": datetime.date.today().isoformat(),
         "prompt": a.prompt or ((spec or {}).get("exercise") and f"prompts/PROMPTS.md, '{(spec or {}).get('exercise')}'") or "", "measured": m,
         "grades": {}, "graded_by": "", "expert_reviewed": False, "verdict": "candidate", "notes": a.notes or ""}
    db["entries"].append(e); save(db)
    flags = []
    if a.poses and m["figures"] != a.poses: flags.append(f"expected {a.poses} figures, found {m['figures']}")
    if m["green_pct"] > 1.0: flags.append(f"{m['green_pct']}% green on the figure (no green shoes)")
    if m["fringe_pct"] > 6: flags.append(f"fringe {m['fringe_pct']}% (messy cut-out)")
    print(f"added {i}: {m['figures']} figures, fringe {m['fringe_pct']}%, green {m['green_pct']}%" + (("  CHECK: " + "; ".join(flags)) if flags else ""))


def cmd_grade(a):
    db = load(); e = find(db, a.id); g = e["grades"]
    for k in GRADES:
        v = getattr(a, k)
        if v is not None:
            if not 1 <= v <= 5: sys.exit(f"{k} must be 1 to 5")
            g[k] = v
    if a.by: e["graded_by"] = a.by
    if a.notes: e["notes"] = (e["notes"] + " | " if e["notes"] else "") + a.notes
    if a.expert: e["expert_reviewed"] = True
    save(db); print(f"{a.id}: {fmt_grades(e)}")


def set_verdict(a, v):
    db = load(); e = find(db, a.id)
    if v == "chosen":
        for o in db["entries"]:
            if o["chart"] == e["chart"] and o["slot"] == e["slot"] and o["verdict"] == "chosen" and o["id"] != e["id"]: o["verdict"] = "candidate"; print(f"  {o['id']} is now a candidate")
    e["verdict"] = v
    if getattr(a, "notes", None): e["notes"] = (e["notes"] + " | " if e["notes"] else "") + a.notes
    save(db); print(f"{e['id']}: {v}")
    if v == "chosen" and not e.get("wired"):
        print(f"  to use it: copy {e['file']} to sheets/, set 'file' for the chart {e['chart']} {e['slot']} strip in config/strips.json, then run tests/smoke.py")


def fmt_grades(e):
    g = e["grades"]
    return " ".join(f"{k[:4]}={g[k]}" if k in g else f"{k[:4]}=-" for k in GRADES) + (f"  (by {e['graded_by']})" if e["graded_by"] else "")


def score(e):
    g = e["grades"]
    return (g.get("form", 0) * 3 + g.get("legibility", 0) * 2 + g.get("character", 0) + g.get("angle", 0) + g.get("key", 0)) if g else -1


def rows(db, a):
    out = [e for e in db["entries"] if (a.chart is None or e["chart"] == a.chart) and (a.slot is None or e["slot"] == a.slot) and (a.verdict is None or e["verdict"] == a.verdict)]
    return sorted(out, key=lambda e: (e["chart"], SLOTS.index(e["slot"]), -(e["verdict"] == "chosen"), -score(e)))


def cmd_list(a):
    db = load(); r = rows(db, a)
    if not r: print("(nothing matches)"); return
    for e in r:
        m = e["measured"]; print(f"{e['id']:12s} {e['verdict']:9s} {e['view']:6s} {e['tool']:8s} {m['figures']}fig fringe {m['fringe_pct']:>5}%  {fmt_grades(e)}\n{'':12s} {e['exercise'] or e['strip']}{' | ' + e['notes'] if e['notes'] else ''}")


def cmd_best(a):
    db = load(); seen = {}
    for e in rows(db, a): seen.setdefault((e["chart"], e["slot"]), []).append(e)
    for (c, s), es in seen.items():
        pick = next((e for e in es if e["verdict"] == "chosen"), None); alt = [e for e in es if e["verdict"] == "candidate"]
        top = pick or (alt[0] if alt else None); tag = "PICK " if pick else "best candidate (not chosen)"
        extra = f"   + {len(alt) - (0 if pick else 1)} more candidate(s)" if len(alt) - (0 if pick else 1) > 0 else ""
        print(f"chart {c} {s:4s} {tag:28s} {top['id']:12s} {fmt_grades(top)}{extra}" if top else f"chart {c} {s:4s} only rejected takes")


def cmd_import(a):
    """Register the strips already wired into config/strips.json, so the library covers them too."""
    db = load(); reg = jload(os.path.join(ROOT, "config", "strips.json")); known = {e["file"] for e in db["entries"]}; added = 0
    for cid, mp in reg["charts"].items():
        for slot, strip in mp.items():
            st = reg["strips"].get(strip); path = os.path.join(ROOT, "sheets", st["file"]) if st else None
            if not st or not os.path.exists(path): continue
            rel = f"sheets/{st['file']}"
            if rel in known: continue
            spec = spec_for(strip) or {}; m = measure(path)
            if st.get("rows"): m["figures"] = st["poses"]       # a shared sheet: the figure count is for the whole sheet
            i = f"c{cid}-{slot}-w{len([e for e in db['entries'] if e['id'].startswith(f'c{cid}-{slot}-w')]) + 1}"
            db["entries"].append({"id": i, "file": rel, "chart": int(cid), "slot": slot, "exercise": spec.get("exercise", ""), "strip": strip, "tool": "unknown",
                                  "view": "side" if int(cid) == 1 else "angle", "poses": st["poses"], "added": datetime.date.today().isoformat(), "prompt": "prompts/PROMPTS.md",
                                  "measured": m, "grades": {}, "graded_by": "", "expert_reviewed": False, "verdict": "chosen", "wired": True,
                                  "notes": "wired into config/strips.json; not yet graded"})
            known.add(rel); added += 1
    save(db); print(f"registered {added} wired strip(s)")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter); sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("add"); p.add_argument("file"); p.add_argument("--chart", type=int); p.add_argument("--slot", choices=SLOTS); p.add_argument("--strip", help="key in prompts/strips.json")
    p.add_argument("--exercise", default=""); p.add_argument("--tool", default="unknown"); p.add_argument("--view", default="angle", choices=VIEWS); p.add_argument("--poses", type=int)
    p.add_argument("--prompt", default=""); p.add_argument("--notes", default=""); p.set_defaults(fn=cmd_add)
    p = sub.add_parser("grade"); p.add_argument("id")
    for k in GRADES: p.add_argument("--" + k, type=int)
    p.add_argument("--by", default="", help="who graded: 'claude' or a name"); p.add_argument("--notes", default=""); p.add_argument("--expert", action="store_true", help="an exercise-knowledgeable person reviewed it"); p.set_defaults(fn=cmd_grade)
    for name, v in (("choose", "chosen"), ("reject", "rejected"), ("candidate", "candidate")):
        p = sub.add_parser(name); p.add_argument("id"); p.add_argument("--notes", default=""); p.set_defaults(fn=lambda a, v=v: set_verdict(a, v))
    for name, fn in (("list", cmd_list), ("best", cmd_best)):
        p = sub.add_parser(name); p.add_argument("--chart", type=int); p.add_argument("--slot", choices=SLOTS); p.add_argument("--verdict", choices=("chosen", "candidate", "rejected")); p.set_defaults(fn=fn)
    p = sub.add_parser("import-chosen"); p.set_defaults(fn=cmd_import)
    a = ap.parse_args(); a.fn(a)


if __name__ == "__main__": main()
