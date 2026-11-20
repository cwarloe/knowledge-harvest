#!/usr/bin/env python3
"""Build the phone-friendly demo: a reel video plus an interactive layer viewer, as a folder of plain files.

  python3 kit/make_demo.py --data path/to/5bx-charts.json --out docs/sprite-boy-demo --reel

The folder works anywhere static files are served (GitHub Pages, any web host, a claude.ai artifact).
Everything is read from the kit's own assets and config, so rebuilding after any change refreshes the demo.
  --reel   also build the highlight video (about 1.5 min the first time; segments are cached)
"""
import argparse, json, os, shutil, subprocess, sys, tempfile
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE); sys.path.insert(0, HERE)
from recolor import REGIONS
import build

def jload(p): return json.load(open(p))
def sh(cmd): 
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode: sys.exit(f"failed: {' '.join(cmd[:8])}...\n{r.stderr[-1200:]}")

def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--data", required=True); ap.add_argument("--out", required=True); ap.add_argument("--reel", action="store_true")
    ap.add_argument("--width", type=int, default=1280, help="demo canvas width; 1920 is the full-size frame")
    a = ap.parse_args(); out = os.path.abspath(a.out); f = a.width / 1920.0
    theme = jload(os.path.join(ROOT, "config", "theme.json")); reg = jload(os.path.join(ROOT, "config", "strips.json"))
    example = jload(os.path.join(ROOT, "config", "scene.example-mat.json"))
    for d in ("sprites", "backdrop", "props"): shutil.rmtree(os.path.join(out, d), ignore_errors=True)
    os.makedirs(out, exist_ok=True)

    data_in = jload(a.data); SLOTS = ["ex1", "ex2", "ex3", "ex4", "run", "jump"]; specs = jload(os.path.join(ROOT, "prompts", "strips.json"))["strips"]
    prompted = {v["chart"] for v in specs.values() if v.get("chart", 1) > 1}
    def has_strip(cid, slot):
        k = reg["charts"].get(str(cid), {}).get(slot); st = reg["strips"].get(k) if k else None
        return bool(st) and os.path.exists(os.path.join(ROOT, "sheets", st["file"]))
    charts, layers, props_scene, gy, S = {}, [], None, None, None
    with tempfile.TemporaryDirectory() as tmp:                      # one layer pack per chart gives us geometry and timing for free
        for c in data_in["charts"]:
            cid = c["id"]; built = [x for x in SLOTS if has_strip(cid, x)]
            names = {f"ex{i + 1}": c["exercises"][i]["name"] for i in range(4)}; names["run"] = c["exercises"][4]["name"]; names["jump"] = c["exercises"][4].get("jumpName", "")
            entry = {"label": f"Chart {cid}", "status": "built" if len(built) == 6 else "partial" if built else "planned",
                     "all": [{"slot": x, "name": names[x], "built": x in built} for x in SLOTS], "slots": {}, "order": [x for x in SLOTS if x in built], "prompts_ready": cid == 1 or cid in prompted}
            charts[str(cid)] = entry
            if not built: continue
            sh([sys.executable, os.path.join(HERE, "build.py"), "--data", a.data, "--chart", str(cid), "--work", os.path.join(ROOT, ".work"), "--export", tmp] + (["--only", ",".join(built)] if len(built) < 6 else []))
            pack = os.path.join(tmp, f"chart{cid}-landscape"); man = jload(os.path.join(pack, "scene.json"))
            if layers == [] :                                         # the backdrop is the same for every chart: write it once
                gy = man["ground_y"]; S = man["strings"]
                for fn in sorted(os.listdir(os.path.join(pack, "backdrop"))):
                    im = Image.open(os.path.join(pack, "backdrop", fn)).convert("RGBA")
                    im = im.resize((round(im.width * f), round(im.height * f)), Image.LANCZOS); os.makedirs(os.path.join(out, "backdrop"), exist_ok=True)
                    im.save(os.path.join(out, "backdrop", fn), optimize=True); layers.append({"name": fn[3:-4], "file": f"backdrop/{fn}"})
            segs = man["segments"]
            for slot, sl in man["slots"].items():
                st = reg["strips"][sl["strip"]]; meta = jload(os.path.join(ROOT, "assets", "sprites", sl["strip"], "meta.json"))
                g = sl["geom"]; s = g["scale"]; X0 = g["X0"]; floor = meta["floor"]; poses = []
                sdir = os.path.join("sprites", f"c{cid}", sl["strip"]); os.makedirs(os.path.join(out, sdir), exist_ok=True)      # per chart: the same strip can be scaled differently in another chart
                for k, m in enumerate(meta["poses"], 1):
                    x, y = build.pose_xy(st, k, m, X0, gy, floor, s); w, h = m["size"][0] * s, m["size"][1] * s
                    im = Image.open(os.path.join(ROOT, "assets", "sprites", sl["strip"], m["file"])).convert("RGBA")
                    sw, shh = max(1, round(w * f)), max(1, round(h * f)); im.resize((sw, shh), Image.LANCZOS).save(os.path.join(out, sdir, m["file"]), optimize=True)
                    poses.append({"file": f"{sdir}/{m['file']}".replace(os.sep, "/"), "x": round(x * f, 2), "y": round(y * f, 2), "w": sw, "h": shh})
                extra = {}                                                        # flipped poses ("5m"): appended after the real ones so the viewer can use plain numbers
                for k in st.get("mirror", []):
                    m = meta["poses"][k - 1]; fl = Image.open(os.path.join(ROOT, "assets", "sprites", sl["strip"], m["file"])).convert("RGBA").transpose(Image.FLIP_LEFT_RIGHT)
                    ax = build.mirror_anchor(st, k, m); dy = (st.get("nudge") or {}).get(str(k), (0, 0))[1]; x, y = X0 - ax * s, gy + 10 - (floor - m["offset"][1]) * s + dy * s; w, h = m["size"][0] * s, m["size"][1] * s
                    sw, shh = max(1, round(w * f)), max(1, round(h * f)); fn = f"p{k}m.png"; fl.resize((sw, shh), Image.LANCZOS).save(os.path.join(out, sdir, fn), optimize=True)
                    poses.append({"file": f"{sdir}/{fn}".replace(os.sep, "/"), "x": round(x * f, 2), "y": round(y * f, 2), "w": sw, "h": shh}); extra[f"{k}m"] = len(poses)
                num = lambda cyc: [extra[c] if str(c) in extra else int(c) for c in cyc]
                seg = next(q for q in segs if q.get("slot") == slot)
                info = {"strip": sl["strip"], "cycle": num(st["cycle"]), **({"cycle_reverse": num(st["cycle_reverse"])} if st.get("cycle_reverse") else {}), "cycle_s": seg["cycle_seconds"], "allot": seg["allot"], "poses": poses,
                        "union": [round((X0 - g["L"] * s) * f, 2), round((X0 + g["R"] * s) * f, 2)]}
                if seg["kind"] == "exercise": info.update(kicker=S["kicker"].format(n=seg["n"]), title=seg["name"], target=S["reps"].format(reps=seg["reps"]))
                elif seg["kind"] == "run": info.update(kicker=S["kicker"].format(n=5), title=seg["name"], target=S["steps"].format(steps=seg["steps"]))
                else: info.update(kicker=S["jump_kicker"], title=S["jump_title"].format(count=seg["count"], name=seg["name"]), target=S["jump_target"])
                entry["slots"][slot] = info
    if not layers: sys.exit("no chart has any strips to show")
    props = []
    for p in example["props"]:
        q = {k: v for k, v in p.items() if not k.startswith("_")}
        if p["kind"] == "overlay":                                 # the viewer needs it already cut out and at the demo's frame size
            from keyer import key as _key
            im = _key(Image.open(os.path.join(ROOT, p["file"]))).convert("RGBA").resize((round(1920 * f), round(1080 * f)), Image.LANCZOS)
            os.makedirs(os.path.join(out, "props"), exist_ok=True); fn = "overlay-" + os.path.splitext(os.path.basename(p["file"]))[0] + ".png"; im.save(os.path.join(out, "props", fn), optimize=True); q["file"] = "props/" + fn
        elif p["kind"] == "image":
            os.makedirs(os.path.join(out, "props"), exist_ok=True); shutil.copy(os.path.join(ROOT, p["file"]), os.path.join(out, "props", os.path.basename(p["file"]))); q["file"] = "props/" + os.path.basename(p["file"])
        props.append(q)
    first = next(k for k, v in charts.items() if v["status"] != "planned")
    data = {"frame": [round(1920 * f), round(1080 * f)], "scale": f, "ground": round(gy * f, 2), "floor": round((gy + 10) * f, 2), "layers": layers,
            "charts": charts, "default_chart": first, "props": props, "strings": S,
            "regions": {k: {"h": v["h"], "smin": v["smin"], "vmin": v["vmin"]} for k, v in REGIONS.items()}}
    json.dump(data, open(os.path.join(out, "data.json"), "w"), indent=1)

    for name, orig, cand in (("edit-run", "ex5-stationary-run.png", "candidates/stationary-run-lower-lift.png"), ("edit-scissor", "ex5-scissor-jumps.png", "candidates/scissor-jumps-upright-stance-b.png")):
        A = Image.open(os.path.join(ROOT, "sheets", orig)).convert("RGB"); B = Image.open(os.path.join(ROOT, "sheets", cand)).convert("RGB")
        w = 900; A = A.resize((w, round(A.height * w / A.width))); B = B.resize((w, round(B.height * w / B.width)))
        im = Image.new("RGB", (w, A.height + B.height + 6), (20, 24, 30)); im.paste(A, (0, 0)); im.paste(B, (0, A.height + 6)); im.save(os.path.join(out, name + ".jpg"), quality=78)

    # prompts: the data the prompts page reads, the two documents, and the strips themselves (reference images for other tools)
    shutil.rmtree(os.path.join(out, "strips"), ignore_errors=True); os.makedirs(os.path.join(out, "strips"), exist_ok=True)
    sh([sys.executable, os.path.join(HERE, "prompt.py"), "--all", "--data", a.data])
    shutil.copy(os.path.join(ROOT, "prompts", "prompts.json"), os.path.join(out, "prompts.json")); shutil.copy(os.path.join(ROOT, "prompts", "PROMPTS.md"), os.path.join(out, "PROMPTS.md"))
    sh([sys.executable, os.path.join(HERE, "prompt_bg.py"), "--publish"])
    for fn in ("backgrounds.json", "BACKGROUNDS.md"): shutil.copy(os.path.join(ROOT, "prompts", fn), os.path.join(out, fn))
    shutil.copy(os.path.join(ROOT, "docs", "HOW-TO-GENERATE-STRIPS.md"), os.path.join(out, "HOW-TO-GENERATE-STRIPS.md"))
    for st in reg["strips"].values(): shutil.copy(os.path.join(ROOT, "sheets", st["file"]), os.path.join(out, "strips", st["file"]))
    for cid in sorted(prompted):                    # a Word document of prompts for each chart still to build
        sh([sys.executable, os.path.join(HERE, "make_prompt_doc.py"), "--data", a.data, "--chart", str(cid), "--out", os.path.join(out, f"Chart-{cid}-image-prompts.docx")])

    for name in ("page", "prompts"):                                  # the page itself; the wrapper makes it a standalone file
        page = open(os.path.join(HERE, "demo", name + ".html"), encoding="utf-8").read()
        open(os.path.join(out, "index.html" if name == "page" else "prompts.html"), "w", encoding="utf-8").write(
            '<!doctype html>\n<html lang="en">\n<head>\n<meta charset="utf-8">\n<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">\n' + page + "\n</html>\n")

    if a.reel: build_reel(a.data, out)
    size = sum(os.path.getsize(os.path.join(dp, fn)) for dp, _, fns in os.walk(out) for fn in fns)
    print(f"demo written to {out} ({size / 1e6:.1f} MB)")


def build_reel(data_path, out):
    """Short highlight video, 720p, each clip captioned. Uses the kit's own preview builds."""
    work = tempfile.mkdtemp(); font = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"; b = os.path.join(HERE, "build.py")
    theme_alt = jload(os.path.join(ROOT, "config", "theme.json")); theme_alt["recolor"].update(shoes=2, shorts=215)
    json.dump(theme_alt, open(os.path.join(work, "theme_alt.json"), "w"))
    base = [sys.executable, b, "--data", data_path, "--preview"]
    sh(base + ["--only", "ex1,ex2,ex3,ex4", "--out", os.path.join(work, "a.mp4")]); sh(base + ["--only", "run", "--out", os.path.join(work, "run.mp4")])
    sh(base + ["--only", "jump", "--out", os.path.join(work, "jump.mp4")]); sh(base + ["--only", "ex1", "--theme", os.path.join(work, "theme_alt.json"), "--out", os.path.join(work, "recolor.mp4")])
    sh(base + ["--only", "ex4", "--scene", os.path.join(ROOT, "config", "scene.example-mat.json"), "--out", os.path.join(work, "mat.mp4")])
    clips = [("a", 20, "Chart 1 level A+: four exercises, 5 s each (preview cut)"), ("run", 5, "Stationary run: 400 steps at 80 a minute (preview cut)"),
             ("jump", 5, "Scissor jumps: every 75 steps (preview cut)"), ("recolor", 5, "Same boy, recolored: two numbers in theme.json"),
             ("mat", 5, "Same video with a mat, shadow and prop: one scene file")]
    lst = []
    for i, (n, dur, cap) in enumerate(clips):
        o = os.path.join(work, f"p{i}.mp4")
        sh(["ffmpeg", "-v", "error", "-y", "-t", str(dur), "-i", os.path.join(work, n + ".mp4"), "-f", "lavfi", "-t", str(dur), "-i", "anullsrc=r=44100:cl=stereo",
            "-vf", f"scale=1280:720,drawtext=fontfile={font}:text='{cap}':fontcolor=white:fontsize=24:borderw=4:bordercolor=0x101820@0.9:x=24:y=h-52",
            "-map", "0:v", "-map", "1:a", "-c:v", "libx264", "-preset", "medium", "-crf", "23", "-profile:v", "main", "-pix_fmt", "yuv420p", "-r", "30",
            "-c:a", "aac", "-b:a", "48k", "-shortest", o]); lst.append(o)
    open(os.path.join(work, "list.txt"), "w").write("".join(f"file '{p}'\n" for p in lst)); tmp = os.path.join(out, "reel.part.mp4")
    sh(["ffmpeg", "-v", "error", "-y", "-f", "concat", "-safe", "0", "-i", os.path.join(work, "list.txt"), "-c", "copy", "-movflags", "+faststart", tmp])
    sh(["ffmpeg", "-v", "error", "-i", tmp, "-f", "null", "-"]); os.replace(tmp, os.path.join(out, "reel.mp4"))


if __name__ == "__main__":
    main()
