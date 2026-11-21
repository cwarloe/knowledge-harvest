"""Prompt generator: character + exercise library + learned rules (+ optional fixes) -> paste-ready batch."""
import os, re, shutil, zipfile
import sheetlib as S

PRONOUNS = {
    "he": dict(his="his", His="His", HIS="HIS", him="him", he="he", He="He", himself="himself"),
    "she": dict(his="her", His="Her", HIS="HER", him="her", he="she", He="She", himself="herself"),
}


def tokenize(s):
    """Turn literal 'boy', 'he', 'his'... in free text into tokens so any character can be substituted."""
    s = re.sub(r"\bthe boy's\b", "the {noun}'s", s)
    s = re.sub(r"\bthe boy\b", "the {noun}", s)
    s = re.sub(r"\bboy\b", "{noun}", s)
    for w, t in [("himself", "himself"), ("his", "his"), ("His", "His"), ("HIS", "HIS"), ("him", "him"), ("he", "he"), ("He", "He")]:
        s = re.sub(rf"\b{w}\b", "{" + t + "}", s)
    return s


def fill(s, ch):
    d = dict(PRONOUNS[ch["pronouns"]])
    d["noun"] = ch["noun"]
    s = s.strip()
    for k, v in d.items():
        s = s.replace("{" + k + "}", v)
    return s


def appearance(ch):
    return (f"a {ch['age']} {ch['noun']}: {ch['hair']}, {ch['skin']}, {ch['face']}, {ch['build']}. "
            f"{ch['outfit']} {ch['art_style']}").rstrip(".")


def tags(ex):
    """Which learned rules apply: 'all' plus the explicit tags in exercises.toml (jump, lying, touch, front, multirow)."""
    return {"all"} | set(ex.get("tags", []))


def sprite_prompt(ex, ch, rules, stage, fix=None):
    """Return (prompt_text, attach_list)."""
    magenta = stage["magenta"]
    ref = ch["reference_image"]
    attach = []
    out = []
    n_img = 1
    if fix:
        attach.append(fix["base"])
        out.append(f"RETAKE. Attach images: (1) the previous sheet to fix: {fix['base']}; (2) the character reference: {ref}"
                   + (f"; (3) the schematic: {ex['schematic_file']}." if ex.get("schematic_file") else ".") + "\n")
        out.append(f"Use image 2 ONLY for how the {ch['noun']} looks (face, hair, skin tone, build, outline weight, shading, colors). "
                   f"Image 1 is a previous attempt at this exercise: keep what it did right and do not copy its mistakes.\n")
        attach.append(ref)
        if ex.get("schematic_file"):
            attach.append(ex["schematic_file"])
            out.append(f"Image 3 is {ex['schematic_note']}\n")
        out.append("WHAT TO FIX:\n" + fill(tokenize(fix["text"]), ch) + "\n")
    else:
        attach.append(ref)
        out.append(f"Using the attached reference image ONLY for the character's appearance and art style ({appearance(ch)}). "
                   f"IGNORE the poses in the reference image completely.\n")
        if ex.get("layout_ref"):
            attach.append(ex["layout_ref"])
            out.append(f"A SECOND attached image, {ex['layout_ref']}, shows a similar movement from a similar camera: use it ONLY for the layout "
                       f"(how the figures are arranged, which way they face and how big the gaps are), never for the pose, the appearance or its mistakes.\n")
        if ex.get("schematic_file"):
            attach.append(ex["schematic_file"])
            out.append(f"A further attached image, {ex['schematic_file']}, is {ex['schematic_note']}\n")
    out.append(fill(ex["layout"], ch) + "\n")
    for x in ex.get("extra", []):
        out.append(fill(x, ch) + "\n")
    if fix and ex.get("keep"):
        out.append("KEEP FROM THE PREVIOUS ATTEMPT: " + fill(ex["keep"], ch) + "\n")
    out.append(f"THE {len(ex['poses'])} POSES (official exercise, follow exactly):")
    for i, p in enumerate(ex["poses"], 1):
        out.append(f"{i}. {p['label']}: {fill(p['text'], ch)}")
    out.append("")
    if ex.get("key_rule"):
        out.append(fill(ex["key_rule"], ch) + "\n")
    out.append(f"BODY AND FACE RULES (every figure): exactly TWO arms and TWO legs, so count the limbs in every figure before you finish "
               f"and never draw a third arm or leg; {ch['garment_rule']}; {fill(ch['face_rule'], ch)}; "
               f"the back straight in standing and crouching poses; {ch['feet_rule']}.\n")
    t = tags(ex)
    applicable = [r for r in rules if r["when"] in t]
    if applicable:
        out.append("ALSO (lessons from earlier runs):")
        for r in applicable:
            out.append(f"- {fill(r['text'], ch)}")
        out.append("")
    if ex.get("pitfalls") and not fix:
        out.append("MISTAKES MADE IN EARLIER ATTEMPTS AT THIS EXERCISE (do not repeat them):")
        for p in ex["pitfalls"]:
            out.append(f"- {fill(p, ch)}")
        out.append("")
    out.append(f"BACKGROUND: perfectly flat solid magenta ({magenta}), nothing else. No ground shadow, no floor line, no scenery, "
               f"no gradient, no text, labels, numbers or arrows.")
    return "\n".join(out), attach


def build_batch(character, exercise_ids, mode, out_path, bundle=None, refs=None, sheets=None):
    ch = S.load_character(character)
    exs = S.load_exercises()
    rules = S.load_toml(os.path.join(S.HERE, "rules.toml"))["rule"]
    stage = S.load_stage()
    fixes = {}
    fp = os.path.join(S.HERE, "fixes.toml")
    if os.path.exists(fp):
        fixes = {f["exercise"]: f for f in S.load_toml(fp)["fix"]}
    sel = exs if exercise_ids in (None, "all") else [S.find_exercise(exs, k) for k in exercise_ids.split(",")]
    if mode == "fix":
        sel = [e for e in sel if e["id"] in fixes]
    head = [f"# Sprite batch: {ch['name']} ({mode} mode)\n",
            "How to use: attach the files listed under ATTACH for each job, then paste the job. Everything below the line is the prompt.\n", "---\n",
            "Please do ALL of the jobs below, in order, by yourself, without asking me any questions. Give each result the label JOB-NN and show me the whole image. "
            "If a job cannot be done, say so in one line and continue. At the end list the finished and unfinished job numbers.\n"]
    body, manifest = [], {}
    for e in sel:
        fx = fixes.get(e["id"]) if mode == "fix" else None
        text, attach = sprite_prompt(e, ch, rules, stage, fx)
        body.append(f"=== JOB-{e['job']:02d}: {e['title']} ===\nATTACH: {', '.join(attach)}\nPRODUCE: ONE image: the whole sheet (all rows, all poses). No separate figures.\nPROMPT:\n{text}\n")
        manifest[e["job"]] = attach
    md = "\n".join(head + body)
    with open(out_path, "w", encoding="utf-8", newline="\n") as f:
        f.write(md)
    if bundle:
        make_bundle(bundle, manifest, refs, sheets, out_path)
    return len(sel)


def make_bundle(bundle, manifest, refs, sheets, md_path):
    """Per-job folders of exactly the files each job needs, plus a zip. Missing files are reported, not fatal."""
    os.makedirs(bundle, exist_ok=True)
    missing = []
    for job, files in manifest.items():
        d = os.path.join(bundle, f"JOB-{job:02d}")
        os.makedirs(d, exist_ok=True)
        for fn in files:
            found = None
            for base in (refs, sheets):
                if base and os.path.exists(os.path.join(base, fn)):
                    found = os.path.join(base, fn)
                    break
            if found:
                shutil.copy(found, d)
            else:
                missing.append(f"JOB-{job:02d}/{fn}")
    shutil.copy(md_path, bundle)
    zp = bundle.rstrip("\\/") + ".zip"
    with zipfile.ZipFile(zp, "w", zipfile.ZIP_DEFLATED) as z:
        for root, _, fs in os.walk(bundle):
            for fn in fs:
                p = os.path.join(root, fn)
                z.write(p, os.path.relpath(p, bundle))
    print(f"bundle: {bundle} -> {zp} ({os.path.getsize(zp)/1e6:.1f} MB)")
    if missing:
        print("MISSING attachments (supply them with --refs / --sheets):")
        for m in missing:
            print("  ", m)


def review_checklist(exercise_ids, character, out_path):
    """The human half of QC: one tick-box sheet per exercise built from the pose text and the learned rules,
    so every reviewer asks the same questions (reduces the variation between reviewers)."""
    ch = S.load_character(character)
    exs = S.load_exercises()
    rules = S.load_toml(os.path.join(S.HERE, "rules.toml"))["rule"]
    sel = exs if exercise_ids in (None, "all") else [S.find_exercise(exs, k) for k in exercise_ids.split(",")]
    out = ["# Pose review checklist", "",
           "Run `sprite.py qc sheet` first (it covers background, spacing, floor line, lift and palette). "
           "This list covers what a script cannot see. Tick every box; any unticked box = retake, and log it in LESSONS.md.", ""]
    for e in sel:
        out.append(f"## JOB-{e['job']:02d} {e['title']}  ({e['id']})")
        out.append("")
        out.append(f"- [ ] Camera is {e['view']}, the same in every figure of a row")
        for i, p in enumerate(e["poses"], 1):
            out.append(f"- [ ] Pose {i} {p['label']}: " + fill(p["text"], ch).replace("\n", " "))
        if e.get("key_rule"):
            out.append("- [ ] " + fill(e["key_rule"], ch).replace("\n", " "))
        out.append("- [ ] Exactly two arms and two legs in every figure (count the hidden far-side limbs too)")
        for r in rules:
            if r["when"] in tags(e) and r["id"] in ("R-CONTACT", "R-FLAT", "R-FRONT", "R-LIFT"):
                out.append(f"- [ ] ({r['id']}) " + fill(r["text"], ch))
        for p in e.get("pitfalls", []):
            out.append(f"- [ ] Not repeated: " + fill(p, ch).replace("\n", " "))
        out.append("")
    with open(out_path, "w", encoding="utf-8", newline="\n") as fh:
        fh.write("\n".join(out))
    return len(sel)


def stage_prompt(fmt, scene_id, out_path):
    stage = S.load_stage()
    f = stage["format"][fmt]
    scene = next(s for s in stage["scene"] if s["id"] == scene_id)
    W, H = f["size"]
    s0, s1 = f["strip"]
    feet = f["feet_line"]
    hz = scene["horizon"]
    txt = f"""Create ONE complete {fmt} {W}x{H} background scene for a cartoon fitness video: {scene['summary']}. No characters, no people, no animals, no text, no frame, no border.

THE STAGE (very important): a cartoon figure about {int(f['character_height']*100)}% of the image height will be pasted on top, standing with the feet on an invisible line {int(feet*100)}% down from the top, in the middle. Keep the strip from {int(s0*100)}% to {int(s1*100)}% down the image completely flat, smooth and empty (no rocks, plants, lines or shadows bigger than a pebble). Keep the middle third of the image calm, with lower contrast and no strong shapes, so the silhouette reads clearly; put the interest and detail in the left and right thirds.

HORIZON: ONE horizon line exactly {int(hz*100)}% down from the top ({round(hz*H)} px on a {H} px high image), shared by every layer; the ground's top edge sits on that line. Last time the horizon came out 2 to 6 points too low, so place it carefully.

Do not use pink, magenta or saturated purple anywhere. All edges crisp: no glow, feathering or blur."""
    with open(out_path, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(txt + "\n")
    return txt
