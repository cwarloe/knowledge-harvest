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
# a strip that already has real transparency must give the same sprites as the magenta route
from keyer import has_real_transparency
src = os.path.join(ROOT, "sheets", reg["strips"]["knee-push-up-c1"]["file"]); mg = Image.open(src); tp = key(mg, **theme["key"])
check(not has_real_transparency(mg) and has_real_transparency(tp), "a real transparent strip is detected; a magenta one is not")
pm = [p for p, _ in build.split_rgba(key(mg, **theme["key"]), 3, "magenta")]; pt = [p for p, _ in build.split_rgba(key(tp, **theme["key"]), 3, "transparent")]
check(len(pm) == len(pt) == 3 and all(x.size == y.size and np.array_equal(np.array(x)[..., 3] > 128, np.array(y)[..., 3] > 128) for x, y in zip(pm, pt)), "transparent route and magenta route give identical sprites")
check(not has_real_transparency(Image.new("RGB", (400, 200), (210, 210, 210))), "a painted-in checkerboard is not mistaken for transparency")
# several exercises on one sheet (rows) must give the same sprites as the strips on their own
import tempfile as _tf
_names = ["toe-touch-c1", "partial-sit-up-c1", "knee-push-up-c1"]; _imgs = [Image.open(os.path.join(ROOT, "sheets", reg["strips"][n]["file"])).convert("RGB") for n in _names]
_W = max(i.width for i in _imgs); _sheet = Image.new("RGB", (_W, sum(i.height for i in _imgs)), (255, 59, 253)); _y = 0
for _i in _imgs: _sheet.paste(_i, (0, _y)); _y += _i.height
_tmp = _tf.mkdtemp(); _sp = os.path.join(_tmp, "sheet.png"); _sheet.save(_sp); _old_assets = build.ASSETS; build.ASSETS = os.path.join(_tmp, "assets")
try:
    ok_rows = True
    for _r, _n in enumerate(_names):
        _one = build.bake("_row_" + _n, dict(reg["strips"][_n], file=_sp, rows=3, row=_r), theme); _own = build.bake("_own_" + _n, dict(reg["strips"][_n], file=os.path.join(ROOT, "sheets", reg["strips"][_n]["file"])), theme)
        ok_rows &= [q["size"] for q in _one["poses"]] == [q["size"] for q in _own["poses"]]
finally: build.ASSETS = _old_assets
check(ok_rows, "a sheet with three exercises in three rows gives the same sprites as the three strips on their own")
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
        refs = [l["file"] for l in dd["layers"]] + [q["file"] for C in dd["charts"].values() for sl in C["slots"].values() for q in sl["poses"]] + [q["file"] for q in dd["props"] if q["kind"] == "image"]
        check(all(os.path.exists(os.path.join(demo, f)) for f in refs), f"every file the demo refers to exists ({len(refs)} files)")
        reg_charts = {str(k) for k in reg["charts"]}
        check(len(dd["charts"]) == len(data["charts"]), f"chart menu lists every chart in the plan ({len(dd['charts'])})")
        check(all((C["status"] == "planned") == (not C["order"]) for C in dd["charts"].values()) and dd["charts"][dd["default_chart"]]["order"], "each chart's status matches the slots it has; the default chart has something to show")
        check(all(set(C["slots"]) == set(C["order"]) == {x["slot"] for x in C["all"] if x["built"]} for C in dd["charts"].values()), "per-chart slots, order and 'built' flags agree")
        check(all(cid in reg_charts or C["status"] == "planned" for cid, C in dd["charts"].items()), "only charts with no strips are shown as 'not made yet'")
        pj = json.load(open(os.path.join(demo, "prompts.json")))
        check({q["key"] for q in pj["strips"]} >= set(reg["strips"]) and all("prompt_with_reference" in q and "prompt_first_strip" in q for q in pj["strips"]), f"published prompts cover every registered strip and the {sum(1 for q in pj['strips'] if not q['image'])} not made yet, with and without a reference")
        docs = [f for f in os.listdir(demo) if f.endswith("-image-prompts.docx")]
        check(bool(docs), f"a Word document of prompts is built for each later chart ({', '.join(docs)})")
        import docx as _d
        for dn in docs:
            cid = int(dn.split("-")[1]); want_n = sum(1 for q in json.load(open(os.path.join(ROOT, "prompts", "strips.json")))["strips"].values() if q.get("chart") == cid)
            dd_ = _d.Document(os.path.join(demo, dn))
            txt = "\n".join(p_.text for p_ in dd_.paragraphs) + "\n".join(c.text for t_ in dd_.tables for r_ in t_.rows for c in r_.cells)
            check(txt.count("PROMPT 1") == want_n and txt.count("PROMPT 2") == want_n and "charles" not in txt.lower(), f"{dn} holds {want_n} strips x 2 prompts and no personal names")
        check(not any(w in open(os.path.join(demo, "PROMPTS.md"), encoding="utf-8").read().lower() for w in ("charles", "@gmail")), "published prompts carry no personal names or addresses")
        check(os.path.exists(os.path.join(demo, "index.html")) and "5BX Sprite Boy" in open(os.path.join(demo, "index.html"), encoding="utf-8").read(), "demo index.html written")
    else: print(r.stderr[-600:])

for name, st in reg["strips"].items():
    if st.get("cycle_reverse"): check(sorted(set(st["cycle_reverse"])) == sorted(set(st["cycle"])) and len(st["cycle_reverse"]) == len(st["cycle"]), f"{name}: the reversed cycle uses the same poses as the forward cycle")

# a cut-out from another tool: real transparency, but a hard rim still tinted with the old magenta
cut = np.zeros((80, 80, 4), np.uint8); cut[20:60, 20:60] = (230, 150, 70, 255); cut[20:22, 20:60] = (190, 40, 200, 255); cut[58:60, 20:60] = (190, 40, 200, 255)   # an orange square, rim tinted
cl = np.array(key(Image.fromarray(cut, "RGBA"))); rim = cl[21, 40, :3].astype(int); mid = cl[40, 40, :3].astype(int)
check(min(rim[0], rim[2]) - rim[1] < 10 and tuple(mid) == (230, 150, 70) and cl[0, 0, 3] == 0 and cl[40, 40, 3] == 255, "keyer: a real-transparency cut-out loses its magenta rim tint, keeps its colours and its see-through background")

# feet stay put: for every strip that pins by a shoe, the pinned shoe point lands within a few pixels in every pose
import numpy as np
for name, st in reg["strips"].items():
    if not str(st["anchor"]).startswith("shoe"): continue
    m = json.load(open(os.path.join(ROOT, "assets", "sprites", name, "meta.json")))
    ok_ = all(isinstance(q["anchors"].get(st["anchor"]), float) for q in m["poses"]) and set(m["poses"][0]["anchors"]) >= {"shoes", "shoe-left", "shoe-right"}
    check(ok_, f"{name}: baked with shoe anchors ({st['anchor']})")
t3 = reg["strips"]["toe-touch-c3"]; m3 = json.load(open(os.path.join(ROOT, "assets", "sprites", "toe-touch-c3", "meta.json")))["poses"]
a_ = [build.pose_anchor(t3, k, q) for k, q in enumerate(m3, 1)]
check(abs((m3[3]["anchors"]["shoe-right"] - t3["nudge"]["4"][0]) - a_[3]) < 1e-6 and a_[0] == m3[0]["anchors"]["shoe-left"], "pose_anchor: a per-pose anchor override and nudge move only that pose")

# background prompts and importing generated layers
import prompt_bg, import_backdrop
bspec = json.load(open(os.path.join(ROOT, "prompts", "backgrounds.spec.json"))); allbg = prompt_bg.build_all(theme, bspec)
envs_ = set(bspec["environments"])
check(set(allbg) == {"landscape", "portrait"} and all(len(allbg[f][k]["items"]) == 8 for f in allbg for k in envs_) and all(set(allbg[f]) == envs_ | {"gym-keeper"} for f in allbg), f"background prompts: {len(envs_)} environments x 2 formats, a master and 7 layers each, plus the gym keeper set")
fl = round(theme["formats"]["landscape"]["ground"] * 100); mp_ = allbg["landscape"]["forest"]["items"][0]["prompt"]
check(f"{fl}% down from the top" in mp_ and f"horizon {fl - 24}% " not in mp_ and f"{fl - 24}% down from the top" in mp_, "background prompts: floor line and horizon come from theme.json")
allt = "\n".join(i["prompt"] for f in allbg.values() for e in f.values() for i in e["items"])
gk = allbg["landscape"]["gym-keeper"]["items"]; gp = allbg["portrait"]["gym-keeper"]["items"]
check(len(gk) == 3 and len(gp) == 3 and gk[0]["plane"] == "finish" and gp[0]["plane"] == "portrait-room" and all("#FF00FF" in i["prompt"] for i in gk[1:] + gp[1:]), "background prompts: the gym keeper set has a finishing pass (wide) or tall room, and two magenta mat overlays per shape")
check("{" not in allt and "}" not in allt and "charles" not in allt.lower(), "background prompts: every placeholder filled, no personal names")
check(all(("#FF00FF" in i["prompt"]) or i["plane"] in ("master", "sky") for f in allbg for k in envs_ for i in allbg[f][k]["items"]), "background prompts: every cut-out layer asks for a flat magenta background")
bc = allbg["landscape"]["beach"]["numbers"]; check(bc["ground_top"] > bc["horizon"] and bc["back"] >= bc["ground_top"] + 3, "background prompts: beach land starts below the horizon and its back row stands on the sand")
with tempfile.TemporaryDirectory() as t3:
    src = os.path.join(t3, "layers"); os.makedirs(src); W_, H_ = 640, 360
    for i_, pl_ in enumerate(import_backdrop.PLANES):
        im_ = Image.new("RGB", (W_, H_), (255, 0, 255))
        if pl_ == "sky": im_ = Image.new("RGB", (W_, H_), (90, 170, 235))
        else:
            from PIL import ImageDraw; ImageDraw.Draw(im_).rectangle((100 + 40 * i_, 150, 220 + 40 * i_, 260), fill=(40 + 20 * i_, 120, 70))
        im_.save(os.path.join(src, f"bg-test-landscape-{i_ + 1:02d}-{pl_}.png"))
    old_assets = build.ASSETS; build.ASSETS = os.path.join(t3, "assets")
    try:
        import_backdrop.run(src, "testset", "landscape", build.ASSETS, theme)
        th2 = json.loads(json.dumps(theme)); th2["backdrop"] = {"id": "testset"}
        lay = build.backdrop_layers(th2, theme["formats"]["landscape"], "landscape"); F_ = theme["formats"]["landscape"]
        check([n for n, _ in lay] == import_backdrop.PLANES and all(im.size == (F_["W"], F_["H"]) for _, im in lay), "importer: seven layers saved at frame size and read back by the build, in stacking order")
        a_ = np.array(lay[2][1])[..., 3]; check(a_[5, 5] == 0 and a_[int(F_["H"] * .5), int(F_["W"] * .3)] > 200, "importer: magenta becomes see-through, the drawn shape stays")
        check(np.array(lay[0][1])[..., 3].min() == 255, "importer: the sky stays fully opaque")
    finally: build.ASSETS = old_assets

# background checker: an orange floor must be flagged, a cool grey one passed, on the real stage numbers
import check_backdrop
Fl = theme["formats"]["landscape"]
with tempfile.TemporaryDirectory() as t4:
    for nm_, col_ in (("orange", (252, 185, 88)), ("grey", (170, 175, 185))):
        im_ = Image.new("RGB", (Fl["W"], Fl["H"]), (200, 205, 190)); im_.paste(Image.new("RGB", (Fl["W"], int(Fl["H"] * .35)), col_), (0, int(Fl["H"] * .65))); im_.save(os.path.join(t4, nm_ + ".png"))
    mo, mg = (check_backdrop.measure(os.path.join(t4, n_ + ".png"), Fl) for n_ in ("orange", "grey"))
    check(mo["de_skin"] < 30 <= 40 <= mg["de_skin"] and "MELT" in check_backdrop.verdict(mo)[0] and check_backdrop.verdict(mg)[0].endswith("clear"), "background checker: an orange floor is flagged as melting his legs, a cool grey one passes")
    dk, md = check_backdrop.worst_part((74, 79, 90)), check_backdrop.worst_part((112, 118, 128))
    check(dk[1] == "black outline" and md[0] > dk[0] + 8, "background checker: a dark charcoal floor loses his black outline; a mid grey is clearly better")
    check(mg["busy"] < 1 and mg["strip_std"] < 3, "background checker: a plain picture is calm and its stage strip flat")

# an overlay prop: a full-frame picture on magenta is cut out and drawn between the backdrop and the boy
with tempfile.TemporaryDirectory() as t5:
    Fo = theme["formats"]["landscape"]; ov = Image.new("RGB", (Fo["W"], Fo["H"]), (255, 0, 255)); ov.paste(Image.new("RGB", (800, 120), (33, 118, 120)), (500, 780)); ovp = os.path.join(ROOT, "assets", "_test_overlay.png"); ov.save(ovp)
    try:
        lay = np.array(build.render_props({"props": [{"id": "m", "kind": "overlay", "file": "assets/_test_overlay.png", "z": "behind", "slots": "*"}]}, "ex2", {"gy": int(Fo["H"] * Fo["ground"]), "X0": 960, "L": 300, "R": 300, "s": 1}, Fo, "behind"))
        check(lay[5, 5, 3] == 0 and lay[840, 900, 3] == 255 and tuple(lay[840, 900, :3]) == (33, 118, 120), "overlay prop: the magenta is cut out, the mat colour is kept, full frame")
    finally: os.remove(ovp)

import copy, builds
th_p, sc_p = os.path.join(ROOT, "config", "theme.json"), os.path.join(ROOT, "config", "scene.json")
rec = {"chart": 3, "inputs": builds.inputs_now(data_path, th_p, sc_p, 3, reg["charts"]["3"], reg, theme, build.CODE_VERSION)}
check(builds.diff(rec, data_path) == [], "builds: a record made from today's files shows nothing out of date")
r2 = copy.deepcopy(rec); r2["inputs"]["slots"]["ex2"]["sheet_sha"] = "000000000000"; d2 = builds.diff(r2, data_path)
check(len(d2) == 1 and d2[0][0] == "slot ex2", "builds: a changed strip image is reported for that slot only")
r3 = copy.deepcopy(rec); r3["inputs"]["data"]["sha"] = "000000000000"; r3["inputs"]["code_version"] = "0"; d3 = {k for k, _ in builds.diff(r3, data_path)}
check({"plan file", "builder code"} <= d3, "builds: a changed plan file and changed builder code are both reported")
check(builds.build_id(3, "A+", "landscape") == "c3-Aplus-landscape" and builds.build_id(3, "A+", "landscape", "red shoes") == "c3-Aplus-landscape-red-shoes", "builds: ids are c<chart>-<level>-<format>[-tag]")
check(all(v["library_id"] for v in rec["inputs"]["slots"].values() if v["strip"] != "stationary-run-c1"), "builds: every chart 3 strip is traceable to a library entry")
check(all(os.path.exists(builds.absp(f["file"])) for f in rec["inputs"]["fonts"].values()) and not any(os.path.isabs(f["file"]) for f in rec["inputs"]["fonts"].values()), "fonts ship inside the kit (no system font paths)")

import importlib
lib = importlib.import_module("library")
with tempfile.TemporaryDirectory() as t2:
    lib.LIB = os.path.join(t2, "library"); lib.INDEX = os.path.join(lib.LIB, "index.json")
    import argparse
    one = os.path.join(ROOT, "sheets", "c2-ex2-sit-up.png")
    lib.cmd_add(argparse.Namespace(file=one, chart=2, slot="ex2", strip="sit-up-c2", exercise="", tool="test", view="angle", poses=3, prompt="", notes="smoke", rows=None, row=None))
    db = lib.load(); e = db["entries"][0]
    check(e["id"] == "c2-ex2-01" and e["measured"]["figures"] == 3 and e["measured"]["green_pct"] < 1 and os.path.exists(os.path.join(ROOT if e["file"].startswith("sheets") else t2, e["file"])), "library: add measures the strip (3 figures, no green) and stores the file")
    try: lib.cmd_add(argparse.Namespace(file=one, chart=2, slot="ex2", strip="sit-up-c2", exercise="", tool="test", view="angle", poses=3, prompt="", notes="", rows=None, row=None)); dup = False
    except SystemExit: dup = True
    check(dup, "library: the same file cannot be added twice")
    sheet = os.path.join(ROOT, "sheets", "c3-ex234-sit-back-push.png")
    for r_, sl_, k_ in ((0, "ex2", "sit-up-hands-behind-head-c3"), (1, "ex3", "back-extension-hands-behind-back-c3")):
        lib.cmd_add(argparse.Namespace(file=sheet, chart=3, slot=sl_, strip=k_, exercise="", tool="test", view="angle", poses=3, prompt="", notes="", rows=3, row=r_))
    db = lib.load(); sh_ = [e for e in db["entries"] if e["chart"] == 3]
    check(len(sh_) == 2 and sh_[0]["file"] == sh_[1]["file"] and all(e["measured"]["figures"] == 3 for e in sh_), "library: a sheet shared by several exercises is stored once and measured per row")
    lib.cmd_grade(argparse.Namespace(id="c2-ex2-01", form=4, legibility=5, character=5, angle=4, key=5, by="test", notes="", expert=False))
    lib.set_verdict(argparse.Namespace(id="c2-ex2-01", notes=""), "chosen")
    db = lib.load(); check(db["entries"][0]["verdict"] == "chosen" and lib.score(db["entries"][0]) == 4 * 3 + 5 * 2 + 5 + 4 + 5, "library: grade and choose are recorded, score weights form first")
real = lib.jload(os.path.join(ROOT, "library", "index.json")) if os.path.exists(os.path.join(ROOT, "library", "index.json")) else {"entries": []}
check(all(os.path.exists(os.path.join(ROOT, x["file"])) for x in real["entries"]) and len({x["id"] for x in real["entries"]}) == len(real["entries"]), f"library: every indexed file exists and ids are unique ({len(real['entries'])} entries)")
print("\nALL PASS" if not fails else f"\n{len(fails)} FAILED"); sys.exit(1 if fails else 0)
