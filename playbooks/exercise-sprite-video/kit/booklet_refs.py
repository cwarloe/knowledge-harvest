#!/usr/bin/env python3
"""Turn the 5BX booklet drawings into pose references an image tool can read: black figures on white.

  python3 kit/booklet_refs.py --figures ../5BX/figures            # writes prompts/refs/BOOKLET-c{chart}e{exercise}.png for all 30

The 5BX app ships the booklet's drawings as white silhouettes on a transparent background (for its dark theme).
Image tools read that as a blank or white image, so this flattens them to dark grey on white with a margin.
The booklet is the authority on form: attach its drawing to any job whose pose keeps coming back wrong.
No text is added, so nothing can leak into the generated sheet.
"""
import argparse, glob, os
from PIL import Image

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); OUT = os.path.join(ROOT, "prompts", "refs")


def convert(src, dst, ink=(35, 35, 35), pad=40):
    im = Image.open(src).convert("RGBA"); a = im.getchannel("A")
    box = a.getbbox() or (0, 0, im.width, im.height); a = a.crop(box)
    out = Image.new("RGB", (a.width + 2 * pad, a.height + 2 * pad), (255, 255, 255))
    out.paste(Image.new("RGB", a.size, ink), (pad, pad), a)
    out.save(dst)


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--figures", required=True, help="the 5BX repo's figures/ folder"); a = ap.parse_args()
    os.makedirs(OUT, exist_ok=True); n = 0
    for f in sorted(glob.glob(os.path.join(a.figures, "c[1-6]e[1-5].png"))):
        convert(f, os.path.join(OUT, "BOOKLET-" + os.path.basename(f))); n += 1
    print(f"wrote {n} booklet references to {OUT}")
