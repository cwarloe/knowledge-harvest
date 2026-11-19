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
import argparse, hashlib, json, math, os, random, subprocess, sys
import numpy as np
from PIL import Image, ImageDraw

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
from keyer import key as chroma_key
from recolor import recolor

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


# ---------- backdrop (a layer of its own) ----------
def backdrop(theme, F):
    b = theme["backdrop"]; W, H = F["W"], F["H"]; gy = int(H * F["ground"])
    if b.get("style") == "image" and b.get("image"):
        im = Image.open(os.path.join(ROOT, b["image"])).convert("RGB")
        s = max(W / im.width, H / im.height); im = im.resize((round(im.width * s), round(im.height * s)), Image.LANCZOS)
        return im.crop(((im.width - W) // 2, (im.height - H) // 2, (im.width - W) // 2 + W, (im.height - H) // 2 + H))
    S = 2; rnd = random.Random(b.get("seed", 7))
    im = Image.new("RGB", (W * S, H * S)); d = ImageDraw.Draw(im)
    top, bot = rgb(b["sky_top"]), rgb(b["sky_bottom"])
    for y in range(gy * S):
        t = y / (gy * S); d.line([(0, y), (W * S, y)], fill=tuple(int(top[i] + (bot[i] - top[i]) * t) for i in range(3)))
    for _ in range(7):
        cx, cy, s = rnd.randint(0, W) * S, rnd.randint(int(H * .06), int(H * .30)) * S, rnd.randint(60, 120) * S
        for dx, dy, r in ((0, 0, 1), (.8, .2, .8), (-.8, .25, .75), (.3, -.25, .7)):
            d.ellipse([cx + dx * s - r * s, cy + dy * s - r * s * .55, cx + dx * s + r * s, cy + dy * s + r * s * .55], fill=(255, 255, 255))
    def ridge(base, amp, col, seed):
        r = random.Random(seed); pts = [(0, gy * S)]
        for x in range(0, W * S + 80 * S, 80 * S): pts.append((x, (base - r.randint(0, amp)) * S))
        pts.append((W * S, gy * S)); d.polygon(pts, fill=col)
    ridge(int(H * .55), int(H * .10), rgb(b["mountains"][0]), 1)
    ridge(int(H * .62), int(H * .08), rgb(b["mountains"][1]), 2)
    def pine(x, base, h, col):
        w = h * .42; d.rectangle([x - w * .06, base - h * .12, x + w * .06, base], fill=(86, 60, 40))
        for k in range(3):
            y0 = base - h * (.12 + .27 * k); y1 = y0 - h * .42; ww = w * (1 - .24 * k)
            d.polygon([(x - ww / 2, y0), (x + ww / 2, y0), (x, y1)], fill=col)
    for row, (col, hmin, hmax, step) in enumerate([(rgb(b["trees"][0]), .13, .19, 70), (rgb(b["trees"][1]), .17, .26, 110)]):
        x = -20 * S
        while x < W * S + 60 * S:
            pine(x, (gy - 6 + row * 14) * S, rnd.randint(int(H * hmin), int(H * hmax)) * S, col); x += int(rnd.uniform(.7, 1.3) * step * S)
    d.rectangle([0, gy * S, W * S, H * S], fill=rgb(b["ground"]))
    d.rectangle([0, gy * S, W * S, (gy + 10) * S], fill=rgb(b["ground_line"]))
    for _ in range(60):
        px, py = rnd.randint(0, W) * S, rnd.randint(gy + 20, H - 10) * S
        d.ellipse([px, py, px + rnd.randint(6, 16) * S, py + rnd.randint(3, 7) * S], fill=rgb(b["pebbles"]))
    return im.resize((W, H), Image.LANCZOS)


# ---------- the boy (a layer of his own) ----------
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


def split(path, n, theme):
    """Strip -> n cut-out poses, left to right. Split by connected shape: neighbours overlap in x."""
    rgba = recolor(chroma_key(Image.open(path), **theme["key"]), theme.get("recolor")); a = np.array(rgba)
    lab, ds = components(a[..., 3] > 128)
    ids = list(range(1, lab.max() + 1)); area = {i: int((lab == i).sum()) for i in ids}
    big = sorted([i for i in ids if area[i] > 400], key=lambda i: -area[i])[:n]
    if len(big) != n: raise SystemExit(f"{path}: expected {n} poses, found {len(big)}. Check 'poses' in config/strips.json or regenerate the strip.")
    cent = {i: np.argwhere(lab == i).mean(axis=0) for i in ids}
    for i in ids:                                         # fold stray fragments into the nearest pose
        if i not in big and area[i] > 6:
            j = min(big, key=lambda b: np.hypot(*(cent[b] - cent[i]))); lab[lab == i] = j
    big.sort(key=lambda i: np.argwhere(lab == i)[:, 1].mean())
    up = np.kron(lab, np.ones((ds, ds), np.int32)); full = np.zeros(a.shape[:2], np.int32); full[:up.shape[0], :up.shape[1]] = up
    poses = []
    for i in big:
        b = a.copy(); b[..., 3] = np.where(full == i, b[..., 3], 0); ys, xs = np.nonzero(b[..., 3] > 16)
        p = Image.fromarray(b[ys.min():ys.max() + 1, xs.min():xs.max() + 1], "RGBA"); p.offset = (int(xs.min()), int(ys.min())); poses.append(p)
    return poses


def anchor_x(p, how):
    a = np.array(p)[..., 3] > 128; h, w = a.shape
    if how == "head":
        xs = np.nonzero(a[:max(6, int(h * .12))].any(axis=0))[0]; return float(xs.mean())
    xs = np.nonzero(a[-14:].any(axis=0))[0]
    return {"span-left": float(xs.min()), "span-right": float(xs.max()), "span-center": float(xs.mean())}[how]


def compose(name, strip, theme, F, fmt, work):
    """Write layer_pK.png (the boy alone, transparent) and pK.png (boy over backdrop). Cached."""
    path = os.path.join(ROOT, "sheets", strip["file"])
    tag = sha(filehash(path), json.dumps(strip, sort_keys=True), json.dumps(theme["key"]), json.dumps(theme.get("recolor")),
              json.dumps(theme["backdrop"], sort_keys=True), json.dumps(F, sort_keys=True), CODE_VERSION)
    out = os.path.join(work, "frames", f"{name}-{fmt}-{tag}")
    if os.path.exists(os.path.join(out, "DONE")): return out
    os.makedirs(out, exist_ok=True)
    poses = split(path, strip["poses"], theme); bg = backdrop(theme, F)
    floor = max(p.offset[1] + p.size[1] for p in poses); top = min(p.offset[1] for p in poses)
    anchors = [anchor_x(p, strip["anchor"]) for p in poses]
    L = max(anchors); R = max(p.size[0] - a for p, a in zip(poses, anchors))
    bw, bh = F["box"]; s = min(bw / (L + R), bh / (floor - top))
    gy = int(F["H"] * F["ground"]); X0 = F["W"] / 2 + (L - R) * s / 2
    for k, (p, ax) in enumerate(zip(poses, anchors), 1):
        w, h = max(1, round(p.size[0] * s)), max(1, round(p.size[1] * s))
        layer = Image.new("RGBA", (F["W"], F["H"]), (0, 0, 0, 0))
        layer.alpha_composite(p.resize((w, h), Image.LANCZOS), (round(X0 - ax * s), gy + 10 - round((floor - p.offset[1]) * s)))
        layer.save(os.path.join(out, f"layer_p{k}.png"))
        f = bg.convert("RGBA"); f.alpha_composite(layer); f.convert("RGB").save(os.path.join(out, f"p{k}.png"))
    open(os.path.join(out, "DONE"), "w").write("ok")
    return out


# ---------- video ----------
def run(cmd):
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode: raise SystemExit(f'ffmpeg failed:\n{" ".join(cmd[:14])}...\n{r.stderr[-1500:]}')

def esc(t): return t.replace("\\", "\\\\").replace(":", r"\:").replace("'", r"\\\'")


class Hud:
    def __init__(self, theme, F):
        self.t, self.F, self.h, self.s = theme, F, theme["hud"], theme["strings"]
        self.bord = f"borderw={self.h['outline_width']}:bordercolor={self.h['outline']}"

    def text(self, font, txt, color, size, y, mono=False):
        return (f"drawtext=fontfile={self.h['mono'] if mono else self.h['font']}:text='{esc(txt)}':fontcolor={color}:{self.bord}:"
                f"fontsize={size}:x=(w-tw)/2:y={y}")

    def exercise(self, kicker, title, target, allot, off=0.0):
        F, h = self.F, self.h; W, H = F["W"], F["H"]; gy = int(H * F["ground"]); cy = gy + int((H - gy) * .22)
        clock = (f"drawtext=fontfile={h['mono']}:text='%{{eif\\:floor(({allot}-{off}-t)/60)\\:d}}\\:%{{eif\\:mod(floor({allot}-{off}-t)\\,60)\\:d\\:2}}':"
                 f"fontcolor={h['clock']}:{self.bord}:fontsize={F['clock']}:x=(w-tw)/2:y={cy}")
        return ",".join([
            self.text(0, kicker, h["kicker"], F["kicker"], int(H * .02)),
            self.text(0, title.upper(), h["title"], F["title"], int(H * .02) + F["kicker"] + 12),
            self.text(0, target, h["target"], F["target"], int(H * .02) + F["kicker"] + F["title"] + 22),
            clock,
            self.text(0, self.s["left"], h["label"], int(F["kicker"] * .9), cy + F["clock"] + 8),
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
    if not os.path.exists(bgpng): backdrop(theme, F).save(bgpng)
    vf = hud.breakcard(secs, nxt)
    out = os.path.join(cache, sha(bgpng, vf, secs, theme["fps"], CODE_VERSION) + ".mp4")
    if os.path.exists(out): return out
    tmp = out + ".part.mp4"
    run(["ffmpeg", "-y", "-loglevel", "error", "-loop", "1", "-framerate", str(theme["fps"]), "-i", bgpng, "-t", str(secs), "-vf", vf,
         "-pix_fmt", "yuv420p", "-r", str(theme["fps"]), tmp])
    os.replace(tmp, out); return out


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--data", required=True, help="5bx-charts.json (the plan; never copied into this kit)")
    ap.add_argument("--chart", type=int, default=1); ap.add_argument("--level", default="A+")
    ap.add_argument("--format", default="landscape", choices=["landscape", "portrait"])
    ap.add_argument("--out", default="out.mp4"); ap.add_argument("--work", default=os.path.join(ROOT, ".work"))
    ap.add_argument("--theme", default=os.path.join(ROOT, "config", "theme.json"))
    ap.add_argument("--preview", action="store_true"); ap.add_argument("--no-fade", action="store_true")
    ap.add_argument("--only", default="", help="comma list of slots: ex1,ex2,ex3,ex4,run,jump")
    ap.add_argument("--list", action="store_true")
    args = ap.parse_args()

    data = jload(args.data); theme = jload(args.theme); reg = jload(os.path.join(ROOT, "config", "strips.json"))
    chart = next((c for c in data["charts"] if c["id"] == args.chart), None)
    if chart is None: raise SystemExit(f"chart {args.chart} not in {args.data}")
    slots = reg["charts"].get(str(args.chart), {}); need = SLOTS + ["run", "jump"]
    missing = [s for s in need if s not in slots or slots[s] not in reg["strips"] or not os.path.exists(os.path.join(ROOT, "sheets", reg["strips"][slots[s]]["file"]))]
    names = {f"ex{i + 1}": chart["exercises"][i]["name"] for i in range(4)}; names["run"] = chart["exercises"][4]["name"]; names["jump"] = chart["exercises"][4].get("jumpName", "")
    if args.list or missing:
        print(f"chart {args.chart}:")
        for s in need: print(f"  {s:5s} {names[s]:40s} -> {slots.get(s, '(no strip yet)')}{'  MISSING' if s in missing else ''}")
        if missing and not args.list: raise SystemExit(f"\nchart {args.chart} needs strips for: {', '.join(missing)}. See README: 'Add an exercise'.")
        return
    only = [s for s in args.only.split(",") if s]
    for s in only:
        if s not in need: raise SystemExit(f"--only: unknown slot {s}")

    F = theme["formats"][args.format]; fps = theme["fps"]; fade_max = 0 if args.no_fade else theme["fade_max_seconds"]
    lv, timing = chart["levels"][args.level], data["timing"]["secondsPerExercise"]; ex5 = chart["exercises"][4]
    os.makedirs(args.work, exist_ok=True); hud = Hud(theme, F); S = theme["strings"]
    def want(slot): return not only or slot in only
    def frames(slot): return compose(slots[slot], reg["strips"][slots[slot]], theme, F, args.format, args.work)

    parts = []
    for i in range(4):
        slot = f"ex{i + 1}"; st = reg["strips"][slots[slot]]
        if want(slot):
            name, allot, reps = chart["exercises"][i]["name"], timing[i], lv["reps"][i]
            ov = hud.exercise(S["kicker"].format(n=i + 1), name, S["reps"].format(reps=reps), allot)
            parts.append(segment(args, args.work, frames(slot), st["cycle"], allot / reps * st["reps_per_cycle"], allot, ov, fps, fade_max, name))
        if not only:                                      # breaks only in a whole-video build
            parts.append(breakcard(args, args.work, theme, F, hud, data["appDefaults"]["transitionSeconds"], chart["exercises"][i + 1]["name"], args.format))

    if want("run") or want("jump"):
        allot, steps = timing[4], lv["steps"]; every, jcount = ex5["jumpEvery"], ex5["jumpCount"]; window = ex5.get("jumpWindowSeconds", 12)
        sets = steps // every; step_s = (allot - sets * window) / steps
        run_st, jmp_st = reg["strips"][slots["run"]], reg["strips"][slots["jump"]]
        print(f"  ex5: {steps} steps, {sets} jump sets, {step_s:.3f}s/step, {60 / step_s:.0f} steps/min")
        off, done, k = 0.0, 0, 0
        while done < steps:
            block = min(every, steps - done); dur = block * step_s
            if want("run"):
                ov = hud.exercise(S["kicker"].format(n=5), ex5["name"], S["steps"].format(steps=steps), allot, off)
                parts.append(segment(args, args.work, frames("run"), run_st["cycle"], step_s / run_st["steps_per_cycle"], dur, ov, fps, fade_max, f"run block {k + 1}"))
            off += dur; done += block
            if done < steps:
                if want("jump"):
                    ov = hud.exercise(S["jump_kicker"], S["jump_title"].format(count=jcount, name=ex5["jumpName"]), S["jump_target"], allot, off)
                    parts.append(segment(args, args.work, frames("jump"), jmp_st["cycle"], window / (jcount / jmp_st["jumps_per_cycle"]), window, ov, fps, fade_max, f"jumps {k + 1}"))
                off += window
            k += 1

    lst = os.path.join(args.work, "all.txt")
    with open(lst, "w") as f:
        for p in parts: f.write(f"file '{p}'\n")
    tmp = args.out + ".part.mp4"
    run(["ffmpeg", "-y", "-loglevel", "error", "-f", "concat", "-safe", "0", "-i", lst, "-c", "copy", "-movflags", "+faststart", tmp])
    run(["ffmpeg", "-v", "error", "-i", tmp, "-f", "null", "-"])       # full-decode check before it counts
    os.replace(tmp, args.out); print("wrote", args.out)


if __name__ == "__main__":
    main()
