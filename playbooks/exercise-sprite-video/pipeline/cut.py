"""Cut-and-key: a checked sheet in, one transparent PNG per figure out, plus a manifest with the feet pivot."""
import json, os, re
import numpy as np
import cv2
from PIL import Image
import sheetlib as S


def slug(s):
    return re.sub(r"[^a-z0-9]+", "-", s.lower()).strip("-")


def key_alpha(a, bg, t0, t1):
    """Soft key: alpha ramps from 0 (colour within t0 of the background) to 1 (farther than t1)."""
    d = np.sqrt(((a.astype(float) - bg) ** 2).sum(-1))
    return np.clip((d - t0) / (t1 - t0), 0, 1)


def despill(rgb, alpha):
    """Remove magenta fringing: where red and blue both exceed green, pull them down to green + a margin.
    Skin, red shorts, cyan tank and blue shoes are untouched because one of red/blue stays low in each."""
    f = rgb.astype(float)
    r, g, b = f[..., 0], f[..., 1], f[..., 2]
    spill = (np.minimum(r, b) - g)
    edge = (alpha < 0.999) | (spill > 40)
    cap = g + 12
    fix = edge & (np.minimum(r, b) > cap)
    r2 = np.where(fix & (r > cap), cap, r)
    b2 = np.where(fix & (b > cap), cap, b)
    return np.stack([r2, g, b2], -1).clip(0, 255).astype(np.uint8)


def cut_sheet(path, ex, out_dir, pad=10, t0=None, t1=None):
    a = S.read_rgb(path)
    bg, spread = S.measure_bg(a)
    t0 = t0 if t0 is not None else max(25.0, spread + 8)
    t1 = t1 if t1 is not None else t0 + 55
    rows, lab = S.segment(a, bg, rows_expected=ex["qc"]["rows"])
    os.makedirs(out_dir, exist_ok=True)
    alpha_all = key_alpha(a, bg, t0, t1)
    h, w = a.shape[:2]
    manifest = dict(sheet=os.path.basename(path), exercise=ex["id"], job=ex["job"], background=[int(v) for v in bg], sprites=[])
    poses = ex["poses"]
    grounded = ex["qc"].get("grounded", [])
    for ri, row in enumerate(rows):
        # the floor line of this row = the median bottom of the poses that rest on it
        gb = [row[i]["bbox"][1] + row[i]["bbox"][3] for i in grounded if i < len(row)]
        floor_y = float(np.median(gb)) if gb else None
        for pi, f in enumerate(row):
            fm = S.figure_mask(lab, a, f, bg)
            # grow the mask a little so anti-aliased edge pixels (below the connected-component threshold) are kept
            fm = cv2.dilate(fm.astype(np.uint8), np.ones((5, 5), np.uint8)).astype(bool)
            al = np.where(fm, alpha_all, 0.0)
            x, y, bw, bh = f["bbox"]
            x0, y0, x1, y1 = max(0, x - pad), max(0, y - pad), min(w, x + bw + pad), min(h, y + bh + pad)
            crop_rgb = despill(a[y0:y1, x0:x1], al[y0:y1, x0:x1])
            rgba = np.dstack([crop_rgb, (al[y0:y1, x0:x1] * 255 + 0.5).astype(np.uint8)])
            label = poses[pi]["label"] if pi < len(poses) else f"pose{pi + 1}"
            name = f"{ex['id']}__r{ri + 1}p{pi + 1:02d}-{slug(label)}.png"
            Image.fromarray(rgba, "RGBA").save(os.path.join(out_dir, name))
            manifest["sprites"].append(dict(
                file=name, row=ri + 1, pose=pi + 1, label=label,
                sheet_bbox=[x, y, bw, bh], size=[x1 - x0, y1 - y0],
                pivot=[int(x + bw / 2 - x0), int(y + bh - y0)],   # bottom-centre of the figure inside the crop
                # pixels the figure's lowest point sits above the row's floor line: 0 when it rests on the floor,
                # positive in the air. Place sprites at (floor_y - lift_px) so jumps stay in the air.
                lift_px=int(round(floor_y - (y + bh))) if floor_y is not None else None,
            ))
    with open(os.path.join(out_dir, f"{ex['id']}.manifest.json"), "w", encoding="utf-8") as fh:
        json.dump(manifest, fh, indent=1)
    return manifest
