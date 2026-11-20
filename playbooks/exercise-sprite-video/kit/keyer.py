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


def clean_cutout(im, ring=2, feather=0.7):
    """A cut-out that already has transparency, from another tool, usually has a hard-edged rim still tinted with the old background colour.
    Remove the tint on the outermost pixels (the same despill as the key), give the see-through pixels a dark colour so resizing cannot pull
    magenta in, and soften the edge slightly. Measured on a ChatGPT cut-out: 80% of the outline pixels were tinted before, none after."""
    from PIL import ImageFilter
    a = np.array(im.convert("RGBA")); solid = a[..., 3] > 128; band = np.zeros_like(solid); cur = solid.copy()
    for _ in range(ring):                                                    # the outer `ring` pixels of the figure
        n = cur.copy(); n[1:] &= cur[:-1]; n[:-1] &= cur[1:]; n[:, 1:] &= cur[:, :-1]; n[:, :-1] &= cur[:, 1:]; band |= cur & ~n; cur = n
    rgb = a[..., :3].astype(np.int16); ex = np.maximum(np.minimum(rgb[..., 0], rgb[..., 2]) - rgb[..., 1], 0)
    for c in (0, 2): rgb[..., c] = np.where(band, rgb[..., c] - ex, rgb[..., c])
    rgb = np.clip(rgb, 0, 255); rgb[~solid] = (24, 24, 28)                    # outline colour behind the edge, never the old background
    alpha = Image.fromarray((solid * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(feather)); al = np.array(alpha)
    return Image.fromarray(np.dstack([rgb.astype(np.uint8), np.where(solid, np.maximum(al, 200), al).astype(np.uint8)]), "RGBA")


def key(im, lo=28, hi=95):
    """Magenta background -> transparency. A strip that already has real transparency is cleaned up (rim tint removed) and used."""
    if has_real_transparency(im): return clean_cutout(im)
    rgb = np.array(im.convert("RGB"))
    ex = magenta_excess(rgb)
    alpha = np.clip((hi - ex) / (hi - lo), 0, 1)
    out = rgb.astype(np.int16)
    spill = np.maximum(ex, 0)
    out[..., 0] = np.clip(out[..., 0] - spill, 0, 255)   # despill: pull R and B down by the excess
    out[..., 2] = np.clip(out[..., 2] - spill, 0, 255)
    return Image.fromarray(np.dstack([out.astype(np.uint8), (alpha * 255).astype(np.uint8)]), "RGBA")
