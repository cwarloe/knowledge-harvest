#!/usr/bin/env python3
"""Turn generated background layers into a backdrop the build can use.

  python3 kit/import_backdrop.py --id beach --dir ~/Downloads/beach-layers            # landscape
  python3 kit/import_backdrop.py --id beach --dir ~/Downloads/beach-layers --format portrait

--dir holds one image per layer; a file is matched by the layer name in its file name (the names the prompts suggest work:
bg-beach-landscape-03-far.png). Layers, back to front: sky, clouds, far, near, ground, back, front. Missing layers are skipped.
Each image is cut out from the magenta (sky and ground stay opaque), fitted to the frame, and saved as
assets/backdrops/<id>/<format>/NN-<layer>.png with a manifest marked "source": "images", so the build uses the files as they are.
To use it: set "backdrop": {"id": "<id>"} in config/theme.json (or a copy of it passed with --theme), then rebuild.
A contact sheet of the stacked result is written next to the layers (preview.png) so you can check it before rendering anything.
"""
import argparse, json, os, re, sys
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE); sys.path.insert(0, HERE)
PLANES = ["sky", "clouds", "far", "near", "ground", "back", "front"]; OPAQUE = {"sky"}


def fit(im, W, H):
    """Cover-fit, then centre-crop, so a slightly different aspect never stretches the drawing."""
    sc = max(W / im.width, H / im.height); im = im.resize((max(W, round(im.width * sc)), max(H, round(im.height * sc))), Image.LANCZOS)
    x, y = (im.width - W) // 2, (im.height - H) // 2; return im.crop((x, y, x + W, y + H))


def find(folder, plane):
    pat = re.compile(rf"(^|[^a-z]){plane}([^a-z]|$)", re.I)
    hits = sorted(f for f in os.listdir(folder) if f.lower().endswith((".png", ".jpg", ".jpeg", ".webp")) and pat.search(os.path.splitext(f)[0]))
    return hits[-1] if hits else None                                      # the newest-named take wins


def run(folder, bid, fmt, assets, theme):
    from keyer import key
    F = theme["formats"][fmt]; W, H = F["W"], F["H"]; d = os.path.join(assets, "backdrops", bid, fmt); os.makedirs(d, exist_ok=True)
    for f in os.listdir(d):
        if f.endswith(".png"): os.remove(os.path.join(d, f))
    names, notes = [], []
    for plane in PLANES:
        fn = find(folder, plane)
        if not fn: notes.append(f"  {plane}: no file found"); continue
        im = Image.open(os.path.join(folder, fn)); im = fit(im.convert("RGB") if plane in OPAQUE else im, W, H)
        im = im.convert("RGBA") if plane in OPAQUE else key(im.convert("RGB"))                  # the magenta becomes see-through; the sky stays a picture
        out = f"{len(names):02d}-{plane}.png"; im.save(os.path.join(d, out)); names.append([plane, out]); notes.append(f"  {plane}: {fn}")
    if not names: sys.exit(f"no layer images found in {folder} (file names need sky, clouds, far, near, ground, back or front in them)")
    json.dump({"source": "images", "layers": names, "size": [W, H]}, open(os.path.join(d, "manifest.json"), "w"), indent=1)
    base = Image.new("RGBA", (W, H), (30, 36, 48, 255))
    for _, out in names: base.alpha_composite(Image.open(os.path.join(d, out)).convert("RGBA"))
    gy = int(H * F["ground"]); from PIL import ImageDraw; dr = ImageDraw.Draw(base)
    dr.line((0, gy, W, gy), fill=(255, 80, 40, 255), width=3); bh = F["box"][1]; dr.rectangle((W / 2 - 60, gy - bh, W / 2 + 60, gy), outline=(255, 255, 255, 255), width=3)   # floor line and the boy's size
    base.convert("RGB").resize((W // 2, H // 2)).save(os.path.join(d, "preview.png"))
    print(f"imported {len(names)} layers into {os.path.relpath(d, ROOT)}\n" + "\n".join(notes) + f"\npreview (orange line = his feet, white box = his height): {os.path.relpath(os.path.join(d, 'preview.png'), ROOT)}")
    if len(names) < 7: print(f"  note: {7 - len(names)} layer(s) missing; the stack is built from the ones present")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--id", required=True); ap.add_argument("--dir", required=True); ap.add_argument("--format", default="landscape", choices=["landscape", "portrait"])
    ap.add_argument("--theme", default=os.path.join(ROOT, "config", "theme.json")); a = ap.parse_args()
    run(a.dir, a.id, a.format, os.path.join(ROOT, "assets"), json.load(open(a.theme)))


if __name__ == "__main__": main()
