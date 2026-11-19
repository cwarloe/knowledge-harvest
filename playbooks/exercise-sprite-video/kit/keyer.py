"""Cut the boy out of a generated strip: soft-magenta background -> transparency.

Key on "how much more magenta than green is this pixel", with a ramp, then despill the rim.
Why not an exact-colour key: the generated background drifts (255,59,253 centre to 246,84,238
corner) and the model adds a purple ground shadow even when told not to. Both have a high
magenta excess, so both key out. Skin, red, blue, white and black all sit near zero.
"""
import numpy as np
from PIL import Image


def magenta_excess(rgb):
    r, g, b = (rgb[..., i].astype(np.int16) for i in range(3))
    return np.minimum(r, b) - g


def has_real_transparency(im):
    """True for a PNG that already carries a see-through background (not a picture of a checkerboard)."""
    if im.mode not in ("RGBA", "LA", "PA") and "transparency" not in im.info: return False
    a = np.array(im.convert("RGBA"))[..., 3]
    return bool((a < 250).mean() > 0.05)          # a real cut-out has a lot of see-through pixels


def key(im, lo=28, hi=95):
    """Magenta background -> transparency. A strip that already has real transparency is used as it is."""
    if has_real_transparency(im): return im.convert("RGBA")
    rgb = np.array(im.convert("RGB"))
    ex = magenta_excess(rgb)
    alpha = np.clip((hi - ex) / (hi - lo), 0, 1)
    out = rgb.astype(np.int16)
    spill = np.maximum(ex, 0)
    out[..., 0] = np.clip(out[..., 0] - spill, 0, 255)   # despill: pull R and B down by the excess
    out[..., 2] = np.clip(out[..., 2] - spill, 0, 255)
    return Image.fromarray(np.dstack([out.astype(np.uint8), (alpha * 255).astype(np.uint8)]), "RGBA")
