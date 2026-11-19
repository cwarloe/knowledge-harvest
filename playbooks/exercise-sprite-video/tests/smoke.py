#!/usr/bin/env python3
"""Quick checks that a change did not break the kit.  python3 tests/smoke.py path/to/5bx-charts.json
Takes about 30 seconds. Checks the strips, the baked sprite and backdrop layer files, recolouring, props,
the layer-pack export, and that one exercise renders and decodes."""
import json, os, subprocess, sys, tempfile
import numpy as np
from PIL import Image

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); sys.path.insert(0, os.path.join(ROOT, "kit"))
import build
from keyer import key
from recolor import recolor

data_path = sys.argv[1] if len(sys.argv) > 1 else os.environ.get("FIVEBX_DATA")
if not data_path: sys.exit("usage: smoke.py path/to/5bx-charts.json")
theme = json.load(open(os.path.join(ROOT, "config", "theme.json"))); reg = json.load(open(os.path.join(ROOT, "config", "strips.json")))
scene = json.load(open(os.path.join(ROOT, "config", "scene.json"))); data = json.load(open(data_path))
fails = []
def check(ok, msg):
    print(("ok   " if ok else "FAIL ") + msg); (None if ok else fails.append(msg))

for name, st in reg["strips"].items():
    p = os.path.join(ROOT, "sheets", st["file"])
    if not os.path.exists(p): check(False, f"{name}: missing file {st['file']}"); continue
    try: m = build.bake(name, st, theme)
    except SystemExit as e: check(False, f"{name}: {e}"); continue
    files = [os.path.join(ROOT, "assets", "sprites", name, q["file"]) for q in m["poses"]]
    check(len(m["poses"]) == st["poses"] and all(os.path.exists(f) for f in files), f"{name}: {len(files)} sprite files on disk, one per pose")
    check(max(st["cycle"]) <= st["poses"], f"{name}: cycle only uses poses that exist")
    check(st["anchor"] in m["poses"][0]["anchors"], f"{name}: anchor '{st['anchor']}' exists")

k = key(Image.open(os.path.join(ROOT, "sheets", reg["strips"]["toe-touch-c1"]["file"])), **theme["key"])
r = recolor(k, {"shorts": 215, "shoes": 2, "tank": 120})
check(np.array_equal(np.array(k)[..., 3], np.array(r)[..., 3]), "recolor leaves transparency untouched")
check(np.array_equal(np.array(k), np.array(recolor(k, {}))), "recolor with no changes is a no-op")
for c, slots in reg["charts"].items():
    for slot, key_ in slots.items(): check(key_ in reg["strips"], f"chart {c} slot {slot} points at a known strip")

for fmt, F in theme["formats"].items():
    layers = build.backdrop_layers(theme, F, fmt); d = os.path.join(ROOT, "assets", "backdrops", theme["backdrop"].get("id", "forest"), fmt)
    check(len(layers) >= 5 and all(im.size == (F["W"], F["H"]) for _, im in layers) and len(os.listdir(d)) >= len(layers),
          f"backdrop '{fmt}': {len(layers)} layers, each its own file, frame-sized")

# every prop kind renders; image props point at real files
allon = {"props": [dict(p, enabled=True, slots="*") for p in scene["props"]]}
F = theme["formats"]["landscape"]; geom = dict(gy=int(F["H"] * F["ground"]), X0=960, s=1.0, L=300, R=300)
for z in ("behind", "front"):
    lay = build.render_props(allon, "ex4", geom, F, z)
    check(lay is not None and lay.size == (F["W"], F["H"]) and np.array(lay)[..., 3].max() > 0, f"props ({z}) render with everything switched on")
for p in scene["props"]:
    if p["kind"] == "image": check(os.path.exists(os.path.join(ROOT, p["file"])), f"prop image exists: {p['file']}")

with tempfile.TemporaryDirectory() as tmp:
    exp = subprocess.run([sys.executable, os.path.join(ROOT, "kit", "build.py"), "--data", data_path, "--work", os.path.join(tmp, "w"), "--export", os.path.join(tmp, "x")], capture_output=True, text=True)
    mp = os.path.join(tmp, "x", "chart1-landscape", "scene.json")
    ok = exp.returncode == 0 and os.path.exists(mp)
    check(ok, "layer pack exports")
    if ok:
        m = json.load(open(mp)); want = sum(data["timing"]["secondsPerExercise"]) + 4 * data["appDefaults"]["transitionSeconds"]
        check(abs(sum(s.get("dur", s.get("secs", 0)) for s in m["segments"]) - want) < 0.5, f"manifest timeline adds up to the plan ({want} s)")
        check(all(os.path.exists(os.path.join(tmp, "x", "chart1-landscape", f)) for sl in m["slots"].values() for f in sl["files"]["boy"]), "every boy layer in the manifest exists")
    else: print(exp.stderr[-600:])
    out = os.path.join(tmp, "t.mp4")
    r = subprocess.run([sys.executable, os.path.join(ROOT, "kit", "build.py"), "--data", data_path, "--preview", "--only", "ex3",
                        "--work", os.path.join(tmp, "w2"), "--out", out], capture_output=True, text=True)
    check(r.returncode == 0 and os.path.exists(out), "one exercise renders and passes the decode check")
    if os.path.exists(out):
        dur = float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", out], capture_output=True, text=True).stdout)
        check(abs(dur - 5.0) < 0.2, f"preview of one exercise is 5 s (got {dur:.1f})")
    else: print(r.stderr[-800:])

with tempfile.TemporaryDirectory() as tmp:
    demo = os.path.join(tmp, "demo")
    r = subprocess.run([sys.executable, os.path.join(ROOT, "kit", "make_demo.py"), "--data", data_path, "--out", demo], capture_output=True, text=True)
    ok = r.returncode == 0 and os.path.exists(os.path.join(demo, "data.json"))
    check(ok, "demo page builds")
    if ok:
        dd = json.load(open(os.path.join(demo, "data.json")))
        refs = [l["file"] for l in dd["layers"]] + [q["file"] for sl in dd["slots"].values() for q in sl["poses"]] + [q["file"] for q in dd["props"] if q["kind"] == "image"]
        check(all(os.path.exists(os.path.join(demo, f)) for f in refs), f"every file the demo refers to exists ({len(refs)} files)")
        pj = json.load(open(os.path.join(demo, "prompts.json")))
        check(len(pj["strips"]) == len(reg["strips"]) and all("prompt_with_reference" in q and "prompt_first_strip" in q for q in pj["strips"]), "published prompts cover every strip, with and without a reference")
        check(not any(w in open(os.path.join(demo, "PROMPTS.md"), encoding="utf-8").read().lower() for w in ("charles", "@gmail")), "published prompts carry no personal names or addresses")
        check(os.path.exists(os.path.join(demo, "index.html")) and "5BX Sprite Boy" in open(os.path.join(demo, "index.html"), encoding="utf-8").read(), "demo index.html written")
    else: print(r.stderr[-600:])
print("\nALL PASS" if not fails else f"\n{len(fails)} FAILED"); sys.exit(1 if fails else 0)
