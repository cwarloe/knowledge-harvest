#!/usr/bin/env python3
"""Build an unattended batch for an image tool: one folder with every reference file, and paste-ready requests that list the jobs in priority order.

  python3 kit/make_batch.py --out batches/2026-11-20            # writes BATCH-A-sprites.md, BATCH-B-backgrounds.md, refs/, jobs.json
The prompts come from prompts/strips.json (retake and first-draw prompts) and prompts/backgrounds.json, so they cannot drift from the kit.
Each job names the exact files to attach (the files in refs/ keep these names), what to produce, and the name to give it.

  python3 kit/make_batch.py --out batches/2026-11-21-D --remake scissor-jumps-c1,back-extension-c2,chin-forehead-push-up-c3
builds a remake batch instead: each job attaches the character, the booklet drawing and a diagram (never the failed take),
plus one ALL-REFS image per job for tools that accept a single attachment. Add --character config/characters/NAME.json for another character.
"""
import argparse, json, os, re, shutil, sys

HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE); sys.path.insert(0, HERE)
import prompt as P
USER_SUPPLIED = ["bg-mountain-v1.png"]      # files only the author has: they add them to the refs folder by hand
CH = "c4-run-knees-waist-high.png"       # the character reference: the best sheet we have for how the boy looks

# where each reference lives in the repo
REFS = {"c4-run-knees-waist-high.png": "sheets", "c4-jump-semi-squat-jumps.png": "sheets", "c4-ex2-sit-up-toe-touch.png": "sheets", "c4-ex3-back-extension-arms-sideways.png": "sheets", "c4-ex4-wide-hand-push-up.png": "sheets",
        "c3-ex1-toe-touching.png": "sheets", "c3-ex234-sit-back-push.png": "sheets", "c3-jump-half-knee-bends.png": "sheets", "c2-ex3-back-extension.png": "sheets", "c2-jump-astride-jumps.png": "sheets",
        "ex5-stationary-run.png": "sheets", "ex5-scissor-jumps.png": "sheets", "REF-footswitch.png": "prompts/refs", "REF-backext-geometry.png": "prompts/refs", "REF-scissor-stances.png": "prompts/refs", "REF-backext-hands.png": "prompts/refs",
        "bg-keeper-gym-landscape-v1.png": "library/backgrounds", "bg-cand-arcade-landscape.png": "library/backgrounds", "bg-cand-loft-landscape.png": "library/backgrounds", "bg-cand-workshop-landscape.png": "library/backgrounds"}

# first-draw jobs: a layout-only second reference of a similar movement
LAYOUT = {"toe-touch-circle-c4": "c3-ex1-toe-touching.png", "toe-touch-clasped-c5": "c3-ex1-toe-touching.png", "toe-touch-reverse-clasp-c6": "c3-ex1-toe-touching.png",
          "pike-sit-up-c6": "c4-ex2-sit-up-toe-touch.png", "back-extension-arms-overhead-c5": "c2-ex3-back-extension.png", "back-extension-press-c6": "c2-ex3-back-extension.png",
          "clap-push-up-c5": "c4-ex4-wide-hand-push-up.png", "chest-slap-push-up-c6": "c4-ex4-wide-hand-push-up.png", "semi-spread-eagle-jumps-c5": "c2-jump-astride-jumps.png", "jack-jumps-c6": "c3-jump-half-knee-bends.png"}
SPRITE_JOBS = [("semi-squat-jumps-c4", "retake", "Chart 4 semi-squat jumps (retake)"), ("toe-touch-circle-c4", "first", "Chart 4 toe touch with circle bend (first draw)"),
               ("sit-up-toe-touch-c4", "retake", "Chart 4 sit-up toe touch (retake: arms against the head)"), ("back-extension-arms-sideways-c4", "retake", "Chart 4 back extension, arms sideways (retake, three cameras)"),
               ("chin-forehead-push-up-c3", "retake", "Chart 3 chin-forehead push-up (retake, two cameras)"), ("back-extension-c2", "retake", "Chart 2 back extension (retake: both thighs clear the hands)"),
               ("stationary-run-c1", "retake", "Chart 1 stationary run (retake: feet only 4 inches up)"), ("scissor-jumps-c1", "retake", "Chart 1 scissor jumps (retake, two cameras)"),
               ("toe-touch-clasped-c5", "first", "Chart 5 toe touch, hands clasped"), ("sit-up-twist-c5", "first", "Chart 5 sit-up with a twist"), ("back-extension-arms-overhead-c5", "first", "Chart 5 back extension, arms overhead"),
               ("clap-push-up-c5", "first", "Chart 5 clap push-up"), ("semi-spread-eagle-jumps-c5", "first", "Chart 5 semi-spread eagle jumps"), ("toe-touch-reverse-clasp-c6", "first", "Chart 6 toe touch, reverse clasp"),
               ("pike-sit-up-c6", "first", "Chart 6 pike sit-up"), ("back-extension-press-c6", "first", "Chart 6 back extension with a press"), ("chest-slap-push-up-c6", "first", "Chart 6 chest-slap push-up"), ("jack-jumps-c6", "first", "Chart 6 jack jumps")]


def attach_of(spec, kind, key):
    if kind == "retake": return [a.split(": ", 1)[1].split(" (")[0] for a in spec["retake"]["attach"]]
    return [CH] + ([LAYOUT[key]] if key in LAYOUT else [])


def sprite_jobs(ch, strips):
    out = []
    for key, kind, title in SPRITE_JOBS:
        spec = strips[key]
        if kind == "retake": prompt = P.retake(spec, ch, individual=False)
        else:
            prompt = P.build(spec, ch, True)
            if key in LAYOUT: prompt = prompt.replace("Create a NEW wide", f"A SECOND attached image, {LAYOUT[key]}, shows a similar movement from a similar camera: use it ONLY for the layout (how the figures are arranged, which way they face and how big the gaps are), never for the pose, the appearance or its mistakes.\n\nCreate a NEW wide", 1)
        out.append({"title": title, "attach": attach_of(spec, kind, key), "prompt": prompt, "strip": key, "kind": kind, "output": "ONE image: the whole sheet (all rows, all poses). No separate figures."})
    return out


def background_jobs(bg):
    L, Pt = bg["formats"]["landscape"], bg["formats"]["portrait"]; gk, gp, cd, fo = L["gym-keeper"]["items"], Pt["gym-keeper"]["items"], L["candidates"]["items"], L["forest"]["items"][0]
    K = "bg-keeper-gym-landscape-v1.png"; J = []
    J.append(("Gym: tall phone version of the room", [K], gp[0]["prompt"], "bg-gym-portrait-final.png"))
    J.append(("Gym: floor mat overlay, muted teal, wide", [K], gk[1]["prompt"], "bg-gym-landscape-mat-teal.png")); J.append(("Gym: floor mat overlay, deep navy, wide", [K], gk[2]["prompt"], "bg-gym-landscape-mat-navy.png"))
    J.append(("Gym: floor mat overlay, muted teal, tall", ["(your own output of the 'tall phone version' job)"], gp[1]["prompt"], "bg-gym-portrait-mat-teal.png")); J.append(("Gym: floor mat overlay, deep navy, tall", ["(your own output of the 'tall phone version' job)"], gp[2]["prompt"], "bg-gym-portrait-mat-navy.png"))
    J.append(("Arcade lounge rework", ["bg-cand-arcade-landscape.png"], cd[0]["prompt"], "bg-arcade-landscape-final.png")); J.append(("Brick loft rework", ["bg-cand-loft-landscape.png"], cd[1]["prompt"], "bg-loft-landscape-final.png"))
    J.append(("Workshop rework", ["bg-cand-workshop-landscape.png"], cd[2]["prompt"], "bg-workshop-landscape-final.png"))
    J.append(("Pine forest master scene (the outdoor option; make 4 variations)", [], fo["prompt"], "bg-forest-landscape-master.png"))
    J.append(("Mountain meadow rework (attach YOUR mountain image)", ["bg-mountain-v1.png"], cd[3]["prompt"], "bg-mountain-landscape-final.png"))
    J.append(("OPTIONAL, lowest priority: gym finishing pass (plain centre window). Accept only if everything else is preserved exactly", [K], gk[0]["prompt"], "bg-gym-landscape-final.png"))
    return [{"title": t, "attach": a, "prompt": p, "output": f"ONE image named {o}" if "master" not in o else "FOUR variations of the master scene"} for t, a, p, o in J]


def remake_jobs(ch, strips, keys):
    """Fresh takes for the listed strips, each with at most three attachments (character, booklet drawing, diagram),
    which every current tool accepts (Grok Imagine edits take 3 to 5 images, ChatGPT more). The failed take is NOT attached."""
    out = []
    for key in keys:
        spec = strips[key]; r = spec.get("remake") or {}
        att = [(CH, "character")] + ([(r["booklet"], "booklet")] if r.get("booklet") else []) + ([(r["schematic"], "schematic")] if r.get("schematic") else [])
        name = re.sub(r"^(a|an) ", "", spec["exercise"].split(" (")[0], flags=re.I).lower(); title = f"Chart {spec.get('chart', '?')} {name} (remake from the booklet)"
        out.append({"title": title, "attach": [f for f, _ in att], "prompt": P.remake(spec, ch, att, r.get("schematic_note")), "strip": key, "kind": "remake",
                    "output": "ONE image: the whole sheet. No separate figures."})
    return out


def composite(files, dst, height=700, gap=40):
    """All of a job's references side by side in ONE image, for a tool or chat that takes a single attachment.
    No labels (they leak into the output); the prompt says which panel is which, left to right."""
    from PIL import Image
    ims = [Image.open(f).convert("RGB") for f in files]
    ims = [im.resize((max(1, round(im.width * height / im.height)), height)) for im in ims]
    out = Image.new("RGB", (sum(i.width for i in ims) + gap * (len(ims) + 1), height + 2 * gap), (255, 255, 255)); x = gap
    for im in ims: out.paste(im, (x, gap)); x += im.width + gap
    out.save(dst)


INTRO = """I am attaching {n} reference files. Each is named exactly as it is called in the jobs below. Please do ALL of the jobs below, in order, by yourself, without asking me any questions. I will be asleep.

RULES FOR EVERY JOB
- Use ONLY the files named in that job's ATTACH line.
- The character reference shows how the boy looks. Follow its face, hair, skin tone, build, outline weight, shading and colors in every figure.
- Give each result the label JOB-NN (the job number) so I can tell them apart. Show me the whole image for each job. {sheets}
- If a job cannot be done, say so in one line and carry on with the next one. Never merge two jobs into one image.
- Count the limbs in every figure before you finish a job: exactly two arms and two legs.
- Do not stop to summarize between jobs. At the very end, list the job numbers you finished and the ones you could not.

{kind}
"""


def render(jobs, title, intro, start, refs_used, refs, extra=()):
    L = [f"# {title}", "", f"How to use this: attach EVERY file in the `{refs}` folder ({len(refs_used)} files) to ONE message, then paste everything below the line." + ("" if not extra else " BEFORE you attach, copy " + " and ".join(f"YOUR file {e}" for e in extra) + " into that folder under exactly that name (it is the mountain picture ChatGPT made; it is not in the repo)."), "", "---", "", intro.format(n=len(refs_used), sheets="", kind=""), "THE JOBS", ""]
    for i, j in enumerate(jobs, start):
        L += [f"=== JOB-{i:02d} of {start + len(jobs) - 1}: {j['title']} ===", f"ATTACH: {', '.join(j['attach']) if j['attach'] else '(nothing)'}", f"PRODUCE: {j['output']}", "PROMPT:", j["prompt"], ""]
    return "\n".join(L) + "\n"


def ref_path(f):
    if f.startswith("BOOKLET-"): return os.path.join(ROOT, "prompts", "refs", f)
    return os.path.join(ROOT, REFS[f], f)


REMAKE_INTRO = """Please do ALL of the jobs below, in order, by yourself, without asking me any questions.

RULES FOR EVERY JOB
- Each job says which images to attach and what each one is for. The character reference shows how the {noun} looks; the booklet drawing shows the correct body positions; a diagram shows where the limbs go.
- If you can attach only ONE image, attach that job's ALL-REFS file instead: the same images side by side, left to right, in the order the job lists them.
- Give each result the label JOB-NN and show me the whole image. Sheets only: I do not need the figures as separate files.
- Count the limbs in every figure: exactly two arms and two legs.
- Grade yourself honestly at the end: for each job, say which items of its CHECK list pass and which do not. Do not invent extra rules (for example a minimum gap size): the figures only need to not touch.
- If a job cannot be done, say so in one line and carry on with the next one.
"""


def remake_main(a):
    out = os.path.abspath(a.out); ch = P.load_character(a.character); strips = json.load(open(os.path.join(ROOT, "prompts", "strips.json")))["strips"]
    keys = [k.strip() for k in a.remake.split(",")]
    for k in keys:
        if k not in strips: sys.exit(f"unknown strip {k}")
        if not strips[k].get("remake"): sys.exit(f"strip {k} has no 'remake' entry in prompts/strips.json")
    J = remake_jobs(ch, strips, keys); tag = a.name; refs = os.path.join(out, f"refs-{tag}"); os.makedirs(refs, exist_ok=True)
    for f in sorted({f for j in J for f in j["attach"]}):
        src = ref_path(f)
        if not os.path.exists(src): sys.exit(f"missing reference {src}")
        shutil.copy(src, os.path.join(refs, f))
    L = [f"# Batch {tag}: remakes from the booklet", "", "How to use this: one job per message. Attach the files on that job's ATTACH line (they are in `refs-" + tag + "/`), then paste that job's text. "
         "If the tool takes only one image, attach that job's `ALL-REFS` file from the same folder instead.", "",
         "The same text works in ChatGPT and in Grok. To compare tools, run every job in both and keep the results apart (e.g. JOB-01-grok.png, JOB-01-chatgpt.png).", "", "---", "",
         REMAKE_INTRO.format(noun=ch.get("noun", "boy")), "THE JOBS", ""]
    for i, j in enumerate(J, 1):
        allrefs = f"JOB-{i:02d}-ALL-REFS.png"; composite([os.path.join(refs, f) for f in j["attach"]], os.path.join(refs, allrefs)); j["all_refs"] = allrefs
        L += [f"=== JOB-{i:02d} of {len(J)}: {j['title']} ===", f"ATTACH: {', '.join(j['attach'])}   (or just {allrefs})", f"PRODUCE: {j['output']}", "PROMPT:", j["prompt"], ""]
    open(os.path.join(out, f"BATCH-{tag}-sprites.md"), "w").write("\n".join(L) + "\n")
    json.dump([{k: v for k, v in j.items() if k != "prompt"} for j in J], open(os.path.join(out, "jobs.json"), "w"), indent=1)
    print(f"{len(J)} remake jobs -> {out}")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter); ap.add_argument("--out", required=True)
    ap.add_argument("--remake", help="comma-separated strip keys: build a remake batch (booklet drawing + diagram attached) instead of the overnight batch")
    ap.add_argument("--name", default="D", help="batch letter for --remake"); ap.add_argument("--character", help="character file (default config/character.json)")
    a = ap.parse_args()
    if a.remake: return remake_main(a)
    out = os.path.abspath(a.out)
    ch = P.load_character(a.character); strips = json.load(open(os.path.join(ROOT, "prompts", "strips.json")))["strips"]; bg = json.load(open(os.path.join(ROOT, "prompts", "backgrounds.json")))
    A = sprite_jobs(ch, strips); B = background_jobs(bg); needed_A = sorted({f for j in A for f in j["attach"]}); needed_B = sorted({f for j in B for f in j["attach"] if f in REFS}); extra_B = sorted({f for j in B for f in j["attach"] if f in USER_SUPPLIED})
    for tag, need in (("A", needed_A), ("B", needed_B)):                      # one folder per request, so "attach every file in the folder" is exactly right
        d_ = os.path.join(out, f"refs-{tag}"); os.makedirs(d_, exist_ok=True)
        for f in need:
            src = os.path.join(ROOT, REFS[f], f)
            if not os.path.exists(src): sys.exit(f"missing reference {src}")
            shutil.copy(src, os.path.join(d_, f))
    introA = INTRO.replace("{sheets}", "Sheets only: I do not need the figures as separate files.").replace("{kind}", "Jobs 1 to 8 fix sheets that came back wrong (RETAKES): image 1 is the bad attempt, image 2 the character reference. Jobs 9 to 18 are first drawings.")
    introB = INTRO.replace("{sheets}", "").replace("{kind}", "These jobs are backgrounds, not characters: no boy, no people. Where a job asks for a flat magenta (#FF00FF) background, that is so the picture can be cut out by software.")
    open(os.path.join(out, "BATCH-A-sprites.md"), "w").write(render(A, "Overnight batch A: the sprite sheets", introA, 1, needed_A, "refs-A"))
    open(os.path.join(out, "BATCH-B-backgrounds.md"), "w").write(render(B, "Overnight batch B: the backgrounds", introB, 19, needed_B + extra_B, "refs-B", extra_B))
    json.dump({"A": [{k: v for k, v in j.items() if k != "prompt"} for j in A], "B": [{k: v for k, v in j.items() if k != "prompt"} for j in B]}, open(os.path.join(out, "jobs.json"), "w"), indent=1)
    print(f"{len(A)} sprite jobs, {len(B)} background jobs, {len(needed_A)} + {len(needed_B)} reference files -> {out}")


if __name__ == "__main__": main()
