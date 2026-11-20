#!/usr/bin/env python3
"""Check a background picture against the stage the boy stands on, and preview it with the real sprites.

  python3 kit/check_backdrop.py bg1.png bg2.png [--format landscape] [--out preview-folder]

Three measurements, then a picture of the run and the push-up on it, built by the same code as the video:
  floor contrast   colour distance (CIE76) between the floor under his feet and his skin, shorts and shoes. Under 30 on the skin means his legs melt
                   into the floor (orange and tan floors do); 40 or more reads clearly.
  busy behind him  share of strong edges in the middle third, from his head down to the wall-floor line. Calm is up to 5%; above 8% it fights him.
  stage strip      how flat the strip around his feet is (the prompts ask for it to be empty). Lower is flatter.
Thresholds are rules of thumb from five generated backgrounds, not measured on viewers: a judgment still goes with the numbers.
"""
import argparse, json, os, shutil, sys, tempfile
import numpy as np
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE); sys.path.insert(0, HERE)
SKIN, SHORTS, SHOES = (235, 155, 65), (215, 35, 35), (50, 110, 200)


def lab(rgb):
    c = np.array(rgb, float) / 255; c = np.where(c > .04045, ((c + .055) / 1.055) ** 2.4, c / 12.92)
    xyz = (c @ np.array([[.4124, .3576, .1805], [.2126, .7152, .0722], [.0193, .1192, .9505]]).T) / np.array([.95047, 1, 1.08883])
    f = np.where(xyz > .008856, np.cbrt(xyz), 7.787 * xyz + 16 / 116); return np.array([116 * f[1] - 16, 500 * (f[0] - f[1]), 200 * (f[1] - f[2])])
def de(a, b): return float(np.linalg.norm(lab(a) - lab(b)))


def measure(path, F):
    a = np.array(Image.open(path).convert("RGB").resize((F["W"], F["H"]), Image.LANCZOS)).astype(float); H, W = a.shape[:2]; lum = a.mean(2)
    floor_y = F["ground"]; head_top = floor_y - F["box"][1] / H
    gm = np.hypot(np.abs(lum[:, 1:] - lum[:, :-1])[:-1, :], np.abs(lum[1:, :] - lum[:-1, :])[:, :-1])
    # the wall-floor line: the biggest brightness step in the middle between head height and 6% above his feet
    y0, y1 = int(H * (floor_y - .30)), int(H * (floor_y - .06)); step = np.abs(np.diff(a[y0:y1, int(W * .3):int(W * .7)].mean(axis=(1, 2)))); wall_floor = y0 + int(np.argmax(step))
    zone = gm[int(H * head_top):wall_floor, int(W * .33):int(W * .67)]
    floor = a[int(H * (floor_y - .06)):int(H * (floor_y + .10)), int(W * .35):int(W * .65)].reshape(-1, 3).mean(0)
    strip = lum[int(H * (floor_y - .07)):int(H * (floor_y + .06)), int(W * .30):int(W * .70)]
    return {"floor_rgb": tuple(int(v) for v in floor), "de_skin": de(floor, SKIN), "de_shorts": de(floor, SHORTS), "de_shoes": de(floor, SHOES),
            "busy": float((zone > 25).mean() * 100), "strip_std": float(strip.std()), "wall_floor_pct": round(100 * wall_floor / H)}


def verdict(m):
    v = []
    v.append("floor: " + ("clear" if m["de_skin"] >= 40 else "ok" if m["de_skin"] >= 30 else "LEGS MELT INTO THE FLOOR (change the floor to a cool grey, blue or green)"))
    v.append("behind him: " + ("calm" if m["busy"] <= 5 else "busy" if m["busy"] <= 8 else "VERY BUSY (move windows and objects to the sides)"))
    v.append("stage strip: " + ("flat" if m["strip_std"] <= 12 else "NOT FLAT (clear objects and lines near his feet)"))
    return v


def preview(path, fmt, out):
    """The run (standing) and the push-up (lying) on this background, through the same compose() the video uses."""
    import build
    theme = json.load(open(os.path.join(ROOT, "config", "theme.json"))); reg = json.load(open(os.path.join(ROOT, "config", "strips.json"))); scene = json.load(open(os.path.join(ROOT, "config", "scene.json")))
    bid = "_check-" + os.path.splitext(os.path.basename(path))[0]; theme["backdrop"] = {"id": bid, "style": "image", "image": os.path.abspath(path)}
    F = theme["formats"][fmt]; work = tempfile.mkdtemp(); tiles = []
    try:
        for chart, slot, k in (("4", "run", 1), ("3", "ex4", 3)):
            name = reg["charts"][chart][slot]; d = build.compose(name, reg["strips"][name], theme, scene, F, fmt, work, slot); tiles.append(Image.open(os.path.join(d, f"p{k}.png")).convert("RGB"))
    finally:
        shutil.rmtree(work, ignore_errors=True); shutil.rmtree(os.path.join(ROOT, "assets", "backdrops", bid), ignore_errors=True)
    S = Image.new("RGB", (F["W"] * 2, F["H"])); S.paste(tiles[0], (0, 0)); S.paste(tiles[1], (F["W"], 0)); S.resize((S.width // 2, S.height // 2)).save(out); return out


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("images", nargs="+"); ap.add_argument("--format", default="landscape", choices=["landscape", "portrait"]); ap.add_argument("--out", default=None, help="folder for the preview pictures")
    a = ap.parse_args(); F = json.load(open(os.path.join(ROOT, "config", "theme.json")))["formats"][a.format]
    for p in a.images:
        m = measure(p, F); print(f"{os.path.basename(p)}\n  floor {m['floor_rgb']}: distance to skin {m['de_skin']:.0f}, shorts {m['de_shorts']:.0f}, shoes {m['de_shoes']:.0f}   |   busy behind him {m['busy']:.1f}%   |   stage strip variation {m['strip_std']:.1f}")
        for line in verdict(m): print("  - " + line)
        if a.out:
            os.makedirs(a.out, exist_ok=True); print("  preview:", preview(p, a.format, os.path.join(a.out, os.path.splitext(os.path.basename(p))[0] + "-preview.png")))


if __name__ == "__main__": main()
