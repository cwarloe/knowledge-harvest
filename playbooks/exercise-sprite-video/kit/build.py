#!/usr/bin/env python3
"""Build a 5BX workout video from generated sprite-boy strips.

    python3 kit/build.py --data path/to/5bx-charts.json --chart 1 --level "A+" --out chart1.mp4

Everything that is likely to change lives in config/, not here:
    config/theme.json      look and wording: colours, backdrop, HUD, formats, fade, recolour
    config/strips.json     which image is which exercise; which strip each chart slot uses
    config/character.json  the boy in words (used by kit/prompt.py to make new strips)
    sheets/                the strips themselves

Useful flags
    --preview          5 s per exercise, 2 s breaks (a quick look; the whole video in about a minute)
    --only ex3,run     render just those slots, no breaks (review one exercise in seconds)
    --no-fade          pure hold-and-cut instead of a short crossfade
    --theme FILE       try another look without editing the default
    --format portrait  1080x1920
    --list             show what each chart slot uses, and what is missing

Timing is never typed here. Every rep count, step count, break and jump window is read from the
data file, so the video cannot disagree with the plan.
"""
import argparse, hashlib, json, math, os, random, shutil, subprocess, sys
import numpy as np
from PIL import Image, ImageDraw

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
ASSETS = os.path.join(ROOT, "assets")          # layers as real files: sprites, backdrops, props (committed)
BAKE_VERSION = "4"                              # bump when the cut-out or backdrop drawing changes
sys.path.insert(0, HERE)
from keyer import key as chroma_key
from recolor import recolor, REGIONS

SLOTS = ["ex1", "ex2", "ex3", "ex4"]


def jload(p): return json.load(open(p))
def sha(*parts):
    h = hashlib.sha1()
    for p in parts: h.update(p if isinstance(p, bytes) else str(p).encode())
    return h.hexdigest()[:12]
def filehash(p): return sha(open(p, "rb").read())
def rgb(hexstr): return tuple(int(hexstr.lstrip("#")[i:i + 2], 16) for i in (0, 2, 4))

CODE_VERSION = sha(open(__file__, "rb").read(), open(os.path.join(HERE, "keyer.py"), "rb").read(),
                   open(os.path.join(HERE, "recolor.py"), "rb").read())   # editing code never serves a stale cache


# ---------- backdrop: several layers, each its own file ----------
def draw_forest(b, F):
    """Return ordered {layer name: RGBA image}. Same drawing order as before so the look is unchanged."""
    W, H = F["W"], F["H"]; gy = int(H * F["ground"]); S = 2; rnd = random.Random(b.get("seed", 7))
    def canvas(fill=(0, 0, 0, 0)): im = Image.new("RGBA", (W * S, H * S), fill); return im, ImageDraw.Draw(im)
    out = {}
    im, d = canvas((0, 0, 0, 255)); top, bot = rgb(b["sky_top"]), rgb(b["sky_bottom"])
    for y in range(gy * S):
        t = y / (gy * S); d.line([(0, y), (W * S, y)], fill=tuple(int(top[i] + (bot[i] - top[i]) * t) for i in range(3)) + (255,))
    out["sky"] = im
    im, d = canvas()
    for _ in range(7):
        cx, cy, s_ = rnd.randint(0, W) * S, rnd.randint(int(H * .06), int(H * .30)) * S, rnd.randint(60, 120) * S
        for dx, dy, r in ((0, 0, 1), (.8, .2, .8), (-.8, .25, .75), (.3, -.25, .7)):
            d.ellipse([cx + dx * s_ - r * s_, cy + dy * s_ - r * s_ * .55, cx + dx * s_ + r * s_, cy + dy * s_ + r * s_ * .55], fill=(255, 255, 255, 255))
    out["clouds"] = im
    for name, (base, amp, col, seed) in {"mountains-far": (int(H * .55), int(H * .10), rgb(b["mountains"][0]), 1),
                                         "mountains-near": (int(H * .62), int(H * .08), rgb(b["mountains"][1]), 2)}.items():
        im, d = canvas(); r = random.Random(seed); pts = [(0, gy * S)]
        for x in range(0, W * S + 80 * S, 80 * S): pts.append((x, (base - r.randint(0, amp)) * S))
        pts.append((W * S, gy * S)); d.polygon(pts, fill=col + (255,)); out[name] = im
    def pine(d, x, base, h, col):
        w = h * .42; d.rectangle([x - w * .06, base - h * .12, x + w * .06, base], fill=(86, 60, 40, 255))
        for k in range(3):
            y0 = base - h * (.12 + .27 * k); y1 = y0 - h * .42; ww = w * (1 - .24 * k)
            d.polygon([(x - ww / 2, y0), (x + ww / 2, y0), (x, y1)], fill=col + (255,))
    for row, (name, col, hmin, hmax, step) in enumerate([("trees-back", rgb(b["trees"][0]), .13, .19, 70), ("trees-front", rgb(b["trees"][1]), .17, .26, 110)]):
        im, d = canvas(); x = -20 * S
        while x < W * S + 60 * S:
            pine(d, x, (gy - 6 + row * 14) * S, rnd.randint(int(H * hmin), int(H * hmax)) * S, col); x += int(rnd.uniform(.7, 1.3) * step * S)
        out[name] = im
    im, d = canvas()
    d.rectangle([0, gy * S, W * S, H * S], fill=rgb(b["ground"]) + (255,)); d.rectangle([0, gy * S, W * S, (gy + 10) * S], fill=rgb(b["ground_line"]) + (255,))
    for _ in range(60):
        px, py = rnd.randint(0, W) * S, rnd.randint(gy + 20, H - 10) * S
        d.ellipse([px, py, px + rnd.randint(6, 16) * S, py + rnd.randint(3, 7) * S], fill=rgb(b["pebbles"]) + (255,))
    out["ground"] = im
    return {k: v.resize((W, H), Image.LANCZOS) for k, v in out.items()}


def backdrop_layers(theme, F, fmt):
    """Ordered [(name, RGBA)]. Cached on disk as assets/backdrops/<id>/<format>/NN-<name>.png (one file per layer)."""
    b = theme["backdrop"]; bid = b.get("id", "forest"); d = os.path.join(ASSETS, "backdrops", bid, fmt); mp = os.path.join(d, "manifest.json")
    want = sha(json.dumps({k: v for k, v in b.items() if k != "overrides"}, sort_keys=True), F["W"], F["H"], F["ground"], BAKE_VERSION)
    if os.path.exists(mp) and (jload(mp).get("source") == "images" or jload(mp).get("hash") == want):          # imported images are used as they are
        layers = [(n, Image.open(os.path.join(d, f)).convert("RGBA")) for n, f in jload(mp)["layers"]]
    else:
        os.makedirs(d, exist_ok=True)
        for f in os.listdir(d):
            if f.endswith(".png"): os.remove(os.path.join(d, f))
        if b.get("style") == "image" and b.get("image"):
            im = Image.open(os.path.join(ROOT, b["image"])).convert("RGB"); sc = max(F["W"] / im.width, F["H"] / im.height)
            im = im.resize((round(im.width * sc), round(im.height * sc)), Image.LANCZOS)
            drawn = {"picture": im.crop(((im.width - F["W"]) // 2, (im.height - F["H"]) // 2, (im.width - F["W"]) // 2 + F["W"], (im.height - F["H"]) // 2 + F["H"])).convert("RGBA")}
        else: drawn = draw_forest(b, F)
        names = []
        for i, (n, im) in enumerate(drawn.items()):
            fn = f"{i:02d}-{n}.png"; im.save(os.path.join(d, fn)); names.append([n, fn])
        json.dump({"hash": want, "layers": names, "size": [F["W"], F["H"]]}, open(mp, "w"), indent=1)
        layers = [(n, Image.open(os.path.join(d, f)).convert("RGBA")) for n, f in names]
    out = []
    for n, im in layers:                       # any layer can be swapped for your own file, without touching code
        ov = (b.get("overrides") or {}).get(n)
        if ov:
            o = Image.open(os.path.join(ROOT, ov)).convert("RGBA")
            if o.size != (F["W"], F["H"]): o = o.resize((F["W"], F["H"]), Image.LANCZOS)
            im = o
        out.append((n, im))
    return out


def flatten(layers, size):
    base = Image.new("RGBA", size, (0, 0, 0, 255))
    for _, im in layers: base.alpha_composite(im)
    return base


# ---------- the boy: baked once into assets/sprites/<strip>/ (one transparent file per pose) ----------
def components(mask, ds=4, dil=1):
    """Label connected shapes on a downsampled, lightly dilated mask."""
    h, w = mask.shape; H, W = h // ds, w // ds
    small = mask[:H * ds, :W * ds].reshape(H, ds, W, ds).max(axis=(1, 3)); d = small.copy()
    for _ in range(dil):
        n = d.copy(); n[1:] |= d[:-1]; n[:-1] |= d[1:]; n[:, 1:] |= d[:, :-1]; n[:, :-1] |= d[:, 1:]; d = n
    lab = np.zeros(d.shape, np.int32); k = 0
    for y, x in zip(*np.nonzero(d)):
        if lab[y, x]: continue
        k += 1; lab[y, x] = k; stack = [(y, x)]
        while stack:
            cy, cx = stack.pop()
            for ny, nx in ((cy + 1, cx), (cy - 1, cx), (cy, cx + 1), (cy, cx - 1)):
                if 0 <= ny < H and 0 <= nx < W and d[ny, nx] and not lab[ny, nx]: lab[ny, nx] = k; stack.append((ny, nx))
    return lab, ds


def split_rgba(rgba, n, label):
    """Cut-out strip -> n poses, left to right. Split by connected shape: neighbours overlap in x."""
    a = np.array(rgba); lab, ds = components(a[..., 3] > 128)
    ids = list(range(1, lab.max() + 1)); area = {i: int((lab == i).sum()) for i in ids}
    big = sorted([i for i in ids if area[i] > 400], key=lambda i: -area[i])[:n]
    if len(big) != n: raise SystemExit(f"{label}: expected {n} poses, found {len(big)}. Check 'poses' in config/strips.json or regenerate the strip.")
    cent = {i: np.argwhere(lab == i).mean(axis=0) for i in ids}
    for i in ids:                                         # fold stray fragments into the nearest pose
        if i not in big and area[i] > 6:
            j = min(big, key=lambda b: np.hypot(*(cent[b] - cent[i]))); lab[lab == i] = j
    big.sort(key=lambda i: np.argwhere(lab == i)[:, 1].mean())
    up = np.kron(lab, np.ones((ds, ds), np.int32)); full = np.zeros(a.shape[:2], np.int32); full[:up.shape[0], :up.shape[1]] = up
    poses = []
    for i in big:
        b = a.copy(); b[..., 3] = np.where(full == i, b[..., 3], 0); ys, xs = np.nonzero(b[..., 3] > 16)
        poses.append((Image.fromarray(b[ys.min():ys.max() + 1, xs.min():xs.max() + 1], "RGBA"), (int(xs.min()), int(ys.min()))))
    return poses


def row_bounds(rgba, n_rows, label="sheet"):
    """A sheet may hold several exercises, one per row. Rows are separated by empty horizontal bands; cut in the middle of the widest ones."""
    a = np.array(rgba)[..., 3] > 128; occ = a.any(axis=1); bands, start = [], None
    for y, o in enumerate(list(occ) + [True]):
        if not o and start is None: start = y
        if o and start is not None: bands.append((start, y)); start = None
    inner = [(b0, b1) for b0, b1 in bands if b0 > 0 and b1 < a.shape[0]]
    if len(inner) < n_rows - 1:
        raise SystemExit(f"{label}: expected {n_rows} rows separated by empty space, found {len(inner) + 1}. Regenerate with more space between the rows.")
    cuts = sorted((b0 + b1) // 2 for b0, b1 in sorted(inner, key=lambda b: -(b[1] - b[0]))[:n_rows - 1])
    edges = [0] + cuts + [a.shape[0]]
    return [(edges[i], edges[i + 1]) for i in range(n_rows)]


def shoe_mask(arr):
    """His shoes: blue pixels that sit beside a white sock, sole or lace. Blue alone also catches the tank on some strips; white alone catches nothing useful."""
    a = arr.astype(int); r, g, b = a[..., 0], a[..., 1], a[..., 2]; hsv = np.array(Image.fromarray(arr[..., :3]).convert("HSV")).astype(float)
    hh, ss, vv = hsv[..., 0] * 360 / 255, hsv[..., 1] / 255, hsv[..., 2] / 255; sr = REGIONS["shoes"]
    blue = (a[..., 3] > 200) & (((hh >= sr["h"][0]) & (hh <= sr["h"][1]) & (ss >= sr["smin"]) & (vv >= sr["vmin"])) | ((b - g >= 70) & (b - r >= 90)))
    white = (a[..., 3] > 200) & (np.minimum(np.minimum(r, g), b) > 205) & (np.max(a[..., :3], axis=2) - np.min(a[..., :3], axis=2) < 30)
    near = white.copy()
    for _ in range(12): n = near.copy(); n[1:] |= near[:-1]; n[:-1] |= near[1:]; n[:, 1:] |= near[:, :-1]; n[:, :-1] |= near[:, 1:]; near = n
    m = blue & near
    lab, ds = components(m, ds=2, dil=1)                                 # keep whole shoe shapes, drop specks
    if lab.max() == 0: return m
    area = np.bincount(lab.ravel())[1:]; keep = np.isin(lab, [i + 1 for i, v in enumerate(area) if v >= 0.2 * area.max()])
    full = np.zeros(m.shape, bool); up = np.kron(keep, np.ones((ds, ds), bool)); full[:up.shape[0], :up.shape[1]] = up
    return m & full


def anchors_of(p):
    """Every anchor a pose can be pinned by, in the pose's own pixel coordinates.
    hips = the red shorts: the part of the body that stays put when he lies on the floor (back extension, sit-up)."""
    arr = np.array(p); a = arr[..., 3] > 128; h, w = a.shape
    head = np.nonzero(a[:max(6, int(h * .12))].any(axis=0))[0]; feet = np.nonzero(a[-14:].any(axis=0))[0]
    red = (arr[..., 3] > 200) & (arr[..., 0] > 150) & (arr[..., 1] < 90) & (arr[..., 2] < 90)
    hips = float(np.nonzero(red)[1].mean()) if red.sum() >= 50 else float(feet.mean())
    shoe = shoe_mask(arr)
    sx = np.nonzero(shoe)[1] if shoe.sum() >= 30 else None            # where his shoes are: the thing that stays planted
    shoes = float(sx.mean()) if sx is not None else float(feet.mean())
    return {"head": float(head.mean()), "span-left": float(feet.min()), "span-right": float(feet.max()), "span-center": float(feet.mean()), "hips": hips, "shoes": shoes,
            "shoe-left": float(sx.min()) if sx is not None else float(feet.min()), "shoe-right": float(sx.max()) if sx is not None else float(feet.max())}


def bake(name, strip, theme):
    """sheets/<file> -> assets/sprites/<name>/p1..pN.png + meta.json. Re-bakes only if the strip or the key changed."""
    src = os.path.join(ROOT, "sheets", strip["file"]); h = filehash(src); d = os.path.join(ASSETS, "sprites", name); mp = os.path.join(d, "meta.json")
    if os.path.exists(mp):
        m = jload(mp)
        if (m.get("source_hash") == h and m.get("key") == theme["key"] and m.get("n") == strip["poses"] and m.get("version") == BAKE_VERSION
                and m.get("rows") == strip.get("rows") and m.get("row") == strip.get("row") and m.get("erase") == strip.get("erase")): return m
    os.makedirs(d, exist_ok=True)
    for f in os.listdir(d):
        if f.endswith(".png"): os.remove(os.path.join(d, f))
    rgba = chroma_key(Image.open(src), **theme["key"])                       # neutral colours: recolour happens at build time
    if strip.get("erase"):                                                   # a stray speck the generator left: "erase": [[x0, y0, x1, y1]] in sheet pixels, cleared before the poses are split
        arr = np.array(rgba)
        for x0, y0, x1, y1 in strip["erase"]: arr[y0:y1, x0:x1, 3] = 0
        rgba = Image.fromarray(arr, "RGBA")
    if strip.get("rows"):                                                    # several exercises on one sheet: take this strip's row
        y0, y1 = row_bounds(rgba, strip["rows"], src)[strip["row"]]; rgba = rgba.crop((0, y0, rgba.width, y1))
    poses = split_rgba(rgba, strip["poses"], src)
    meta = {"version": BAKE_VERSION, "source": strip["file"], "source_hash": h, "key": theme["key"], "n": strip["poses"], "rows": strip.get("rows"), "row": strip.get("row"), "erase": strip.get("erase"), "poses": []}
    for k, (p, off) in enumerate(poses, 1):
        p.save(os.path.join(d, f"p{k}.png")); meta["poses"].append({"file": f"p{k}.png", "offset": list(off), "size": list(p.size), "anchors": anchors_of(p)})
    meta["floor"] = max(o[1] + p.size[1] for p, o in poses); meta["top"] = min(o[1] for p, o in poses)
    json.dump(meta, open(mp, "w"), indent=1); return meta


def pose_anchor(strip, k, meta_pose):
    """The x (in strip pixels) that pose k is pinned by. strips.json can override the anchor for one pose ("anchor_pose": {"4": "shoe-right"}, for a pose
    where the usual shoe is hidden behind a hand) and nudge a pose sideways ("nudge": {"4": [dx, dy]}: strip pixels, +x right, +y down)."""
    how = (strip.get("anchor_pose") or {}).get(str(k), strip["anchor"]); dx = (strip.get("nudge") or {}).get(str(k), (0, 0))[0]
    return meta_pose["anchors"][how] - dx


def pose_xy(strip, k, meta_pose, X0, gy, floor, s):
    """Where pose k's top-left corner goes in the frame: its anchor at X0, standing on the strip's floor line, plus the vertical nudge."""
    dy = (strip.get("nudge") or {}).get(str(k), (0, 0))[1]
    return X0 - pose_anchor(strip, k, meta_pose) * s, gy + 10 - (floor - meta_pose["offset"][1]) * s + dy * s


def fit_of(strip, fmt):
    """strips.json "fit": a number, or {"landscape": 0.72, "portrait": 1.0}. Smaller than 1 shrinks the exercise inside the stage box."""
    f = strip.get("fit", 1.0); return f.get(fmt, 1.0) if isinstance(f, dict) else f


def extents(strip, meta):
    """The figure's width either side of its anchor (L, R) and its height, in sprite pixels, over all poses including flipped ones."""
    anchors = [pose_anchor(strip, k, m) for k, m in enumerate(meta["poses"], 1)]; mir = [(meta["poses"][k - 1]["size"][0], mirror_anchor(strip, k, meta["poses"][k - 1])) for k in strip.get("mirror", [])]
    return max(anchors + [a for _, a in mir]), max([m["size"][0] - a for m, a in zip(meta["poses"], anchors)] + [w - a for w, a in mir]), meta["floor"] - meta["top"]


def hud_block(theme, F, texts):
    """Size of the title block (kicker, title, reps) in frame pixels, measured with the real font. Returns (width, bottom edge)."""
    from PIL import ImageFont
    font = theme["hud"]["font"]; font = font if os.path.isabs(font) else os.path.join(ROOT, font); kick, title, target = texts; y0 = int(F["H"] * .02)
    w = max(ImageFont.truetype(font, F[k]).getlength(txt) for k, txt in (("kicker", kick), ("title", title.upper()), ("target", target)))
    return w + 2 * theme["hud"]["outline_width"], y0 + F["kicker"] + F["title"] + 22 + F["target"] * 1.25


def stage_plan(strip, meta, theme, F, fmt, texts):
    """Where the title goes and how tall the figure may be. "auto": the title block sits top-left or top-right, whichever leaves the figure more room; a standing
    figure that the block does not reach may use the whole free height; a lying figure is wide, not tall, so it keeps the normal box. "center": the old layout."""
    h = F.get("hud") or {}; layout = h.get("layout", "center"); base_h = F["box"][1]
    if layout == "center": return {"side": "center", "clock": "center", "box_h": base_h}
    sides = ["left", "right"] if layout == "auto" else [layout]; bw = F["box"][0]; fit = fit_of(strip, fmt); L, R, height = extents(strip, meta); floor_y = int(F["H"] * F["ground"]) + 10
    margin, gap, free_h = h.get("margin", 40), h.get("gap", 26), h.get("free_h", base_h); bwid, bbot = hud_block(theme, F, texts); lying = (L + R) > 1.2 * height; best = None
    for side in sides:
        box_h = base_h if lying else free_h
        for _ in range(3):                                       # the figure's width depends on its size, so settle in a few passes
            s = fit * min(bw / (L + R), box_h / height); x0 = F["W"] / 2 + (L - R) * s / 2 - L * s; x1 = x0 + (L + R) * s; top = floor_y - height * s
            bx0, bx1 = (margin, margin + bwid) if side == "left" else (F["W"] - margin - bwid, F["W"] - margin)
            reaches = bx1 > x0 - gap and bx0 < x1 + gap and bbot + gap > top
            if not reaches: break
            box_h = max(base_h * 0.5, floor_y - (bbot + gap) / 1.0) if not lying else base_h
            if lying: break
        if best is None or box_h > best["box_h"] + 1: best = {"side": side, "box_h": round(box_h)}
    best["clock"] = h.get("clock", "opposite"); return best


def cycle_pose(c):
    """A cycle entry is a pose number, or "5m": pose 5 flipped left to right (the lean to the other side of a circle bend)."""
    return int(str(c).rstrip("m")), str(c).endswith("m")


_SWAP = {"shoe-left": "shoe-right", "shoe-right": "shoe-left", "span-left": "span-right", "span-right": "span-left"}


def mirror_anchor(strip, k, meta_pose):
    """Where pose k's anchor falls once the picture is flipped left to right: the left/right anchors swap sides and every x becomes width - x."""
    how = (strip.get("anchor_pose") or {}).get(str(k), strip["anchor"]); dx = (strip.get("nudge") or {}).get(str(k), (0, 0))[0]
    return meta_pose["size"][0] - meta_pose["anchors"][_SWAP.get(how, how)] + dx


def load_sprites(name, strip, theme):
    meta = bake(name, strip, theme); d = os.path.join(ASSETS, "sprites", name)
    return [recolor(Image.open(os.path.join(d, m["file"])).convert("RGBA"), theme.get("recolor")) for m in meta["poses"]], meta


# ---------- props: anything between the backdrop and the boy, or in front of him ----------
def prop_applies(prop, slot):
    return prop.get("enabled", True) and (prop.get("slots", "*") == "*" or slot in prop["slots"])


def render_props(scene, slot, geom, F, z):
    """RGBA frame-sized layer of every enabled prop for this slot and depth (z = 'behind' | 'front'), or None."""
    props = [p for p in scene.get("props", []) if prop_applies(p, slot) and p.get("z", "behind") == z]
    if not props: return None
    W, H, gy, k = F["W"], F["H"], geom["gy"], F["H"] / 1080.0
    layer = Image.new("RGBA", (W, H), (0, 0, 0, 0)); floor_y = gy + 10
    ux0, ux1 = geom["X0"] - geom["L"] * geom["s"], geom["X0"] + geom["R"] * geom["s"]; cx, uw = (ux0 + ux1) / 2, ux1 - ux0
    for p in props:
        kind = p["kind"]
        if kind == "mat":
            w = uw * (1 + 2 * p.get("pad", .12)); t = p.get("thickness", 18) * k; x0 = cx - w / 2
            d = ImageDraw.Draw(layer); r = max(2, int(t / 2))
            d.rounded_rectangle([x0, floor_y, x0 + w, floor_y + t], radius=r, fill=rgb(p["edge"]) + (255,))
            d.rounded_rectangle([x0, floor_y, x0 + w, floor_y + t * .62], radius=r, fill=rgb(p["color"]) + (255,))
        elif kind == "shadow":
            from PIL import ImageFilter
            sh = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(sh); hh = p.get("height", 26) * k
            d.ellipse([cx - uw * p.get("width", .95) / 2, floor_y - hh * .35, cx + uw * p.get("width", .95) / 2, floor_y + hh * .65],
                      fill=(0, 0, 0, int(255 * p.get("opacity", .28))))
            layer.alpha_composite(sh.filter(ImageFilter.GaussianBlur(p.get("blur", 10) * k)))
        elif kind == "image":
            im = Image.open(os.path.join(ROOT, p["file"])).convert("RGBA"); w = max(1, round(W * p.get("scale", .1))); h = max(1, round(im.height * w / im.width))
            im = im.resize((w, h), Image.LANCZOS); layer.alpha_composite(im, (round(p.get("x", .5) * W - w / 2), round(floor_y - h + p.get("lift", 0) * k)))
        elif kind == "overlay":                                    # a full-frame picture (a floor mat in perspective, light beams, a foreground fringe); magenta becomes see-through
            im = chroma_key(Image.open(os.path.join(ROOT, p["file"]))).convert("RGBA")
            if im.size != (W, H): im = im.resize((W, H), Image.LANCZOS)
            if p.get("opacity", 1) < 1: im.putalpha(im.getchannel("A").point(lambda v: int(v * p["opacity"])))
            layer.alpha_composite(im)
        else: raise SystemExit(f"unknown prop kind '{kind}' (mat | shadow | image | overlay)")
    return layer


def compose(name, strip, theme, scene, F, fmt, work, slot, plan=None):
    """Per pose: layer_pN.png (boy alone), plus backdrop.png, props_*.png and the finished pN.png. Cached."""
    meta = bake(name, strip, theme); blayers = backdrop_layers(theme, F, fmt)
    tag = sha(meta["source_hash"], json.dumps(strip, sort_keys=True), json.dumps(theme["key"]), json.dumps(theme.get("recolor")), json.dumps(scene, sort_keys=True),
              json.dumps(theme["backdrop"], sort_keys=True), json.dumps(F, sort_keys=True), slot, json.dumps(plan or {}, sort_keys=True), CODE_VERSION)
    out = os.path.join(work, "frames", f"{slot}-{name}-{fmt}-{tag}")
    if os.path.exists(os.path.join(out, "DONE")): return out
    os.makedirs(out, exist_ok=True)
    poses, meta = load_sprites(name, strip, theme)
    floor, top = meta["floor"], meta["top"]; anchors = [pose_anchor(strip, k, m) for k, m in enumerate(meta["poses"], 1)]
    mir = [(k, meta["poses"][k - 1]["size"][0], mirror_anchor(strip, k, meta["poses"][k - 1])) for k in strip.get("mirror", [])]      # flipped copies of some poses
    L = max(anchors + [a for _, _, a in mir]); R = max([p.size[0] - a for p, a in zip(poses, anchors)] + [w - a for _, w, a in mir])
    bw, bh = F["box"]; bh = (plan or {}).get("box_h", bh); fit = fit_of(strip, fmt); s = fit * min(bw / (L + R), bh / (floor - top));      # "fit" < 1 shrinks this exercise inside the stage box (lying exercises fill the width and look huge next to standing ones)
    gy = int(F["H"] * F["ground"]); X0 = F["W"] / 2 + (L - R) * s / 2
    geom = dict(gy=gy, X0=X0, s=s, L=L, R=R)
    bg = flatten(blayers, (F["W"], F["H"])); bg.save(os.path.join(out, "backdrop.png"))
    behind, front = render_props(scene, slot, geom, F, "behind"), render_props(scene, slot, geom, F, "front")
    if behind: behind.save(os.path.join(out, "props_behind.png"))
    if front: front.save(os.path.join(out, "props_front.png"))
    for k, (p, m, ax) in enumerate(zip(poses, meta["poses"], anchors), 1):
        w, h = max(1, round(p.size[0] * s)), max(1, round(p.size[1] * s))
        layer = Image.new("RGBA", (F["W"], F["H"]), (0, 0, 0, 0))
        px, py = pose_xy(strip, k, m, X0, gy, floor, s)
        layer.alpha_composite(p.resize((w, h), Image.LANCZOS), (round(px), round(py)))
        layer.save(os.path.join(out, f"layer_p{k}.png"))
        f = bg.copy()
        if behind: f.alpha_composite(behind)
        f.alpha_composite(layer)
        if front: f.alpha_composite(front)
        f.convert("RGB").save(os.path.join(out, f"p{k}.png"))
    for k, w0, ax in mir:                                          # the flipped copies: layer_pKm.png and the finished pKm.png
        p, m = poses[k - 1], meta["poses"][k - 1]; fl = p.transpose(Image.FLIP_LEFT_RIGHT); w, h = max(1, round(fl.size[0] * s)), max(1, round(fl.size[1] * s))
        dy = (strip.get("nudge") or {}).get(str(k), (0, 0))[1]; py = gy + 10 - (floor - m["offset"][1]) * s + dy * s
        layer = Image.new("RGBA", (F["W"], F["H"]), (0, 0, 0, 0)); layer.alpha_composite(fl.resize((w, h), Image.LANCZOS), (round(X0 - ax * s), round(py))); layer.save(os.path.join(out, f"layer_p{k}m.png"))
        f = bg.copy()
        if behind: f.alpha_composite(behind)
        f.alpha_composite(layer)
        if front: f.alpha_composite(front)
        f.convert("RGB").save(os.path.join(out, f"p{k}m.png"))
    json.dump({"geom": {"gy": gy, "X0": X0, "scale": s, "L": L, "R": R}, "poses": strip["poses"]}, open(os.path.join(out, "geom.json"), "w"))
    open(os.path.join(out, "DONE"), "w").write("ok"); return out


# ---------- video ----------
def run(cmd):
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode: raise SystemExit(f'ffmpeg failed:\n{" ".join(cmd[:14])}...\n{r.stderr[-1500:]}')

def esc(t): return t.replace("\\", "\\\\").replace(":", r"\:").replace("'", r"\\\'")


class Hud:
    def __init__(self, theme, F):
        self.t, self.F, self.s = theme, F, theme["strings"]
        self.h = {k: (os.path.join(ROOT, v) if k in ("font", "mono") and not os.path.isabs(v) else v) for k, v in theme["hud"].items()}      # fonts ship in assets/fonts
        self.bord = f"borderw={self.h['outline_width']}:bordercolor={self.h['outline']}"

    def xexpr(self, align):
        m = (self.F.get("hud") or {}).get("margin", 40)
        return {"left": str(m), "right": f"w-tw-{m}"}.get(align, "(w-tw)/2")

    def text(self, font, txt, color, size, y, mono=False, align="center"):
        return (f"drawtext=fontfile={self.h['mono'] if mono else self.h['font']}:text='{esc(txt)}':fontcolor={color}:{self.bord}:"
                f"fontsize={size}:x={self.xexpr(align)}:y={y}")

    def exercise(self, kicker, title, target, allot, off=0.0, plan=None):
        F, h = self.F, self.h; W, H = F["W"], F["H"]; gy = int(H * F["ground"]); cy = gy + int((H - gy) * .22)
        side = (plan or {}).get("side", "center"); copt = (plan or {}).get("clock", "center")
        calign = side if copt == "same" else {"left": "right", "right": "left"}.get(side, "center") if copt == "opposite" else "center"
        clock = (f"drawtext=fontfile={h['mono']}:text='%{{eif\\:floor(({allot}-{off}-t)/60)\\:d}}\\:%{{eif\\:mod(floor({allot}-{off}-t)\\,60)\\:d\\:2}}':"
                 f"fontcolor={h['clock']}:{self.bord}:fontsize={F['clock']}:x={self.xexpr(calign)}:y={cy}")
        return ",".join([
            self.text(0, kicker, h["kicker"], F["kicker"], int(H * .02), align=side),
            self.text(0, title.upper(), h["title"], F["title"], int(H * .02) + F["kicker"] + 12, align=side),
            self.text(0, target, h["target"], F["target"], int(H * .02) + F["kicker"] + F["title"] + 22, align=side),
            clock,
            self.text(0, self.s["left"], h["label"], int(F["kicker"] * .9), cy + F["clock"] + 8, align=calign),
            f"drawbox=x=0:y={H - F['bar']}:w={W}:h={F['bar']}:color={h['bar_back']}:t=fill",
            f"drawbox=x=0:y={H - F['bar']}:w='{W}*(({off}+t)/{allot})':h={F['bar']}:color={h['bar_fill']}@1:t=fill"])

    def breakcard(self, secs, nxt):
        F, h = self.F, self.h; W, H = F["W"], F["H"]
        return ",".join([
            f"drawbox=x=0:y=0:w={W}:h={H}:color={h['break_dim']}:t=fill",
            self.text(0, self.s["break"], h["kicker"], F["title"], int(H * .24)),
            (f"drawtext=fontfile={h['mono']}:text='%{{eif\\:ceil({secs}-t)\\:d}}':fontcolor={h['clock']}:{self.bord}:"
             f"fontsize={int(F['clock'] * 2.4)}:x=(w-tw)/2:y={int(H * .34)}"),
            self.text(0, self.s["next"], h["label"], F["kicker"], int(H * .66)),
            self.text(0, nxt.upper(), h["title"], F["target"], int(H * .66) + F["kicker"] + 14)])


def blend_frames(d, a, b, nf):
    outs = []; A = B = None
    for k in range(1, nf + 1):
        fn = os.path.join(d, f"x{a}_{b}_{nf}_{k}.png")
        if not os.path.exists(fn):
            if A is None: A, B = Image.open(f"{d}/p{a}.png"), Image.open(f"{d}/p{b}.png")
            t = k / (nf + 1); Image.blend(A, B, t * t * (3 - 2 * t)).save(fn)
        outs.append(fn)
    return outs


def segment(args, work, posedir, cycle, cycle_s, dur, ov, fps, fade_max, label):
    """One continuous stretch of a looping pose cycle with the HUD. Cached by everything it depends on."""
    if args.preview: dur = min(dur, 5.0)
    cache = os.path.join(work, "cache"); os.makedirs(cache, exist_ok=True)
    out = os.path.join(cache, sha(posedir, cycle, round(cycle_s, 4), round(dur, 3), ov, fps, fade_max, CODE_VERSION) + ".mp4")
    if os.path.exists(out): print(f"  {label}: cached"); return out
    per = cycle_s / len(cycle); nf = int(min(fade_max, .45 * per) * fps) if fade_max > 0 else 0; hold = per - nf / fps
    lst = out + ".txt"
    with open(lst, "w") as f:
        for _ in range(math.ceil(dur / cycle_s) + 1):
            for i, p in enumerate(cycle):
                nxt = cycle[(i + 1) % len(cycle)]; f.write(f"file '{posedir}/p{p}.png'\nduration {hold:.4f}\n")
                if nf and nxt != p:
                    for fn in blend_frames(posedir, p, nxt, nf): f.write(f"file '{fn}'\nduration {1 / fps:.5f}\n")
                elif nf: f.write(f"file '{posedir}/p{p}.png'\nduration {nf / fps:.5f}\n")
        f.write(f"file '{posedir}/p{cycle[0]}.png'\n")
    tmp = out + ".part.mp4"
    run(["ffmpeg", "-y", "-loglevel", "error", "-f", "concat", "-safe", "0", "-i", lst, "-t", f"{dur:.3f}",
         "-vf", f"fps={fps},{ov}", "-pix_fmt", "yuv420p", "-r", str(fps), tmp])
    os.replace(tmp, out); print(f"  {label}: rendered"); return out


def breakcard(args, work, theme, F, hud, secs, nxt, fmt):
    if args.preview: secs = min(secs, 2)
    cache = os.path.join(work, "cache"); os.makedirs(cache, exist_ok=True)
    bgpng = os.path.join(work, f"backdrop-{fmt}-{sha(json.dumps(theme['backdrop'], sort_keys=True), json.dumps(F, sort_keys=True), CODE_VERSION)}.png")
    if not os.path.exists(bgpng): flatten(backdrop_layers(theme, F, fmt), (F["W"], F["H"])).convert("RGB").save(bgpng)
    vf = hud.breakcard(secs, nxt)
    out = os.path.join(cache, sha(bgpng, vf, secs, theme["fps"], CODE_VERSION) + ".mp4")
    if os.path.exists(out): return out
    tmp = out + ".part.mp4"
    run(["ffmpeg", "-y", "-loglevel", "error", "-loop", "1", "-framerate", str(theme["fps"]), "-i", bgpng, "-t", str(secs), "-vf", vf,
         "-pix_fmt", "yuv420p", "-r", str(theme["fps"]), tmp])
    os.replace(tmp, out); return out


def apply_look(theme, chart, default_scene):
    """Each chart can have its own room and props: theme.json "chart_looks": {"1": {"backdrop": {...}, "scene": "config/scene.chart1.json"}}. Returns (theme, scene path)."""
    look = (theme.get("chart_looks") or {}).get(str(chart)) or {}
    if look.get("backdrop"): theme = dict(theme, backdrop=look["backdrop"])
    return theme, (os.path.join(ROOT, look["scene"]) if look.get("scene") else default_scene)


def make_plan(data, chart, level, only):
    """The whole video as a list of timed segments, read straight from the data file. Render and export both use it."""
    lv, timing, ex5 = chart["levels"][level], data["timing"]["secondsPerExercise"], chart["exercises"][4]; plan = []
    for i in range(4):
        slot = f"ex{i + 1}"; name, allot, reps = chart["exercises"][i]["name"], timing[i], lv["reps"][i]
        if not only or slot in only: plan.append(dict(kind="exercise", slot=slot, name=name, dur=allot, allot=allot, off=0.0, reps=reps, n=i + 1))
        if not only: plan.append(dict(kind="break", secs=data["appDefaults"]["transitionSeconds"], next=chart["exercises"][i + 1]["name"]))
    if not only or "run" in only or "jump" in only:
        allot, steps = timing[4], lv["steps"]; every, jcount = ex5["jumpEvery"], ex5["jumpCount"]; window = ex5.get("jumpWindowSeconds", 12)
        sets = steps // every; step_s = (allot - sets * window) / steps; off, done, k = 0.0, 0, 0
        while done < steps:
            block = min(every, steps - done); dur = block * step_s
            if not only or "run" in only: plan.append(dict(kind="run", slot="run", name=ex5["name"], dur=dur, allot=allot, off=off, steps=steps, step_s=step_s, label=f"run block {k + 1}"))
            off += dur; done += block
            if done < steps:
                if not only or "jump" in only: plan.append(dict(kind="jumps", slot="jump", name=ex5["jumpName"], dur=window, allot=allot, off=off, count=jcount, label=f"jumps {k + 1}"))
                off += window
            k += 1
    return plan, ex5


def export_layers(dirpath, plan, theme, scene, reg, slots, F, fmt, work, chart_id, level, data_path, with_composites=False, stage=None):
    """Write the scene as separate files any other tool can recombine: backdrop layers, props, the boy per pose, and scene.json."""
    root = os.path.join(dirpath, f"chart{chart_id}-{fmt}"); os.makedirs(os.path.join(root, "backdrop"), exist_ok=True)
    for i, (n, im) in enumerate(backdrop_layers(theme, F, fmt)): im.save(os.path.join(root, "backdrop", f"{i:02d}-{n}.png"))
    flatten(backdrop_layers(theme, F, fmt), (F["W"], F["H"])).convert("RGB").save(os.path.join(root, "backdrop.png"))
    man = {"_about": "Layer pack. Stack, bottom to top: backdrop, props_behind, boy (one file per pose), props_front, then the on-screen text from 'segments'. All PNGs are frame-sized.",
           "chart": chart_id, "level": level, "format": fmt, "size": [F["W"], F["H"]], "fps": theme["fps"], "ground_y": int(F["H"] * F["ground"]),
           "data_file": os.path.basename(data_path), "strings": theme["strings"], "slots": {}, "segments": []}
    for slot in sorted({p["slot"] for p in plan if "slot" in p}):
        st = reg["strips"][slots[slot]]; src = compose(slots[slot], st, theme, scene, F, fmt, work, slot, (stage or {}).get(slot)); sd = os.path.join(root, slot); os.makedirs(sd, exist_ok=True)
        files = {"boy": [], "composite": []}
        for k in range(1, st["poses"] + 1):
            shutil.copy(os.path.join(src, f"layer_p{k}.png"), os.path.join(sd, f"boy_p{k}.png")); files["boy"].append(f"{slot}/boy_p{k}.png")
            if with_composites: shutil.copy(os.path.join(src, f"p{k}.png"), os.path.join(sd, f"composite_p{k}.png")); files["composite"].append(f"{slot}/composite_p{k}.png")
        for k in st.get("mirror", []):
            shutil.copy(os.path.join(src, f"layer_p{k}m.png"), os.path.join(sd, f"boy_p{k}m.png")); files["boy"].append(f"{slot}/boy_p{k}m.png")
        for extra in ("props_behind.png", "props_front.png"):
            if os.path.exists(os.path.join(src, extra)): shutil.copy(os.path.join(src, extra), os.path.join(sd, extra)); files[extra[:-4]] = f"{slot}/{extra}"
        man["slots"][slot] = {"strip": slots[slot], "anchor": st["anchor"], "hud": (stage or {}).get(slot), "cycle": st["cycle"], **({"cycle_reverse": st["cycle_reverse"]} if st.get("cycle_reverse") else {}), "files": files, **jload(os.path.join(src, "geom.json"))}
    for p in plan:
        seg = {k: v for k, v in p.items() if k not in ("label",)}
        if p["kind"] in ("exercise", "run", "jumps") and "cycle_s" in p: seg["cycle_seconds"] = round(p["cycle_s"], 4)
        man["segments"].append(seg)
    json.dump(man, open(os.path.join(root, "scene.json"), "w"), indent=1); return root


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--data", help="5bx-charts.json (the plan; never copied into this kit)")
    ap.add_argument("--chart", type=int, default=1); ap.add_argument("--level", default="A+")
    ap.add_argument("--format", default="landscape", choices=["landscape", "portrait"])
    ap.add_argument("--out", default="out.mp4"); ap.add_argument("--work", default=os.path.join(ROOT, ".work"))
    ap.add_argument("--theme", default=os.path.join(ROOT, "config", "theme.json")); ap.add_argument("--scene", default=os.path.join(ROOT, "config", "scene.json"))
    ap.add_argument("--preview", action="store_true"); ap.add_argument("--no-fade", action="store_true")
    ap.add_argument("--only", default="", help="comma list of slots: ex1,ex2,ex3,ex4,run,jump")
    ap.add_argument("--tag", default="", help="name a variant (a different scene or look); becomes part of the build id")
    ap.add_argument("--no-record", action="store_true", help="do not write builds/<id>.json")
    ap.add_argument("--list", action="store_true"); ap.add_argument("--bake", action="store_true", help="write assets/ (sprites + backdrop layers) and stop")
    ap.add_argument("--export", metavar="DIR", help="write the layer pack (separate PNGs + scene.json) to DIR instead of a video")
    ap.add_argument("--with-composites", action="store_true", help="with --export: also write the finished frames (redundant; the layers recreate them)")
    args = ap.parse_args()

    theme = jload(args.theme); reg = jload(os.path.join(ROOT, "config", "strips.json"))
    theme, scene_path = apply_look(theme, args.chart, args.scene); scene = jload(scene_path)
    if args.bake:
        for name, st in reg["strips"].items():
            if os.path.exists(os.path.join(ROOT, "sheets", st["file"])): print(f"  sprites {name}: {len(bake(name, st, theme)['poses'])} poses")
        for fmt, F in theme["formats"].items(): print(f"  backdrop {theme['backdrop'].get('id', 'forest')}/{fmt}: {len(backdrop_layers(theme, F, fmt))} layers")
        return
    if not args.data: raise SystemExit("--data is required (path to 5bx-charts.json)")
    data = jload(args.data)
    chart = next((c for c in data["charts"] if c["id"] == args.chart), None)
    if chart is None: raise SystemExit(f"chart {args.chart} not in {args.data}")
    slots = reg["charts"].get(str(args.chart), {}); all_slots = SLOTS + ["run", "jump"]
    only = [x for x in args.only.split(",") if x]
    for x in only:
        if x not in all_slots: raise SystemExit(f"--only: unknown slot {x}")
    def is_missing(x): return x not in slots or slots[x] not in reg["strips"] or not os.path.exists(os.path.join(ROOT, "sheets", reg["strips"][slots[x]]["file"]))
    need = [x for x in all_slots if not only or x in only]                 # a chart can be previewed one exercise at a time while the rest is still being made
    missing = [x for x in need if is_missing(x)]
    names = {f"ex{i + 1}": chart["exercises"][i]["name"] for i in range(4)}; names["run"] = chart["exercises"][4]["name"]; names["jump"] = chart["exercises"][4].get("jumpName", "")
    if args.list or missing:
        print(f"chart {args.chart}:")
        for x in all_slots: print(f"  {x:5s} {names[x]:40s} -> {slots.get(x, '(no strip yet)')}{'  MISSING' if is_missing(x) else ''}")
        if missing and not args.list: raise SystemExit(f"\nchart {args.chart} needs strips for: {', '.join(missing)}. See README: 'Add an exercise'.")
        return

    F = theme["formats"][args.format]; fps = theme["fps"]; fade_max = 0 if args.no_fade else theme["fade_max_seconds"]
    plan, ex5 = make_plan(data, chart, args.level, only); os.makedirs(args.work, exist_ok=True); hud = Hud(theme, F); S = theme["strings"]
    lv = chart["levels"][args.level]; sstep = lambda sl: reg["strips"][slots[sl]]
    stage = {}
    def seg_texts(p):
        if p["kind"] == "exercise": return S["kicker"].format(n=p["n"]), p["name"], S["reps"].format(reps=p["reps"])
        if p["kind"] == "run": return S["kicker"].format(n=5), p["name"], S["steps"].format(steps=p["steps"])
        return S["jump_kicker"], S["jump_title"].format(count=p["count"], name=p["name"]), S["jump_target"]
    for p in plan:                                                     # where the title goes and how big the figure may be, per exercise
        if p.get("slot") and p["slot"] not in stage: stg = sstep(p["slot"]); stage[p["slot"]] = stage_plan(stg, bake(slots[p["slot"]], stg, theme), theme, F, args.format, seg_texts(p))
    def frames(slot): return compose(slots[slot], sstep(slot), theme, scene, F, args.format, args.work, slot, stage.get(slot))
    for p in plan:                                                     # cycle length per segment, from the data
        if p["kind"] == "exercise": p["cycle_s"] = p["allot"] / p["reps"] * sstep(p["slot"])["reps_per_cycle"]
        elif p["kind"] == "run": p["cycle_s"] = p["step_s"] / sstep("run")["steps_per_cycle"]
        elif p["kind"] == "jumps": p["cycle_s"] = p["dur"] / (ex5["jumpCount"] / sstep("jump")["jumps_per_cycle"])
    if args.export:
        root = export_layers(args.export, plan, theme, scene, reg, slots, F, args.format, args.work, args.chart, args.level, args.data, args.with_composites, stage)
        print("wrote layer pack:", root); return

    parts = []
    for p in plan:
        if p["kind"] == "break": parts.append(breakcard(args, args.work, theme, F, hud, p["secs"], p["next"], args.format)); continue
        st = sstep(p["slot"])
        if p["kind"] == "exercise": ov = lambda off=0.0, p=p: hud.exercise(S["kicker"].format(n=p["n"]), p["name"], S["reps"].format(reps=p["reps"]), p["allot"], off, stage.get(p["slot"])); label = p["name"]
        elif p["kind"] == "run": ov = lambda off=0.0, p=p: hud.exercise(S["kicker"].format(n=5), p["name"], S["steps"].format(steps=p["steps"]), p["allot"], p["off"] + off, stage.get(p["slot"])); label = p["label"]
        else: ov = lambda off=0.0, p=p: hud.exercise(S["jump_kicker"], S["jump_title"].format(count=p["count"], name=p["name"]), S["jump_target"], p["allot"], p["off"] + off, stage.get(p["slot"])); label = p["label"]
        rev = st.get("cycle_reverse") if p["kind"] == "exercise" else None
        if rev:                                                        # "reverse direction after half the number of counts": whole cycles first, then the reversed order
            first = math.floor(p["reps"] / 2 / st["reps_per_cycle"] + 0.5) * p["cycle_s"]
            parts.append(segment(args, args.work, frames(p["slot"]), st["cycle"], p["cycle_s"], first, ov(0.0), fps, fade_max, label + " (first half)"))
            parts.append(segment(args, args.work, frames(p["slot"]), rev, p["cycle_s"], p["dur"] - first, ov(first), fps, fade_max, label + " (reversed)"))
        else: parts.append(segment(args, args.work, frames(p["slot"]), st["cycle"], p["cycle_s"], p["dur"], ov(), fps, fade_max, label))
    steps = lv["steps"]
    if not only or "run" in only: print(f"  ex5: {steps} steps, {60 / [x for x in plan if x['kind'] == 'run'][0]['step_s']:.0f} steps/min")
    lst = os.path.join(args.work, "all.txt")
    with open(lst, "w") as f:
        for q in parts: f.write(f"file '{q}'\n")
    tmp = args.out + ".part.mp4"
    run(["ffmpeg", "-y", "-loglevel", "error", "-f", "concat", "-safe", "0", "-i", lst, "-c", "copy", "-movflags", "+faststart", tmp])
    run(["ffmpeg", "-v", "error", "-i", tmp, "-f", "null", "-"])       # full-decode check before it counts
    os.replace(tmp, args.out); print("wrote", args.out)
    if not (args.preview or only or args.no_record):                   # a full render gets a record of exactly what went in
        sys.path.insert(0, HERE); import builds
        builds.record(args, args.theme, scene_path, args.chart, {x: slots[x] for x in all_slots}, reg, theme, CODE_VERSION, args.out)


if __name__ == "__main__":
    main()
