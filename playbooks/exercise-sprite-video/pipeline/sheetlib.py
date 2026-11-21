"""Shared helpers: config loading, background measurement, figure segmentation of a pose sheet."""
import os
import re
import tomllib
import numpy as np
import cv2
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))


def load_toml(path):
    with open(path, "rb") as f:
        return tomllib.load(f)


def load_exercises():
    return load_toml(os.path.join(HERE, "exercises.toml"))["exercise"]


def load_character(name_or_path):
    p = name_or_path
    if not os.path.exists(p):
        p = os.path.join(HERE, "characters", name_or_path if name_or_path.endswith(".toml") else name_or_path + ".toml")
    return load_toml(p)


def load_stage():
    return load_toml(os.path.join(HERE, "stage.toml"))


def find_exercise(exercises, key):
    """key = slug, job number ('7', 'JOB-07') or a file name containing JOB-NN."""
    k = str(key)
    for e in exercises:
        if e["id"] == k:
            return e
    m = re.search(r"JOB-?(\d+)", k, re.I) or re.fullmatch(r"(\d+)", k)
    if m:
        n = int(m.group(1))
        for e in exercises:
            if e["job"] == n:
                return e
    raise KeyError(f"no exercise matches {key!r}")


def hex2rgb(h):
    h = h.lstrip("#")
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


def read_rgb(path):
    return np.array(Image.open(path).convert("RGB"))


def measure_bg(a, band=6):
    """Median colour of the outer border band, plus how far border pixels stray from it (99th percentile)."""
    border = np.concatenate([a[:band].reshape(-1, 3), a[-band:].reshape(-1, 3),
                             a[:, :band].reshape(-1, 3), a[:, -band:].reshape(-1, 3)]).astype(float)
    med = np.median(border, axis=0)
    dist = np.sqrt(((border - med) ** 2).sum(1))
    return med, float(np.percentile(dist, 99))


def fg_mask(a, bg, tol=60):
    d = np.sqrt(((a.astype(float) - bg) ** 2).sum(-1))
    return d > tol


def _overlap_merge(items):
    """items = [(bbox, labels)]. Merge when one box sits mostly inside another (a hand drawn as a separate
    shape); neighbouring figures whose boxes merely overlap a little stay separate."""
    items = [[list(b), set(l)] for b, l in items]
    changed = True
    while changed:
        changed = False
        out = []
        while items:
            b = items.pop()
            for o in out:
                ix = min(b[0][0] + b[0][2], o[0][0] + o[0][2]) - max(b[0][0], o[0][0])
                iy = min(b[0][1] + b[0][3], o[0][1] + o[0][3]) - max(b[0][1], o[0][1])
                inter = ix * iy if ix > 0 and iy > 0 else 0
                if inter >= 0.5 * min(b[0][2] * b[0][3], o[0][2] * o[0][3]):
                    x0 = min(b[0][0], o[0][0]); y0 = min(b[0][1], o[0][1])
                    x1 = max(b[0][0] + b[0][2], o[0][0] + o[0][2]); y1 = max(b[0][1] + b[0][3], o[0][1] + o[0][3])
                    o[0] = [x0, y0, x1 - x0, y1 - y0]; o[1] |= b[1]
                    changed = True
                    break
            else:
                out.append(b)
        items = out
    return [(tuple(b), l) for b, l in items]


def _rect_dist(px, py, bbox):
    x, y, w, h = bbox
    dx = max(x - px, 0, px - (x + w)); dy = max(y - py, 0, py - (y + h))
    return (dx * dx + dy * dy) ** 0.5


def segment(a, bg, rows_expected=1, min_area_frac=0.0015, attach_dist=30):
    """Find the figures on a sheet. Returns (rows, labels): rows = list (top to bottom) of lists (left to right)
    of dicts {bbox:(x,y,w,h), labels:set of component ids}; labels = connected-component label image.
    Large shapes are figures; small detached bits (a hand, a hair spike) join the nearest figure within attach_dist."""
    h, w = a.shape[:2]
    m = fg_mask(a, bg).astype(np.uint8)
    n, lab, stats, cent = cv2.connectedComponentsWithStats(m, connectivity=8)
    thr = min_area_frac * w * h
    big = [(tuple(int(v) for v in stats[i][:4]), {i}) for i in range(1, n) if stats[i][4] >= thr]
    merged = _overlap_merge(big)
    figs = [dict(bbox=b, labels=set(l)) for b, l in merged]
    if not figs:
        return [], lab
    bigids = {i for f in figs for i in f["labels"]}
    for i in range(1, n):
        if i in bigids or stats[i][4] < 4:
            continue
        cx, cy = cent[i]
        best = min(figs, key=lambda f: _rect_dist(cx, cy, f["bbox"]))
        if _rect_dist(cx, cy, best["bbox"]) <= attach_dist:
            best["labels"].add(i)
            # grow the figure's box to include the attached piece so cropping and the feet pivot see it
            sx, sy, sw, sh = (int(v) for v in stats[i][:4])
            bx, by, bw, bh = best["bbox"]
            x0, y0 = min(bx, sx), min(by, sy)
            x1, y1 = max(bx + bw, sx + sw), max(by + bh, sy + sh)
            best["bbox"] = (x0, y0, x1 - x0, y1 - y0)
    figs.sort(key=lambda f: f["bbox"][1] + f["bbox"][3] / 2)
    cyv = [f["bbox"][1] + f["bbox"][3] / 2 for f in figs]
    if rows_expected > 1 and len(figs) >= rows_expected:
        gaps = sorted(range(len(cyv) - 1), key=lambda i: cyv[i + 1] - cyv[i], reverse=True)[:rows_expected - 1]
        groups, start = [], 0
        for c in sorted(gaps):
            groups.append(figs[start:c + 1]); start = c + 1
        groups.append(figs[start:])
    else:
        groups = [figs]
    return [sorted(g, key=lambda f: f["bbox"][0]) for g in groups], lab


def figure_mask(lab, a, fig, bg=None):
    """Boolean mask of every foreground pixel that belongs to one figure."""
    return np.isin(lab, list(fig["labels"]))


def clearance(lab, a, fa, fb, bg=None):
    """Smallest pixel distance between two figures (0 = touching)."""
    x0 = max(0, min(fa["bbox"][0], fb["bbox"][0]) - 2); y0 = max(0, min(fa["bbox"][1], fb["bbox"][1]) - 2)
    x1 = max(fa["bbox"][0] + fa["bbox"][2], fb["bbox"][0] + fb["bbox"][2]) + 2
    y1 = max(fa["bbox"][1] + fa["bbox"][3], fb["bbox"][1] + fb["bbox"][3]) + 2
    sub = lab[y0:y1, x0:x1]
    A = np.isin(sub, list(fa["labels"])); B = np.isin(sub, list(fb["labels"]))
    dt = cv2.distanceTransform((~A).astype(np.uint8), cv2.DIST_L2, 3)
    return float(dt[B].min()) if B.any() else float("inf")
