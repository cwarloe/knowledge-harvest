"""QC gate: scores a returned sheet, background or mat against the specs. Every check prints PASS / WARN / FAIL.
Automated checks catch measurable defects in seconds; pose correctness still needs a human (see LESSONS.md)."""
import glob, os, sys
import numpy as np
import sheetlib as S

OK, WARN, FAIL = "PASS", "WARN", "FAIL"


class Report:
    def __init__(self, name):
        self.name = name
        self.rows = []

    def add(self, status, check, detail):
        self.rows.append((status, check, detail))

    @property
    def worst(self):
        order = {OK: 0, WARN: 1, FAIL: 2}
        return max((r[0] for r in self.rows), key=lambda s: order[s], default=OK)

    def show(self):
        print(f"\n{self.name}   =>  {self.worst}")
        for st, ck, dt in self.rows:
            print(f"  [{st}] {ck}: {dt}")


# ------------------------------------------------------------------ sheets
def qc_sheet(path, ex, ch, stage, min_gap_warn=0.03, min_gap_fail=0.005):
    rep = Report(os.path.basename(path) + f"  ({ex['id']})")
    a = S.read_rgb(path)
    h, w = a.shape[:2]
    bg, spread = S.measure_bg(a)
    magenta = np.array(S.hex2rgb(stage["magenta"]), float)
    off = float(np.sqrt(((bg - magenta) ** 2).sum()))
    st = OK if off <= 30 else (WARN if off <= 60 else FAIL)
    rep.add(st, "background", f"median {tuple(int(v) for v in bg)} is {off:.0f} from #FF00FF; border noise 99th pct {spread:.0f} "
                              f"-> use a key tolerance of at least {max(40, int(spread) + 15)}")
    q = ex["qc"]
    rows, lab = S.segment(a, bg, rows_expected=q["rows"])
    counts = [len(r) for r in rows]
    exp = [q["per_row"]] * q["rows"]
    why = "" if counts == exp else (" (fewer than expected usually means two figures touch and merged into one shape)"
                                    if sum(counts) < sum(exp) else " (more than expected: stray marks or a split figure)")
    rep.add(OK if counts == exp else FAIL, "figure count", f"found {counts} per row, expected {exp}{why}")
    if counts != exp:
        return rep
    # clearance: true pixel distance between neighbouring figures (not bounding boxes)
    worst_gap, worst_loc = 1.0, None
    for ri, row in enumerate(rows):
        for i in range(len(row) - 1):
            gap = S.clearance(lab, a, row[i], row[i + 1], bg) / w
            if gap < worst_gap:
                worst_gap, worst_loc = gap, (ri + 1, i + 1, i + 2)
    px = int(worst_gap * w)
    st = OK if worst_gap >= min_gap_warn else (WARN if worst_gap >= min_gap_fail else FAIL)
    rep.add(st, "gap between figures", f"smallest {worst_gap:.1%} of width ({px} px) between row {worst_loc[0]} figures {worst_loc[1]} and {worst_loc[2]}"
                                       f"; target 8%, warn <{min_gap_warn:.0%}, fail <{min_gap_fail:.1%} (touching)")
    # edge margin
    edge = [f["bbox"] for r in rows for f in r
            if f["bbox"][0] < 0.008 * w or f["bbox"][0] + f["bbox"][2] > 0.992 * w or f["bbox"][1] < 0.008 * h or f["bbox"][1] + f["bbox"][3] > 0.992 * h]
    rep.add(OK if not edge else WARN, "edge margin", "all figures clear of the sheet edge" if not edge else f"{len(edge)} figure(s) within 0.8% of the edge")
    # floor line + airborne
    grounded = q.get("grounded", [])
    if q.get("floor_check") and len(grounded) >= 2:
        spreads = []
        for row in rows:
            bots = [(row[i]["bbox"][1] + row[i]["bbox"][3]) / h for i in grounded if i < len(row)]
            spreads.append(max(bots) - min(bots))
        sp = max(spreads)
        rep.add(OK if sp <= 0.03 else (WARN if sp <= 0.06 else FAIL), "floor line", f"grounded poses' bottoms differ by up to {sp:.1%} of sheet height (pass <=3%)")
    for k, need in (q.get("airborne") or {}).items():
        k = int(k)
        lifts = []
        for row in rows:
            gb = float(np.median([(row[i]["bbox"][1] + row[i]["bbox"][3]) / h for i in grounded]))
            lifts.append(gb - (row[k]["bbox"][1] + row[k]["bbox"][3]) / h)
        got = min(lifts)
        rep.add(OK if got >= need else FAIL, f"lift of pose {k + 1}", f"{got:.1%} of sheet height above the floor line, need >= {need:.1%}")
    # palette (the figure still looks like this character)
    absent, thin = [], []
    for ri, row in enumerate(rows):
        for fi, f in enumerate(row):
            m = S.figure_mask(lab, a, f, bg)
            px = a[m].astype(float)
            if len(px) == 0:
                continue
            for p in ch["palette"]:
                d = np.sqrt(((px - np.array(S.hex2rgb(p["hex"]), float)) ** 2).sum(1))
                frac = (d <= p["tol"]).mean()
                tag = f"{p['name']}@r{ri + 1}f{fi + 1}"
                if frac < p["min_frac"] / 10:
                    absent.append(tag)          # colour essentially missing: wrong outfit or wrong character
                elif frac < p["min_frac"]:
                    thin.append(tag)            # little visible (e.g. seen from above or behind)
    if absent:
        rep.add(FAIL, "character palette", "colour missing: " + ", ".join(absent[:8]))
    elif thin:
        rep.add(WARN, "character palette", "little visible (check the outfit is right): " + ", ".join(thin[:8]))
    else:
        rep.add(OK, "character palette", "every figure contains the character's skin, hair and clothing colours")
    return rep


def qc_sheets_dir(folder, ch, stage, exercises):
    reps = []
    for p in sorted(glob.glob(os.path.join(folder, "JOB-*.png"))):
        try:
            ex = S.find_exercise(exercises, os.path.basename(p))
        except KeyError:
            continue
        if ex["job"] > 18:
            continue
        reps.append(qc_sheet(p, ex, ch, stage))
    return reps


# ------------------------------------------------------------------ backgrounds
def qc_bg(path, fmt, stage, horizon=None, span=0.8, floor_colour=True):
    """span = share of the width (centred) that must be flat in the stage strip; use 0.5 for outdoor scenes whose
    framing trees and rocks legitimately reach into the sides."""
    rep = Report(os.path.basename(path) + f"  ({fmt} background)")
    f = stage["format"][fmt]
    a = S.read_rgb(path).astype(int)
    h, w = a.shape[:2]
    rep.add(OK if [w, h] == f["size"] else FAIL, "size", f"{w}x{h}, expected {f['size'][0]}x{f['size'][1]}")
    s0, s1 = f["strip"]
    y0, y1 = int(s0 * h), int(s1 * h)
    xa, xb = int((1 - span) / 2 * w), int((1 + span) / 2 * w)
    strip = a[y0:y1, xa:xb]
    std = strip.reshape(-1, 3).std(0).max()
    rows = strip.mean(1).sum(1)
    seams = [y0 + i for i, j in enumerate(np.abs(np.diff(rows))) if j > 12]
    rep.add(OK if std <= 6 and not seams else FAIL, "stage strip flat",
            f"{int(s0 * 100)}-{int(s1 * 100)}% band, middle {int(span * 100)}% of width: colour spread {std:.1f} (pass <=6)"
            + (f", horizontal seam at rows {seams[:3]}" if seams else ", no seams"))
    mean = strip.reshape(-1, 3).mean(0)
    target = np.array(S.hex2rgb(stage["floor"]["hex"]))
    dev = np.abs(mean - target).max()
    if floor_colour:
        rep.add(OK if dev <= stage["floor"]["tol"] else WARN, "floor colour", f"strip mean #{int(mean[0]):02x}{int(mean[1]):02x}{int(mean[2]):02x} vs {stage['floor']['hex']} (max channel diff {dev:.0f})")
    mid = strip[:, int(.3 * w) - xa: int(.5 * w) - xa]
    mid_edges = (np.abs(np.diff(mid.sum(-1), axis=1)) > 45).mean()
    rep.add(OK if mid_edges <= 0.002 else FAIL, "middle of strip empty", f"edge density {mid_edges:.4f} (pass <=0.002)")
    pink = int(((a[..., 0] > 170) & (a[..., 2] > 150) & (a[..., 1] < 110)).sum())
    rep.add(OK if pink <= 50 else FAIL, "no pink/magenta", f"{pink} pink-ish pixels")
    if horizon is not None:
        col = a[:, int(.4 * w):int(.6 * w)].mean(1)
        d = np.abs(np.diff(col, axis=0)).sum(1)
        lo, hi = int((horizon - .10) * h), int((horizon + .10) * h)
        y = lo + int(np.argmax(d[lo:hi]))
        err = abs(y / h - horizon)
        rep.add(OK if err <= .02 else (WARN if err <= .04 else FAIL), "horizon", f"strongest centre edge at {y / h:.1%}, target {horizon:.0%} (error {err:.1%})")
    return rep


# ------------------------------------------------------------------ mats
def qc_mat(path, fmt, colour, stage):
    rep = Report(os.path.basename(path) + f"  ({fmt} {colour} mat)")
    a = S.read_rgb(path).astype(int)
    h, w = a.shape[:2]
    spec = stage["mat"][fmt]
    mag = np.array(S.hex2rgb(stage["magenta"]))
    d = np.abs(a - mag).sum(-1)
    near_not_exact = int(((d > 0) & (d <= 30)).sum())
    m = d > 0
    ys, xs = np.where(m)
    rep.add(OK if near_not_exact == 0 else FAIL, "background exact", f"{near_not_exact} near-magenta pixels that are not exactly #FF00FF")
    ny, nx0, nx1 = spec["near"]; fy, fx0, fx1 = spec["far"]
    box = (xs.min() / w, ys.min() / h, (xs.max() + 1) / w, (ys.max() + 1) / h)
    err = max(abs(box[0] - nx0), abs(box[2] - nx1), abs(box[1] - fy), abs(box[3] - ny))
    rep.add(OK if err <= 0.003 else (WARN if err <= 0.02 else FAIL), "position",
            f"box L{box[0]:.3f} T{box[1]:.3f} R{box[2]:.3f} B{box[3]:.3f} vs L{nx0} T{fy} R{nx1} B{ny} (worst error {err:.1%})")
    hexv = next(c for c in stage["mat_colour"] if c["name"] == colour)["top"]
    cy = int(((fy + ny) / 2) * h); cx = int(.5 * w)
    med = np.median(a[cy - 20:cy + 20, cx - 100:cx + 100].reshape(-1, 3), axis=0).astype(int)
    diff = np.abs(med - np.array(S.hex2rgb(hexv))).max()
    rep.add(OK if diff <= 3 else (WARN if diff <= 16 else FAIL), "colour", f"top surface #{med[0]:02x}{med[1]:02x}{med[2]:02x} vs {hexv} (max diff {diff})")
    return rep
