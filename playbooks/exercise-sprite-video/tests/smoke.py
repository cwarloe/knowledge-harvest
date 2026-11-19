#!/usr/bin/env python3
"""Quick checks that a change did not break the kit.  python3 tests/smoke.py path/to/5bx-charts.json
Takes about 15 seconds. Checks: every registered strip exists and splits into its declared pose count;
recolouring never touches transparency; the config files agree with each other; one exercise renders and decodes."""
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
fails = []
def check(ok, msg):
    print(("ok   " if ok else "FAIL ") + msg); (None if ok else fails.append(msg))

for name, st in reg["strips"].items():
    p = os.path.join(ROOT, "sheets", st["file"])
    if not os.path.exists(p): check(False, f"{name}: missing file {st['file']}"); continue
    try: n = len(build.split(p, st["poses"], theme))
    except SystemExit as e: check(False, f"{name}: {e}"); continue
    check(n == st["poses"], f"{name}: splits into {n} poses")
    check(max(st["cycle"]) <= st["poses"], f"{name}: cycle only uses poses that exist")

k = key(Image.open(os.path.join(ROOT, "sheets", reg["strips"]["toe-touch-c1"]["file"])), **theme["key"])
r = recolor(k, {"shorts": 215, "shoes": 2, "tank": 120})
check(np.array_equal(np.array(k)[..., 3], np.array(r)[..., 3]), "recolor leaves transparency untouched")
check(np.array_equal(np.array(k), np.array(recolor(k, {}))), "recolor with no changes is a no-op")
for c, slots in reg["charts"].items():
    for slot, key_ in slots.items(): check(key_ in reg["strips"], f"chart {c} slot {slot} points at a known strip")

with tempfile.TemporaryDirectory() as tmp:
    out = os.path.join(tmp, "t.mp4")
    r = subprocess.run([sys.executable, os.path.join(ROOT, "kit", "build.py"), "--data", data_path, "--preview", "--only", "ex3",
                        "--work", os.path.join(tmp, "w"), "--out", out], capture_output=True, text=True)
    check(r.returncode == 0 and os.path.exists(out), "one exercise renders and passes the decode check")
    if os.path.exists(out):
        dur = float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", out], capture_output=True, text=True).stdout)
        check(abs(dur - 5.0) < 0.2, f"preview of one exercise is 5 s (got {dur:.1f})")
    else: print(r.stderr[-800:])
print("\nALL PASS" if not fails else f"\n{len(fails)} FAILED"); sys.exit(1 if fails else 0)
