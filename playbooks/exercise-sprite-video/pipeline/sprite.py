#!/usr/bin/env python
"""One command for the whole line.

  python sprite.py list
  python sprite.py prompts  --character boy [--exercises all|slug,job,...] [--mode fresh|fix] --out batch.md
                            [--bundle DIR --refs REFS_DIR --sheets SHEETS_DIR]
  python sprite.py checklist --character boy [--exercises all|...] --out review.md
  python sprite.py stage    --format wide --scene forest --out stage.md
  python sprite.py qc sheet FILE [--exercise slug|job] --character boy
  python sprite.py qc sheets FOLDER --character boy
  python sprite.py qc bg    FILE --format wide|tall [--horizon 0.56]
  python sprite.py qc mat   FILE --format wide|tall --colour teal|navy
  python sprite.py cut      FILE [--exercise slug|job] --out DIR
  python sprite.py mats     --out DIR [--tall-room PNG] [--wide-room PNG]
"""
import argparse, sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import sheetlib as S


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("list")
    p = sub.add_parser("prompts"); p.add_argument("--character", default="boy"); p.add_argument("--exercises", default="all")
    p.add_argument("--mode", choices=["fresh", "fix"], default="fresh"); p.add_argument("--out", required=True)
    p.add_argument("--bundle"); p.add_argument("--refs"); p.add_argument("--sheets")
    p = sub.add_parser("checklist"); p.add_argument("--character", default="boy"); p.add_argument("--exercises", default="all"); p.add_argument("--out", required=True)
    p = sub.add_parser("stage"); p.add_argument("--format", default="wide"); p.add_argument("--scene", default="forest"); p.add_argument("--out", required=True)
    p = sub.add_parser("qc"); p.add_argument("what", choices=["sheet", "sheets", "bg", "mat"]); p.add_argument("path")
    p.add_argument("--character", default="boy"); p.add_argument("--exercise"); p.add_argument("--format", default="wide")
    p.add_argument("--horizon", type=float); p.add_argument("--colour", default="teal")
    p.add_argument("--span", type=float, default=0.8, help="bg: share of width the stage strip must be flat over (0.5 for outdoor scenes)")
    p.add_argument("--no-floor-colour", action="store_true", help="bg: skip the grey-floor colour check (outdoor scenes)")
    p = sub.add_parser("cut"); p.add_argument("path"); p.add_argument("--exercise"); p.add_argument("--out", required=True)
    p = sub.add_parser("mats"); p.add_argument("--out", required=True); p.add_argument("--tall-room"); p.add_argument("--wide-room")
    a = ap.parse_args(argv)

    exs = S.load_exercises()
    if a.cmd == "list":
        for e in exs:
            q = e["qc"]
            print(f"JOB-{e['job']:02d}  {e['id']:<34} {len(e['poses'])} poses, {q['rows']} row(s)  [{e['view']}]")
        return 0
    if a.cmd == "prompts":
        import gen
        n = gen.build_batch(a.character, a.exercises, a.mode, a.out, a.bundle, a.refs, a.sheets)
        print(f"wrote {a.out}: {n} job(s), character '{a.character}', mode {a.mode}")
        return 0
    if a.cmd == "checklist":
        import gen
        n = gen.review_checklist(a.exercises, a.character, a.out)
        print(f"wrote {a.out}: {n} checklist(s)")
        return 0
    if a.cmd == "stage":
        import gen
        gen.stage_prompt(a.format, a.scene, a.out)
        print("wrote", a.out)
        return 0
    if a.cmd == "qc":
        import qc
        stage = S.load_stage()
        if a.what == "sheet":
            ch = S.load_character(a.character)
            ex = S.find_exercise(exs, a.exercise or os.path.basename(a.path))
            reps = [qc.qc_sheet(a.path, ex, ch, stage)]
        elif a.what == "sheets":
            reps = qc.qc_sheets_dir(a.path, S.load_character(a.character), stage, exs)
        elif a.what == "bg":
            reps = [qc.qc_bg(a.path, a.format, stage, a.horizon, a.span, not a.no_floor_colour)]
        else:
            reps = [qc.qc_mat(a.path, a.format, a.colour, stage)]
        for r in reps:
            r.show()
        tally = {k: sum(1 for r in reps if r.worst == k) for k in (qc.OK, qc.WARN, qc.FAIL)}
        print(f"\nSUMMARY: {tally[qc.OK]} pass, {tally[qc.WARN]} warn, {tally[qc.FAIL]} fail of {len(reps)}")
        return 1 if tally[qc.FAIL] else 0
    if a.cmd == "cut":
        import cut
        ex = S.find_exercise(exs, a.exercise or os.path.basename(a.path))
        m = cut.cut_sheet(a.path, ex, a.out)
        print(f"cut {len(m['sprites'])} sprite(s) into {a.out}")
        return 0
    if a.cmd == "mats":
        import mats
        names = mats.draw_all(a.out, {"tall": a.tall_room, "wide": a.wide_room})
        print("wrote", ", ".join(names))
        return 0


if __name__ == "__main__":
    sys.exit(main())
