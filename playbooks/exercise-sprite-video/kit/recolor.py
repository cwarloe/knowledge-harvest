"""Free recolor of the cut-out boy by hue region. Alpha is never touched; no credits spent.

Each region is a hue band plus a saturation/brightness floor, so the cyan tank, the blue shoes,
the red shorts and the tan skin stay separate. Saturation and brightness are kept, so the
cel-shaded shadow tones follow the new colour (the darker far-side shoe stays darker).
"""
import numpy as np
from PIL import Image

REGIONS = {
    "shorts": dict(h=(345, 15), smin=.45, vmin=.25),
    "shoes":  dict(h=(212, 255), smin=.40, vmin=.15),
    "tank":   dict(h=(170, 208), smin=.45, vmin=.30),
}


def recolor(rgba, changes):
    """changes: {"shorts": hue_degrees, ...}; None or missing means leave alone."""
    changes = {k: v for k, v in (changes or {}).items() if k in REGIONS and v is not None}
    if not changes:
        return rgba
    a = np.array(rgba)
    hsv = np.array(Image.fromarray(a[..., :3], "RGB").convert("HSV")).astype(np.float32)
    H, S, V = hsv[..., 0] * 360 / 255, hsv[..., 1] / 255, hsv[..., 2] / 255
    opaque = a[..., 3] > 16
    for name, target in changes.items():
        r = REGIONS[name]; lo, hi = r["h"]
        in_band = ((H >= lo) | (H <= hi)) if lo > hi else ((H >= lo) & (H <= hi))
        m = in_band & (S >= r["smin"]) & (V >= r["vmin"]) & opaque
        hsv[..., 0] = np.where(m, target * 255 / 360, hsv[..., 0])
    out = np.array(Image.fromarray(hsv.astype(np.uint8), "HSV").convert("RGB"))
    return Image.fromarray(np.dstack([out, a[..., 3]]), "RGBA")
