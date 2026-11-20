import sys, glob, os
import numpy as np
from PIL import Image

A = r"C:\Users\charl\OneDrive\Desktop\overnight\jobs-A"
B = r"C:\Users\charl\OneDrive\Desktop\overnight\jobs-B"

def load(p):
    return Image.open(p)

def magentaness(arr):
    d = np.abs(arr[..., :3].astype(int) - np.array([255, 0, 255])).sum(-1)
    return d

print("=== SPRITE SHEETS: size, bg exactness, figure boxes ===")
for p in sorted(glob.glob(A + r"\JOB-*.png")):
    im = load(p).convert("RGB")
    a = np.array(im)
    h, w = a.shape[:2]
    d = magentaness(a)
    exact = (d == 0).mean()
    near = (d <= 30).mean()
    # corner colour
    corners = [tuple(a[y, x]) for y, x in [(2, 2), (2, w - 3), (h - 3, 2), (h - 3, w - 3)]]
    fg = d > 90
    cols = fg.any(0)
    # figure column runs
    runs = []
    start = None
    for x in range(w):
        if cols[x] and start is None:
            start = x
        if not cols[x] and start is not None:
            runs.append((start, x - 1)); start = None
    if start is not None:
        runs.append((start, w - 1))
    runs = [r for r in runs if r[1] - r[0] > 20]
    gaps = [runs[i + 1][0] - runs[i][1] for i in range(len(runs) - 1)]
    print(f"{os.path.basename(p)}: {w}x{h} exact#FF00FF={exact:.1%} within30={near:.1%} corners={corners[0]}")
    print(f"   col-runs={len(runs)} min-gap={min(gaps) if gaps else None}px  edge-touch L={fg[:, 0].any()} R={fg[:, -1].any()} T={fg[0].any()} B={fg[-1].any()}")

print()
print("=== MAT PNGs: bbox, colour ===")
for p in sorted(glob.glob(B + r"\JOB-2[0-3]-*mat-*.png")):
    n = os.path.basename(p)
    if "preview" in n:
        continue
    im = load(p)
    if "transparent" in n:
        a = np.array(im.convert("RGBA"))
        al = a[..., 3]
        solid = al > 250
        semi = (al > 0) & (al <= 250)
        ys, xs = np.where(al > 0)
        h, w = al.shape
        print(f"{n}: {w}x{h} bbox L{xs.min()/w:.3f} T{ys.min()/h:.3f} R{xs.max()/w:.3f} B{ys.max()/h:.3f}")
        # fringe: semi/edge pixels that are magenta-ish
        edge = al > 0
        rgb = a[..., :3].astype(int)
        mg = (rgb[..., 0] > 150) & (rgb[..., 2] > 150) & (rgb[..., 1] < 120)  # pinkish
        print(f"   solid px={solid.sum()} semi-alpha px={semi.sum()} magenta-ish visible px={(mg & edge).sum()} ({(mg & edge).sum()/max(edge.sum(),1):.3%} of visible)")
        mid = rgb[solid][len(rgb[solid]) // 2] if solid.any() else None
        print(f"   median solid colour={np.median(rgb[solid],axis=0).astype(int)}")
    else:
        a = np.array(im.convert("RGB"))
        h, w = a.shape[:2]
        d = magentaness(a)
        bg_exact = (d == 0).mean()
        m = d > 90
        ys, xs = np.where(m)
        print(f"{n}: {w}x{h} bg exact magenta={ (d==0).sum()/ (~m).sum() if False else bg_exact:.1%} bbox L{xs.min()/w:.3f} T{ys.min()/h:.3f} R{xs.max()/w:.3f} B{ys.max()/h:.3f}")
        # far / near edge widths
        def span(row):
            r = np.where(m[row])[0]
            return (r.min() / w, r.max() / w) if len(r) else None
        t = ys.min() + 4
        b = ys.max() - 10
        print(f"   far-edge span(row {t/h:.3f})={span(t)}  near-edge span(row {b/h:.3f})={span(b)}")
        print(f"   mat median colour (hex)={'#%02x%02x%02x' % tuple(np.median(a[m],axis=0).astype(int))}")
        # fully-flat-magenta check: pixels not exactly magenta but within 30 and outside mat
        near_not_exact = ((d > 0) & (d <= 30)).sum()
        print(f"   near-magenta-but-not-exact px={near_not_exact}")

print()
print("=== GYM PORTRAIT JOB-19: wall/floor line, strip flatness ===")
for n in ["JOB-19-bg-gym-portrait-final.png", "JOB-19-bg-gym-portrait-plain-window-candidate.png"]:
    a = np.array(load(B + "\\" + n).convert("RGB")).astype(int)
    h, w = a.shape[:2]
    col = a[:, w // 2]
    diff = np.abs(np.diff(col, axis=0)).sum(1)
    # strongest transition between 45% and 65%
    lo, hi = int(.45 * h), int(.65 * h)
    y = lo + np.argmax(diff[lo:hi])
    strip = a[int(.67 * h):int(.80 * h), int(.1 * w):int(.9 * w)]
    print(f"{n}: {w}x{h} wall/floor line ~{y/h:.3f}; strip67-80 std per channel={strip.reshape(-1,3).std(0).round(1)} min/max lum range={strip.sum(-1).min()//3}-{strip.sum(-1).max()//3}; floor mean={strip.reshape(-1,3).mean(0).astype(int)}")
    # centre third of wall busy-ness (edges count) between 20% and 50%
    cw = a[int(.2*h):int(.5*h), w//3:2*w//3].sum(-1)
    gx = np.abs(np.diff(cw, axis=1)) > 60
    print(f"   centre-third wall strong-edge density={gx.mean():.4f}")

print()
print("=== FOREST JOB-27 variations: horizon / strip emptiness / sky ===")
for p in sorted(glob.glob(B + r"\JOB-27-variation-*.png")):
    a = np.array(load(p).convert("RGB")).astype(int)
    h, w = a.shape[:2]
    # horizon: in centre columns, first row (from 45% down) where pixel becomes green-ish/tan ground after hills.
    # report the strongest vertical colour change between 55% and 70% averaged over middle 20% columns
    mid = a[:, int(.4*w):int(.6*w)].mean(1)
    d = np.abs(np.diff(mid, axis=0)).sum(1)
    lo, hi = int(.50*h), int(.72*h)
    ys = np.argsort(d[lo:hi])[::-1][:3] + lo
    print(os.path.basename(p) + f": {w}x{h} strongest centre transitions at " + ", ".join(f"{y/h:.3f}" for y in sorted(ys)))
    strip = a[int(.73*h):int(.86*h)]
    # edge density in strip (non-flat objects)
    g = (np.abs(np.diff(strip.sum(-1), axis=1)) > 45)
    cols = g.mean(0)
    thirds = [cols[:w//3].mean(), cols[w//3:2*w//3].mean(), cols[2*w//3:].mean()]
    print(f"   strip73-86 edge density L/M/R = {[round(float(t),4) for t in thirds]}  middle-third max col density={cols[w//3:2*w//3].max():.3f}")
    # magenta/pink pixels anywhere
    pink = ((a[...,0] > 170) & (a[...,2] > 150) & (a[...,1] < 110)).sum()
    print(f"   pink/magenta-ish px={pink}")
