"""Draw the exercise-mat overlays in code to the exact spec in stage.toml (ChatGPT could not hit the numbers)."""
import os
import numpy as np
from PIL import Image, ImageDraw
import sheetlib as S

SS = 4  # supersampling


def _inset(pts, d):
    n = len(pts); lines = []
    for i in range(n):
        a, b = np.array(pts[i], float), np.array(pts[(i + 1) % n], float)
        e = (b - a) / np.linalg.norm(b - a)
        lines.append((a + np.array([-e[1], e[0]]) * d, e))
    out = []
    for i in range(n):
        (p1, d1), (p2, d2) = lines[i - 1], lines[i]
        t = np.linalg.solve(np.array([[d1[0], -d2[0]], [d1[1], -d2[1]]], float), np.array([p2[0] - p1[0], p2[1] - p1[1]], float))
        out.append((p1[0] + t[0] * d1[0], p1[1] + t[0] * d1[1]))
    return out


def _rounded(pts, r, size):
    W, H = size
    inner = _inset(pts, r)
    m = Image.new("L", (W * SS, H * SS), 0); dr = ImageDraw.Draw(m)
    s = lambda p: (p[0] * SS, p[1] * SS)
    dr.polygon([s(p) for p in inner], fill=255)
    for i in range(len(inner)):
        dr.line([s(inner[i]), s(inner[(i + 1) % len(inner)])], fill=255, width=int(round(2 * r * SS)))
        x, y = s(inner[i]); R = r * SS
        dr.ellipse([x - R, y - R, x + R, y + R], fill=255)
    return m


def _stroke(pts, d, width, size):
    W, H = size
    inner = _inset(pts, d)
    m = Image.new("L", (W * SS, H * SS), 0); dr = ImageDraw.Draw(m)
    for i in range(len(inner)):
        a = (inner[i][0] * SS, inner[i][1] * SS); b = (inner[(i + 1) % len(inner)][0] * SS, inner[(i + 1) % len(inner)][1] * SS)
        dr.line([a, b], fill=255, width=int(round(width * SS)))
        R = width * SS / 2
        dr.ellipse([a[0] - R, a[1] - R, a[0] + R, a[1] + R], fill=255)
    return m


def _down(m, size):
    return np.array(m.resize(size, Image.LANCZOS)).astype(float) / 255.0


def build(stage, fmt, colour):
    sp = stage["mat"][fmt]
    W, H = stage["format"][fmt]["size"]
    c = next(x for x in stage["mat_colour"] if x["name"] == colour)
    ny, nx0, nx1 = sp["near"]; fy, fx0, fx1 = sp["far"]
    r, t = sp["radius_px"], sp["thick_px"]
    pts = [(fx0 * W, fy * H), (fx1 * W, fy * H), (nx1 * W, ny * H), (nx0 * W, ny * H)]
    for _ in range(3):   # rounding trims the widest point; widen the near vertices until the silhouette hits the spec
        sil = _down(_rounded(pts, r, (W, H)), (W, H))
        xs = np.where((sil >= 0.5).any(0))[0]
        pts[3] = (pts[3][0] - (xs.min() - nx0 * W), pts[3][1])
        pts[2] = (pts[2][0] + (nx1 * W - 1 - xs.max()), pts[2][1])
    sil = _down(_rounded(pts, r, (W, H)), (W, H))
    yt = ny * H - t
    sx = lambda xf, xn, y: xf + (xn - xf) * (y - fy * H) / (ny * H - fy * H)
    pt = [pts[0], pts[1], (sx(pts[1][0], pts[2][0], yt), yt), (sx(pts[0][0], pts[3][0], yt), yt)]
    top = np.minimum(_down(_rounded(pt, r, (W, H)), (W, H)), sil)
    front = np.clip(sil - top, 0, 1)
    line = np.minimum(_down(_stroke(pt, sp["border_inset_px"], sp["border_px"], (W, H)), (W, H)), top)
    rgb = np.zeros((H, W, 3)); alpha = np.zeros((H, W))
    for mask, col in ((front, c["front"]), (top, c["top"]), (line, c["line"])):
        col = np.array(S.hex2rgb(col), float)
        rgb = rgb * (1 - mask[..., None]) + col * mask[..., None]
        alpha = np.maximum(alpha, mask)
    return rgb, alpha, (W, H)


def save(name, rgb, alpha, size, out, room=None, magenta="#FF00FF"):
    W, H = size
    nz = alpha > 1e-3
    base = np.zeros((H, W, 3)); base[nz] = rgb[nz] / np.maximum(alpha[nz][:, None], 1e-3)
    rgba = np.dstack([np.clip(base + .5, 0, 255).astype(np.uint8), np.clip(alpha * 255 + .5, 0, 255).astype(np.uint8)])
    rgba[~nz] = 0
    Image.fromarray(rgba, "RGBA").save(os.path.join(out, name + "-transparent.png"))
    hard = alpha >= .5
    mg = np.zeros((H, W, 3), np.uint8); mg[:] = S.hex2rgb(magenta)
    mg[hard] = np.clip(base[hard] + .5, 0, 255).astype(np.uint8)
    Image.fromarray(mg, "RGB").save(os.path.join(out, name + ".png"))
    if room:
        rm = Image.open(room).convert("RGB")
        if rm.size != (W, H):
            rm = rm.resize((W, H), Image.LANCZOS)
        Image.alpha_composite(rm.convert("RGBA"), Image.fromarray(rgba, "RGBA")).convert("RGB").save(os.path.join(out, name + "-preview.png"))


def draw_all(out, rooms=None, prefix="mat"):
    stage = S.load_stage()
    os.makedirs(out, exist_ok=True)
    rooms = rooms or {}
    made = []
    for fmt in stage["mat"]:
        for c in stage["mat_colour"]:
            name = f"{prefix}-{fmt}-{c['name']}"
            rgb, alpha, size = build(stage, fmt, c["name"])
            save(name, rgb, alpha, size, out, rooms.get(fmt), stage["magenta"])
            made.append(name)
    return made
