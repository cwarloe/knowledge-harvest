"""Draw the four gym exercise-mat overlays exactly to the BATCH-B spec (jobs 20-23).

Per mat it writes:
  <name>.png              full frame, solid #FF00FF background, hard (non-antialiased) edges
  <name>-transparent.png  full frame RGBA, antialiased alpha, no magenta anywhere
and, when a room image is given, <name>-preview.png (mat composited on the room).

Usage: python draw_mats.py <out_dir> [room_tall.png] [room_wide.png]
"""
import sys, os
import numpy as np
from PIL import Image, ImageDraw

SS = 4  # supersampling factor

SPECS = {
    # near edge y, near x-range, far edge y, far x-range (all fractions of the frame)
    "wide": dict(size=(1920, 1080), near=(0.90, 0.05, 0.95), far=(0.73, 0.08, 0.92),
                 thick=12, border_inset=16, border_w=3, radius=28),
    "tall": dict(size=(1080, 1920), near=(0.84, 0.02, 0.98), far=(0.67, 0.05, 0.95),
                 thick=14, border_inset=18, border_w=4, radius=34),
}
COLOURS = {
    "teal": dict(top="#217678", line="#5FA3A5", front="#164f52"),
    "navy": dict(top="#243B66", line="#4B6FB5", front="#18284a"),
}
JOBS = [
    ("JOB-20-bg-gym-landscape-mat-teal", "wide", "teal"),
    ("JOB-21-bg-gym-landscape-mat-navy", "wide", "navy"),
    ("JOB-22-bg-gym-portrait-mat-teal", "tall", "teal"),
    ("JOB-23-bg-gym-portrait-mat-navy", "tall", "navy"),
]

def hex2rgb(h):
    h = h.lstrip("#"); return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))

def line_intersect(p1, d1, p2, d2):
    a = np.array([[d1[0], -d2[0]], [d1[1], -d2[1]]], float)
    b = np.array([p2[0] - p1[0], p2[1] - p1[1]], float)
    t = np.linalg.solve(a, b)
    return (p1[0] + t[0] * d1[0], p1[1] + t[0] * d1[1])

def inset_polygon(pts, d):
    """Move every edge of a convex polygon (clockwise in image coords) inward by d."""
    n = len(pts); lines = []
    for i in range(n):
        a, b = np.array(pts[i], float), np.array(pts[(i + 1) % n], float)
        e = (b - a) / np.linalg.norm(b - a)
        normal = np.array([-e[1], e[0]])  # inward for clockwise order in image coords
        lines.append((a + normal * d, e))
    out = []
    for i in range(n):
        p1, d1 = lines[i - 1]; p2, d2 = lines[i]
        out.append(line_intersect(p1, d1, p2, d2))
    return out

def rounded_mask(pts, r, size, shift=0):
    """Mask of a convex polygon with corners rounded to radius r (supersampled)."""
    W, H = size
    inner = inset_polygon(pts, r)
    m = Image.new("L", (W * SS, H * SS), 0)
    dr = ImageDraw.Draw(m)
    s = lambda p: (p[0] * SS, (p[1] + shift) * SS)
    dr.polygon([s(p) for p in inner], fill=255)
    n = len(inner)
    for i in range(n):  # fatten by r: line along each edge + a disc on each vertex
        dr.line([s(inner[i]), s(inner[(i + 1) % n])], fill=255, width=int(round(2 * r * SS)))
        x, y = s(inner[i]); R = r * SS
        dr.ellipse([x - R, y - R, x + R, y + R], fill=255)
    return m

def stroke_mask(pts, d, width, size):
    inner = inset_polygon(pts, d)
    W, H = size
    m = Image.new("L", (W * SS, H * SS), 0)
    dr = ImageDraw.Draw(m)
    n = len(inner)
    for i in range(n):
        a = (inner[i][0] * SS, inner[i][1] * SS); b = (inner[(i + 1) % n][0] * SS, inner[(i + 1) % n][1] * SS)
        dr.line([a, b], fill=255, width=int(round(width * SS)))
        R = width * SS / 2
        dr.ellipse([a[0] - R, a[1] - R, a[0] + R, a[1] + R], fill=255)
    return m

def down(m, size):
    return np.array(m.resize(size, Image.LANCZOS)).astype(float) / 255.0

def build(kind, colour):
    sp = SPECS[kind]; W, H = sp["size"]; c = COLOURS[colour]
    ny, nx0, nx1 = sp["near"]; fy, fx0, fx1 = sp["far"]
    # clockwise (image coords): far-left, far-right, near-right, near-left
    pts = [(fx0 * W, fy * H), (fx1 * W, fy * H), (nx1 * W, ny * H), (nx0 * W, ny * H)]
    r = sp["radius"]; t = sp["thick"]
    # rounding the near corners trims the widest point; widen the near vertices until the silhouette
    # reaches the spec x-range exactly
    for _ in range(3):
        sil = down(rounded_mask(pts, r, (W, H)), (W, H))
        xs = np.where((sil >= 0.5).any(0))[0]
        dl = xs.min() - nx0 * W; dr_ = nx1 * W - 1 - xs.max()
        pts[3] = (pts[3][0] - dl, pts[3][1]); pts[2] = (pts[2][0] + dr_, pts[2][1])
    sil = down(rounded_mask(pts, r, (W, H)), (W, H))                # whole silhouette = spec lines
    # top surface: same far edge, near edge raised by the thickness, side edges kept on the same slant lines
    def side_x(x_far, x_near, y):
        return x_far + (x_near - x_far) * (y - fy * H) / (ny * H - fy * H)
    yt = ny * H - t
    pts_top = [pts[0], pts[1], (side_x(pts[1][0], pts[2][0], yt), yt), (side_x(pts[0][0], pts[3][0], yt), yt)]
    top_only = np.minimum(down(rounded_mask(pts_top, r, (W, H)), (W, H)), sil)
    front = np.clip(sil - top_only, 0, 1)                           # thickness band along the near edge
    line = down(stroke_mask(pts_top, sp["border_inset"], sp["border_w"], (W, H)), (W, H))
    line = np.minimum(line, top_only)
    rgb = np.zeros((H, W, 3), float); alpha = np.zeros((H, W), float)
    def lay(mask, col):
        nonlocal rgb, alpha
        col = np.array(hex2rgb(col), float)
        rgb = rgb * (1 - mask[..., None]) + col * mask[..., None]
        alpha = np.maximum(alpha, mask)
    lay(front, c["front"]); lay(top_only, c["top"]); lay(line, c["line"])
    return rgb, alpha, (W, H)

def save(name, rgb, alpha, size, out, room=None):
    W, H = size
    # transparent version: antialiased alpha, colours un-premultiplied
    a8 = np.clip(alpha * 255 + 0.5, 0, 255).astype(np.uint8)
    base = np.zeros((H, W, 3), float)
    nz = alpha > 1e-3
    # rgb was composited over black; recover the straight colour
    base[nz] = rgb[nz] / np.maximum(alpha[nz][:, None], 1e-3)
    rgba = np.dstack([np.clip(base + 0.5, 0, 255).astype(np.uint8), a8])
    rgba[~nz] = (0, 0, 0, 0)
    Image.fromarray(rgba, "RGBA").save(os.path.join(out, name + "-transparent.png"))
    # magenta version: crisp edges (no blend with magenta)
    hard = alpha >= 0.5
    mg = np.zeros((H, W, 3), np.uint8); mg[:] = (255, 0, 255)
    mg[hard] = np.clip(base[hard] + 0.5, 0, 255).astype(np.uint8)
    Image.fromarray(mg, "RGB").save(os.path.join(out, name + ".png"))
    if room is not None:
        rm = Image.open(room).convert("RGB")
        if rm.size != (W, H): rm = rm.resize((W, H), Image.LANCZOS)
        Image.alpha_composite(rm.convert("RGBA"), Image.fromarray(rgba, "RGBA")).convert("RGB").save(
            os.path.join(out, name + "-preview.png"))

if __name__ == "__main__":
    out = sys.argv[1]; os.makedirs(out, exist_ok=True)
    rooms = {"tall": sys.argv[2] if len(sys.argv) > 2 else None, "wide": sys.argv[3] if len(sys.argv) > 3 else None}
    for name, kind, colour in JOBS:
        rgb, alpha, size = build(kind, colour)
        save(name, rgb, alpha, size, out, rooms[kind])
        print("wrote", name)
