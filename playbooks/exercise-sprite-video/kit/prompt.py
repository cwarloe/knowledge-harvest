#!/usr/bin/env python3
"""Make the image prompt for one exercise strip, so a new strip is the same boy and the same rules.

  # 1. Pull the booklet's own words for an exercise (to base the pose list on):
  python3 kit/prompt.py --booklet --data 5bx-charts.json --chart 2 --slot ex3

  # 2. Add an entry to prompts/strips.json (exercise name, pose list, what must NOT happen), then:
  python3 kit/prompt.py --strip alternate-leg-raise-c1

The character, view, far-side shading and background wording come from config/character.json,
so changing the boy changes every future prompt. Pose lists are written by a person (or an agent
and then checked): they are the part that decides whether the form is right.
"""
import argparse, json, os, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def build(spec, ch):
    n = len(spec["poses"]); words = {2: "TWO", 3: "THREE", 4: "FOUR", 5: "FIVE", 6: "SIX"}.get(n, str(n))
    lines = [
        f"Using the attached reference image ONLY for the character's appearance and art style ({ch['description']}). "
        "IGNORE the poses in the reference image completely.",
        "",
        f"Create a NEW wide {ch['generator']['aspect']} pose sheet of that same boy doing {spec['exercise']}, shown {words} times left to right, "
        f"{ch['view']}. {spec.get('layout', 'Same scale, all on the same invisible floor line, wide empty gaps so the figures never touch.')}",
    ]
    if spec.get("rule"): lines += ["", spec["rule"]]
    lines += ["", f"THE {words} POSES (official exercise, follow exactly):"] + [f"{i}. {p}" for i, p in enumerate(spec["poses"], 1)]
    lines += ["", ch["far_side"], "", "BACKGROUND: " + ch["background"]]
    return "\n".join(lines)


def booklet(data, chart_id, slot):
    chart = next(c for c in data["charts"] if c["id"] == chart_id)
    i = {"ex1": 0, "ex2": 1, "ex3": 2, "ex4": 3, "run": 4, "jump": 4}[slot]; e = chart["exercises"][i]
    print(f"chart {chart_id}, exercise {e['n']}: {e['name']}")
    print(f"  start:    {e.get('start', '')}\n  movement: {e.get('movement', '')}")
    for note in e.get("notes", []): print(f"  note:     {note}")
    print("\nWrite one pose per visible stage. Add a 'must NOT' line for the common error (knees bent, hips piked,\n"
          "hands behind head...). Pose counts in chart 1: 3 each, 4 for the run and the jumps.")


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--strip"); ap.add_argument("--booklet", action="store_true")
    ap.add_argument("--data"); ap.add_argument("--chart", type=int, default=1); ap.add_argument("--slot", default="ex1")
    a = ap.parse_args()
    if a.booklet:
        if not a.data: sys.exit("--booklet needs --data")
        booklet(json.load(open(a.data)), a.chart, a.slot)
    else:
        specs = json.load(open(os.path.join(ROOT, "prompts", "strips.json")))["strips"]
        if a.strip not in specs: sys.exit(f"unknown strip '{a.strip}'. Known: {', '.join(specs)}")
        print(build(specs[a.strip], json.load(open(os.path.join(ROOT, "config", "character.json")))))
