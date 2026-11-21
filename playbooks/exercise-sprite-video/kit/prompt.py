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


def build(spec, ch, reference=True):
    """reference=True: a character image is attached. reference=False: the first strip, the character described in words only."""
    N = ch.get("noun", "boy")
    n = len(spec["poses"]); words = {2: "TWO", 3: "THREE", 4: "FOUR", 5: "FIVE", 6: "SIX"}.get(n, str(n))
    layout = spec.get('layout', 'Same scale, all on the same invisible floor line, wide empty gaps so the figures never touch.')
    view = spec.get('view', ch['view'])
    if reference:
        lines = [
            f"Using the attached reference image ONLY for the character's appearance and art style ({ch['description']}). "
            "IGNORE the poses in the reference image completely.",
            "",
            f"Create a NEW wide {ch['generator']['aspect']} pose sheet of that same {N} doing {spec['exercise']}, shown {words} times left to right, {view}. {layout}",
        ]
    else:
        lines = [
            f"Generate a wide {ch['generator']['aspect']} character pose sheet for a fitness animation: ONE {N} shown {words} times, left to right, doing {spec['exercise']}, {view}. "
            f"This is a pose-by-pose animation reference, so all {words.lower()} figures must be the same character at the same scale. {layout}",
            "",
            f"CHARACTER (keep identical in every pose): {ch['description']}.",
        ]
    if spec.get("rule"): lines += ["", spec["rule"]]
    lines += ["", f"THE {words} POSES (official exercise, follow exactly):"] + [f"{i}. {p}" for i, p in enumerate(spec["poses"], 1)]
    if spec.get("far_side", True): lines += ["", ch["far_side"]]
    if ch.get("body_rules"): lines += ["", ch["body_rules"]]
    lines += ["", "BACKGROUND: " + ch["background"]]
    return "\n".join(lines)


def booklet_text(data, chart_id, slot):
    chart = next(c for c in data["charts"] if c["id"] == chart_id)
    i = {"ex1": 0, "ex2": 1, "ex3": 2, "ex4": 3, "run": 4, "jump": 4}[slot]; e = chart["exercises"][i]
    return {"name": e["name"], "start": e.get("start", ""), "movement": e.get("movement", ""), "notes": e.get("notes", [])}


def retake(spec, ch, individual=True):
    """A prompt for fixing a sheet that came back wrong: attach the bad sheet and a good character reference (and any schematic), name what was wrong, ask again.
    With 'rows', it asks for the same poses from several cameras on one image, so the best camera can be picked. individual=False leaves out the request for separate figure files."""
    r = spec.get("retake")
    if not r: return None
    N = ch.get("noun", "boy")
    poses = r.get("poses") or spec["poses"]; n = len(poses); words = {2: "TWO", 3: "THREE", 4: "FOUR", 5: "FIVE", 6: "SIX"}.get(n, str(n)); aspect = ch["generator"]["aspect"]; rows = r.get("rows")
    att = r["attach"]; names = {1: "ONE", 2: "TWO", 3: "THREE", 4: "FOUR"}
    L = [f"RETAKE. Attach {names.get(len(att), len(att))} images: " + "; ".join(f"({i}) {a}" for i, a in enumerate(att, 1)) + ".", "",
         f"Use image 2 ONLY for how the {N} looks (face, hair, skin tone, build, outline weight, shading, colors). Image 1 is a previous attempt at this exercise: do not copy its mistakes." + (f" Image 3 is {r['schematic']}" if len(att) > 2 and r.get("schematic") else ""), "",
         f"THE {N.upper()} (keep identical in every figure): {ch['description']}.", "", "WHAT WAS WRONG WITH THE PREVIOUS ATTEMPT (fix every one of these):"] + [f"- {x}" for x in r["problems"]] + ["", f"KEEP from the previous attempt: {r['keep']}", ""]
    layout = r.get("layout") or spec.get("layout", "Same scale, all on the same invisible floor line, wide empty gaps so the figures never touch.")
    if rows:
        L += [f"Create ONE NEW {aspect} image with {len(rows)} ROWS. Each row shows the same {N} doing {spec['exercise']} in the same {words} poses, left to right, in the same order, but from a different camera, so the best camera can be picked:"] + [f"ROW {i}: {v}." for i, v in enumerate(rows, 1)]
        L += ["", f"{layout} Same scale in every figure and every row, a wide empty gap between figures and a wide empty band between rows."]
    else:
        L += [f"Create a NEW wide {aspect} pose sheet of that same {N} doing {spec['exercise']}, shown {words} times left to right, {spec.get('view', ch['view'])}. {layout}"]
    if spec.get("rule"): L += ["", spec["rule"]]
    L += ["", f"THE {words} POSES (official exercise, follow exactly):"] + [f"{i}. {x}" for i, x in enumerate(poses, 1)]
    if spec.get("far_side", True): L += ["", ch["far_side"]]
    if ch.get("body_rules"): L += ["", ch["body_rules"]]
    L += ["", "BACKGROUND: " + ch["background"]]
    if individual: L += ["", "ALSO GIVE ME each figure as a separate transparent PNG at the original size, not resized, with a few pixels of empty margin, named by row and pose number."]
    return "\n".join(L)


def load_character(path=None):
    """The character to draw. Default config/character.json; override with --character PATH or SPRITE_CHARACTER=PATH,
    so a second character (config/characters/<name>.json) reuses every exercise spec unchanged."""
    path = path or os.environ.get("SPRITE_CHARACTER") or os.path.join(ROOT, "config", "character.json")
    ch = json.load(open(path)); ch.setdefault("noun", "boy"); return ch


# Rules that hold for every character and every exercise. Character-specific wording (clothes, face) stays in the character file.
UNIVERSAL = ("SPACING: the figures must not touch or overlap anywhere (hands, feet and hair included). The gap only has to be clear; "
             "it does not have to be any particular size, so do not shrink or squash a figure to make a bigger gap.")


def remake(spec, ch, attach, schematic_note=None):
    """A fresh take that leans on the plan's own drawing instead of a failed take.
    attach: list of (filename, role) in order, role one of 'character', 'booklet', 'schematic'.
    Why: attaching the bad sheet anchored the tool to its mistakes (batch C kept most of them), while the one
    job that got the form right (semi-squat jumps) had a position diagram attached."""
    N = ch.get("noun", "boy"); poses = spec["poses"]; n = len(poses); words = {2: "TWO", 3: "THREE", 4: "FOUR", 5: "FIVE", 6: "SIX"}.get(n, str(n))
    aspect = ch["generator"]["aspect"]; names = {1: "ONE", 2: "TWO", 3: "THREE"}
    roles = {"character": f"ONLY for how the {N} looks: face, hair, skin tone, build, clothes, outline weight, shading and colors. Ignore its pose completely.",
             "booklet": "the official drawing of this exercise from the original 1961 5BX booklet. Copy the BODY POSITIONS from it: where the head, hands, hips and feet are and how the body bends. Do NOT copy its drawing style (white silhouettes) and never add a second person.",
             "schematic": schematic_note or "a stick-figure diagram of WHERE the limbs are. Copy the positions only, never its style, colors or text."}
    L = [f"Attach {names.get(len(attach), len(attach))} images, in this order: " + "; ".join(f"({i}) {f}" for i, (f, _) in enumerate(attach, 1)) + ".", ""]
    L += [f"Image {i} is {roles[r]}" if r != "character" else f"Use image {i} {roles[r]}" for i, (_, r) in enumerate(attach, 1)]
    L += ["", f"THE {N.upper()} (keep identical in every figure): {ch['description']}.", ""]
    r = spec.get("retake") or {}
    if r.get("problems"): L += ["EARLIER ATTEMPTS GOT THESE WRONG (avoid every one):"] + [f"- {x}" for x in r["problems"]] + [""]
    L += [f"Create a NEW wide {aspect} pose sheet of that same {N} doing {spec['exercise']}, shown {words} times left to right, {(spec.get('remake') or {}).get('view') or spec.get('view', ch['view'])}. {spec.get('layout', '')}".rstrip()]
    if spec.get("rule"): L += ["", spec["rule"]]
    L += ["", f"THE {words} POSES (official exercise, follow exactly):"] + [f"{i}. {x}" for i, x in enumerate(poses, 1)]
    if spec.get("far_side", True): L += ["", ch["far_side"]]
    if ch.get("body_rules"): L += ["", ch["body_rules"]]
    L += ["", UNIVERSAL, "", "BACKGROUND: " + ch["background"]]
    if spec.get("check"): L += ["", "BEFORE YOU FINISH, CHECK THE SHEET AGAINST THIS LIST and redraw any figure that fails:"] + [f"- {x}" for x in spec["check"]]
    return "\n".join(L)


def publish_all(data, out_md, out_json):
    """One file with every prompt, the character, the settings and what was learned: usable with any image tool."""
    ch = load_character(); sp = json.load(open(os.path.join(ROOT, "prompts", "strips.json")))
    reg = json.load(open(os.path.join(ROOT, "config", "strips.json"))); edits = json.load(open(os.path.join(ROOT, "prompts", "edits.json")))
    items = []
    for key, spec in sorted(sp["strips"].items(), key=lambda kv: (kv[1].get("chart", 1), ["ex1", "ex2", "ex3", "ex4", "run", "jump"].index(kv[1].get("slot", "ex1")))):
        reg_entry = reg["strips"].get(key); has_image = bool(reg_entry) and os.path.exists(os.path.join(ROOT, "sheets", reg_entry["file"]))
        b = booklet_text(data, spec.get("chart", 1), spec.get("slot", "ex1")) if data else None
        items.append({"key": key, "chart": spec.get("chart", 1), "slot": spec.get("slot"), "exercise": spec["exercise"], "image": has_image,
                      "file": reg_entry["file"] if reg_entry else spec.get("suggest", {}).get("file", ""), "poses": len(spec["poses"]), "kept": spec.get("kept", ""),
                      "booklet": b, "check": spec.get("check", []), "draft": spec.get("draft", []), "learned": spec.get("learned", []),
                      "prompt_with_reference": build(spec, ch, True), "prompt_first_strip": build(spec, ch, False),
                      "retake": retake(spec, ch), "retake_why": (spec.get("retake") or {}).get("why_rows", "")})
    json.dump({"character": ch, "generation": sp["_generation"], "strips": items, "edits": edits["edits"]}, open(out_json, "w"), indent=1, ensure_ascii=False)
    g = sp["_generation"]; L = ["# Prompts for every strip", "",
        "Everything needed to make these strips in **any** image tool. Generated by `kit/prompt.py --all`; do not edit by hand (edit `prompts/strips.json` and `config/character.json`, then regenerate).", "",
        "Read `docs/HOW-TO-GENERATE-STRIPS.md` first for the method. This file is the paste-ready text.", "",
        "## Settings that worked", "", f"- **Model:** {g['model']} (ElevenLabs). Any image model that accepts a reference image should be able to follow the same text; results will differ.",
        f"- **Shape:** {g['aspect']}, {g['resolution']}. **Takes:** {g['variations']} per strip, then pick one.", f"- **Reference:** {g['reference']}",
        f"- **Cost then:** {g['credits_each']}", f"- **Order used:** {'; '.join(g['order'])}", "",
        "## The character, in words", "", ch["description"] + ".", "", "Locked: " + " ".join(ch["locked"]), "",
        "## The background, in words", "", ch["background"], "", "## How the far-side shading is asked for", "", ch["far_side"], ""]
    for it in items:
        L += ["---", "", f"## Chart {it['chart']}: {it['exercise'].title() if it['exercise'].isupper() else it['exercise']}  (`{it['key']}`, {it['poses']} poses)", ""]
        if it["booklet"]:
            bk = it["booklet"]; L += ["**What the plan says** (the booklet's own wording, from the 5BX data file):", "", f"- Starts: {bk['start']}", f"- Movement: {bk['movement']}"] + [f"- Note: {n}" for n in bk["notes"]] + [""]
        L += [f"**Status:** {it['kept']}" if not it["image"] else f"**Kept:** {it['kept']}", ""]
        if it["check"]: L += ["**Check before you keep a take:**", ""] + [f"- {x}" for x in it["check"]] + [""]
        if it["draft"]: L += ["**My decisions to check [DRAFT]:**", ""] + [f"- {x}" for x in it["draft"]] + [""]
        L += ["**Prompt, with a character reference attached:**", "", "```text", it["prompt_with_reference"], "```", "",
              "**Prompt for the very first strip (no reference, character in words):**", "", "```text", it["prompt_first_strip"], "```", ""]
        if it["retake"]: L += ["**Retake prompt (the sheet came back wrong; attach the bad sheet and a character reference):**", ""] + ([it["retake_why"], ""] if it["retake_why"] else []) + ["```text", it["retake"], "```", ""]
        if it["learned"]: L += ["**What went wrong, and the fix:**", ""] + [f"- {x}" for x in it["learned"]] + [""]
    L += ["---", "", "## Edit prompts (change one thing, keep the rest)", "", "Used with the ElevenLabs edit tool (gpt-image-2.5-sunburst), the strip passed as the reference. About 433 credits a take.", ""]
    for e in edits["edits"]: L += [f"### {e['target']}", "", f"**Problem:** {e['problem']}", "", "```text", e["prompt"], "```", "", f"**Result:** {e['result']}", ""]
    open(out_md, "w", encoding="utf-8").write("\n".join(L) + "\n")
    print(f"wrote {out_md} and {out_json} ({len(items)} strips, {len(edits['edits'])} edit prompts)")


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
    ap.add_argument("--strip"); ap.add_argument("--booklet", action="store_true"); ap.add_argument("--first", action="store_true", help="with --strip: the no-reference version for a character's first strip")
    ap.add_argument("--all", action="store_true", help="write prompts/PROMPTS.md and prompts/prompts.json (everything, for any image tool)")
    ap.add_argument("--data"); ap.add_argument("--chart", type=int, default=1); ap.add_argument("--slot", default="ex1")
    ap.add_argument("--character", help="character file (default config/character.json, or $SPRITE_CHARACTER)")
    a = ap.parse_args()
    if a.all:
        publish_all(json.load(open(a.data)) if a.data else None, os.path.join(ROOT, "prompts", "PROMPTS.md"), os.path.join(ROOT, "prompts", "prompts.json"))
    elif a.booklet:
        if not a.data: sys.exit("--booklet needs --data")
        booklet(json.load(open(a.data)), a.chart, a.slot)
    else:
        specs = json.load(open(os.path.join(ROOT, "prompts", "strips.json")))["strips"]
        if a.strip not in specs: sys.exit(f"unknown strip '{a.strip}'. Known: {', '.join(specs)}")
        print(build(specs[a.strip], load_character(a.character), reference=not a.first))
