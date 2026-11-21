import numpy as np, colorsys
from PIL import Image

B = r"C:\Users\charl\OneDrive\Desktop\overnight\jobs-B"
def L(n):
    return np.array(Image.open(B + "\\" + n).convert("RGB")).astype(int)

def hexs(c):
    return "#%02x%02x%02x" % tuple(int(v) for v in c)

print("== strip 73-86% flatness (middle 80% of width), floor colour, horizontal seam rows ==")
for n in ["JOB-24.png", "JOB-25.png", "JOB-26.png", "JOB-28.png", "JOB-29.png"]:
    a = L(n); h, w = a.shape[:2]
    y0, y1 = int(.73 * h), int(.86 * h)
    strip = a[y0:y1, int(.1 * w):int(.9 * w)]
    mid = strip[:, int(.3 * w):int(.5 * w)]  # centre stretch
    std = strip.reshape(-1, 3).std(0)
    # row-to-row mean jumps inside strip = horizontal seams
    rows = strip.mean(1).sum(1)
    jumps = np.abs(np.diff(rows))
    seam_rows = [(y0 + i, round(float(j), 1)) for i, j in enumerate(jumps) if j > 12]
    print(f"{n}: strip mean={hexs(strip.reshape(-1,3).mean(0))} std={std.round(1)} range lum {int(strip.sum(-1).min()/3)}-{int(strip.sum(-1).max()/3)}; row-jumps>12 at {seam_rows[:6]}")

print()
print("== JOB-25: warm/orange/red pixels on brick wall area ==")
a = L("JOB-25.png"); h, w = a.shape[:2]
wall = a[int(.12*h):int(.68*h), int(.06*w):int(.95*w)]
cnt = 0; tot = 0; locs = []
rgb = wall / 255.0
mx = rgb.max(-1); mn = rgb.min(-1); sat = np.where(mx > 0, (mx - mn) / np.maximum(mx, 1e-6), 0)
r, g, b = rgb[..., 0], rgb[..., 1], rgb[..., 2]
warm = (r > b + 0.12) & (r >= g) & (sat > 0.25)   # orange/red/yellow-ish, excluding greys/blues
ys, xs = np.where(warm)
print(f"warm px in wall region: {warm.sum()} of {warm.size} ({warm.mean():.2%})")
if len(xs):
    X = xs + int(.06*w); Y = ys + int(.12*h)
    print(f"  warm bbox x {X.min()}-{X.max()} y {Y.min()}-{Y.max()}")
    # exclude shelves (x<240 or x>1690) and see what's left
    sel = (X > 240) & (X < 1690)
    print(f"  warm px excluding shelf columns: {sel.sum()}")
    # median colour of warm px at upper-left
    ul = (X < 700) & (Y < 300)
    if ul.any():
        print("  upper-left warm px:", ul.sum(), "median colour", hexs(np.median(a[Y[ul], X[ul]], axis=0)))
# brick colour in middle third
mid = a[int(.3*h):int(.6*h), int(.4*w):int(.6*w)]
print("  centre-third brick mean:", hexs(mid.reshape(-1,3).mean(0)), "(target #8C9BAA)")

print()
print("== JOB-28: rubber track rows/colour ==")
a = L("JOB-28.png"); h, w = a.shape[:2]
col = a[:, w // 2]
# track = grey-blue near (112,118,128)
tgt = np.array([112, 118, 128])
d = np.abs(col - tgt).sum(1)
rows = np.where(d < 30)[0]
print(f"track rows at centre col: {rows.min()/h:.3f} - {rows.max()/h:.3f}  (need to cover 0.73-0.86); median colour {hexs(np.median(col[rows],axis=0))}")
tk = a[rows.min()+5:rows.max()-5, int(.1*w):int(.9*w)]
print("  track std:", tk.reshape(-1,3).std(0).round(1))
# does the track span full width at a row?
r = (rows.min()+rows.max())//2
rowpx = a[r]
print("  track coverage across width at mid row:", float((np.abs(rowpx - tgt).sum(1) < 30).mean()))

print()
print("== JOB-29 vs keeper (taken from JOB-20 preview, upper room only) ==")
k = L("JOB-20-bg-gym-landscape-mat-teal-preview.png")
j = L("JOB-29.png")
h, w = j.shape[:2]
print("shapes", k.shape, j.shape)
top = slice(0, int(.60*h))
diff = np.abs(k[top] - j[top]).sum(-1)
print(f"top 60% mean abs diff per px: {diff.mean():.1f}; >60 diff px: {(diff>60).mean():.2%}")
# split by region: left third, middle third, right third
for nm, sl in [("left", slice(0, w//3)), ("mid", slice(w//3, 2*w//3)), ("right", slice(2*w//3, w))]:
    dd = diff[:, sl]
    print(f"  {nm}: >60 diff {(dd>60).mean():.2%}")
# floor region (below 62%) away from the mat (mat is in preview) - compare top of floor only 62-72%
fl = slice(int(.62*h), int(.72*h))
df = np.abs(k[fl] - j[fl]).sum(-1)
print(f"floor 62-72%: mean diff {df.mean():.1f}, >30 {(df>30).mean():.2%}")
