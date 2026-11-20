# Exercise sprite video

Turns a workout plan (the 5BX data file) into a full video starring a cartoon boy: pose strips
generated once, then looped at the plan's real pace with a timer, rep count and break cards.
First built for 5BX chart 1, level A+: 11:40 at 1080p, 49 MB.

**Built for change.** Assume the look, the wording, the character, the format and the exercises
will all change. Each of those is one small file, and a rebuild only redoes what changed.

## Run it

```bash
pip install pillow numpy          # plus ffmpeg on PATH

python3 kit/build.py --data path/to/5bx-charts.json --chart 1 --level "A+" --out chart1.mp4
python3 kit/build.py --data ... --preview                 # whole video in about a minute
python3 kit/build.py --data ... --only ex3 --preview      # one exercise, seconds
python3 kit/build.py --data ... --list                    # what each chart slot uses, and what is missing
python3 kit/build.py --data ... --scene config/scene.example-mat.json --preview --only ex4   # try a mat, shadow, prop
python3 kit/build.py --data ... --export exports          # the scene as separate transparent PNGs + scene.json
python3 kit/build.py --bake                               # (re)write assets/: sprites and backdrop layers
python3 kit/make_demo.py --data ... --out docs/sprite-boy-demo --reel   # phone-friendly demo: reel + interactive layer viewer
python3 tests/smoke.py path/to/5bx-charts.json            # 20 s: did my change break anything?
```

Every full render also writes `builds/<id>.json` (id = `c<chart>-<level>-<format>`, plus `--tag name` for a variant). It records exactly what went in: the plan file's hash and where it lives, the look, scene and strip settings, each strip sheet per slot with its hash and library id, the fonts, the code version, ffmpeg's version, and the result. The videos stay out of git; the record is what lets you remake one:

```bash
python3 kit/builds.py list
python3 kit/builds.py check   c3-Aplus-landscape --data path/to/5bx-charts.json   # up to date, or what changed (and which parts re-render)
python3 kit/builds.py rebuild c3-Aplus-landscape --data path/to/5bx-charts.json   # same settings -> out/c3-Aplus-landscape.mp4
```

Everything a build reads is in this folder (strip sheets, `config/`, baked `assets/`, the fonts in `assets/fonts/`), except the plan file. The data file is a parameter and is never copied here. The plan has one home (`cwarloe/5BX`,
`data/5bx-charts.json`), so this kit cannot drift from it.

## Change something

Measured on the first build (one machine; treat as rough).

| I want to change… | Edit | Credits | Time to see it |
|---|---|---|---|
| Shoe, shorts or tank colour | `config/theme.json` → `recolor` (hue in degrees) | none | seconds for one exercise, about 30 s for two |
| Backdrop colours | `theme.json` → `backdrop` | none | one re-render |
| Swap one backdrop layer (just the clouds, just the trees) | `theme.json` → `backdrop.overrides: {"clouds": "path.png"}` | none | one re-render |
| Add a mat, a soft shadow, or any prop picture | `config/scene.json` (`enabled: true`) or `--scene file` | none | one exercise, about 10 s |
| Backdrop as a picture | `backdrop.style: "image"`, `backdrop.image: "sheets/…"` | none (or one generated image) | one re-render |
| Wording ("BREAK", "LEFT", the title line), other languages | `theme.json` → `strings` | none | one re-render |
| Timer, title or bar colours, fonts, sizes | `theme.json` → `hud`, `formats` | none | one re-render |
| Crossfade length, or no crossfade | `fade_max_seconds`, or `--no-fade` | none | one re-render |
| Portrait instead of landscape | `--format portrait` | none | one exercise took 8 s |
| Another level of the same chart | `--level "B"` | none | full build about 6 min |
| Where the boy stands, or his size | `formats.*.box`, or `anchor` in `strips.json` | none | one exercise |
| One pose is wrong | **edit** the strip (below), or regenerate it | edit: about 1,700 for 4 takes (about $0.31). Regenerate: about 7,300 (about $1.33) | about a minute, then the check |
| The boy's look | `config/character.json`, regenerate every strip | about 56,000 for the whole set, with retries | an afternoon |
| A new exercise or a new chart | add strips (below) and map them | about 7,300 per strip | per strip, as above |

Everything is cached by what it depends on (the strip file, the theme, the code). An unchanged
rebuild took 3 seconds; a one-exercise change re-renders only that exercise.

## How it is layered

Every layer is a real file you can open, replace or reuse in another tool. Nothing depends on a workspace.

| Layer (bottom to top) | Lives in | Change it by |
|---|---|---|
| Backdrop: sky, clouds, mountains-far, mountains-near, trees-back, trees-front, ground | `assets/backdrops/<id>/<format>/NN-name.png` | `theme.json`, or swap any one file with `overrides` |
| Props behind the boy: mat, contact shadow, anything | drawn from `config/scene.json`, or a PNG in `assets/props/` | `scene.json` (`enabled`, `slots`, `z`) |
| **The boy**, one transparent file per pose | `assets/sprites/<strip>/pN.png` + `meta.json` (anchors, offsets) | regenerate or edit the strip, then `--bake` |
| Props in front of the boy | same as above, with `"z": "front"` | `scene.json` |
| Timer, titles, bar, break cards | drawn at render time | `theme.json` |

- **Recolour happens on the boy's layer at build time**, so the saved sprites stay in the original colours and a colour change never needs a re-bake.
- **`--bake`** writes `assets/` (sprites and backdrop layers). They are cached by what they came from, so a changed strip or theme re-bakes on its own.
- **`--export DIR`** writes a **layer pack** for any other tool (Remotion, After Effects, Captivate, a video editor): `backdrop/` layers, `props_behind` / `props_front`, `boyN.png` per pose (frame-sized, positioned), and `scene.json` with the stack order, timing of every segment, cycle lengths, the on-screen wording and the geometry. A pack for chart 1, landscape, is in `exports/` (5.5 MB).
- There is no drag-and-drop editor. Placement is settings (`formats.*.box`, `anchor`, prop `x`/`scale`). If you want to scrub and nudge visually, the layer pack maps one-to-one onto a Remotion project.

## Edit a strip instead of regenerating it

The ElevenLabs edit tool takes "change this, keep that" and re-renders the strip. Tested on two known weak spots (see `prompts/edits.json`):

- **It works.** Untouched figures kept 96–99% of their shape. The run's lifted foot came down toward the booklet's 4 inches. The scissor stance lost its lunge and bent knee.
- **It costs about 433 credits a take**, roughly a quarter of a fresh generation.
- **It re-renders the whole strip** (it came back 1280×720, not the 1376×768 sent), so it is not pixel-exact. Fine here, because poses are re-cut by shape.
- **Shading can be lost.** Some edits dropped the darker far-side arm. Say what to keep, and check.
- **It cannot invent a visual difference that profile hides.** Scissor stance A and B still look alike.
- Candidates from the test are in `sheets/candidates/`. They are not wired in.

## Make the strips with a different tool

The prompts, settings and lessons are published so the strips do not depend on one vendor: `docs/HOW-TO-GENERATE-STRIPS.md` (method, checklist, what to test in a new tool) and `prompts/PROMPTS.md` (paste-ready text for every strip, with and without a reference image). The demo site has the same thing with a copy button on each prompt. Regenerate after any change: `python3 kit/prompt.py --all --data path/to/5bx-charts.json`.

## Backgrounds that match the boy

The first backdrop was drawn in code in a blocky style; the boy is now a smooth cartoon. `python3 kit/prompt_bg.py --publish` writes prompts for six settings (forest, beach, desert, snow, city park, gym), landscape and portrait, to `prompts/BACKGROUNDS.md` and the prompts page. They work in two steps: one master scene fixes the horizon, light and scale, then each of seven depth layers (sky, clouds, far, near, ground, back, front) is redrawn from it on flat magenta. The horizon, the floor line where the boy stands (80% down in landscape, 74% in portrait), the empty strip around his feet and the calm middle third all come from `config/theme.json`, so the prompts follow the build.

```bash
python3 kit/import_backdrop.py --id beach --dir path/to/layers     # cut out the magenta, fit to the frame, write assets/backdrops/beach/landscape/
# then set "backdrop": {"id": "beach"} in config/theme.json and rebuild
```

A scene can also carry an `overlay` prop: a full-frame picture on magenta (a floor mat drawn in the floor's perspective, light beams, a foreground fringe) cut out at build time and drawn behind or in front of the boy. Put it in `config/scene.json` as `{"kind": "overlay", "file": "assets/mat-teal.png", "z": "behind", "slots": "*"}`; swap the file (or pass another `--scene`) to change the mat per chart. The kit's older `mat` prop is only a thin bar below the feet.

`python3 kit/check_backdrop.py picture.png --out previews/` grades any background against the stage: floor contrast against his skin (orange and tan floors make his legs melt into them), how busy the middle third is, how flat the strip around his feet is, and writes a preview with the real run and push-up sprites on it. Candidates and verdicts so far: `library/backgrounds/`.

The importer also writes `preview.png` with the floor line and the boy's height marked, so placement can be checked before any render. Layers from different settings can be mixed: every set shares one horizon and one floor line.

## Add an exercise, or a whole chart

1. See what the plan says: `python3 kit/prompt.py --booklet --data … --chart 2 --slot ex3`
2. Write the pose list in `prompts/strips.json` (one pose per visible stage, plus a "must NOT" for
   the common error). Then `python3 kit/prompt.py --strip <name>` prints the prompt.
3. Generate several takes (4 in the API; 9 at a time in a chat image tool works too). First strip of a new character: no reference. After that,
   pin a **neutral standing strip** as the reference. Do not pin a strip that is lying down for a
   different lying exercise: its pose leaks in.
4. **Check each take against the booklet text before anything else.** Pick the one with the right form.
5. Put every take worth keeping in the library (below), then grade it. Copy the pick to `sheets/`. Add an entry under `strips` in `config/strips.json` (`file`, `poses`, `anchor`, `cycle`).
6. Point the chart slot at it under `charts`. `build.py --list` shows what is still missing.
7. `python3 tests/smoke.py …`, then a `--preview` build.

Charts 2–6 use different exercises (sit-up with hands behind head, wide-hand push-up, jack jumps…),
so each one needs its own strips: **26 more across the five charts** (`docs/CHARTS-2-6.md`). `--list` refuses to build a chart that still has gaps and says which.

## The strip library

Every take worth keeping goes in `library/` with a record, so the best strip for an exercise is one command away and a rejected take is never generated twice. `library/index.json` is the record, `library/images/` the files.

```
python3 kit/library.py add take.png --strip sit-up-hands-behind-head-c3 --tool chatgpt --view angle --notes "..."
python3 kit/library.py grade c3-ex2-01 --form 4 --legibility 5 --character 5 --angle 4 --key 5 --by claude
python3 kit/library.py choose c3-ex2-01        # the pick; the previous pick becomes a candidate
python3 kit/library.py best                    # the pick, or the best candidate, for every chart and slot
python3 kit/library.py list --chart 3 --slot ex1
```

`add` measures what can be counted: figures found, fringe (a messy cut-out), stray green (no green shoes), and refuses the same file twice. Grades are 1 to 5 on form (matches the booklet), legibility, character (same boy), angle (one camera angle) and key. Form counts most. A grade records who gave it; `--expert` marks one given by a person who knows the exercises. `choose` does not change a video: copy the file to `sheets/` and name it in `config/strips.json` (the command prints this).

## The demo page

`kit/make_demo.py` builds a folder of plain files: a chart menu (every chart in the plan, with what is made and what is not), a 40-second reel (about 1.6 MB), an interactive viewer where you switch backdrop layers, add the mat, shadow and bottle, and recolor the boy, and the edit-test pictures. About 4.6 MB in all. It reads everything from the kit's own assets and config, so rebuilding after any change refreshes it. A copy for the chart 1 look is in `docs/sprite-boy-demo/` at the repo root, ready for GitHub Pages (Settings → Pages → deploy from a branch → `/docs`; the page would be at `/sprite-boy-demo/`). Rebuild it with the command above.

## Sizes on screen

Each exercise is scaled to fill a stage box (`formats.landscape.box` in `config/theme.json`). A lying exercise fills the width and a standing one fills the height, so left alone the lying boy came out about twice the size of the standing boy (measured by shoe length: 180-210 px against 85-100 px). A strip can set `"fit"` in `config/strips.json` (1.0 fills the box; 0.75 is three quarters of it) without moving his feet. Chart 1's three lying exercises use 0.72 to 0.78. The title block was made more compact so the standing figures could grow about 8%: the box is 690 px tall, and the three text sizes are in the same file.

## Where the title and the clock go

The title block (exercise number, name, reps) and the countdown used to sit in dead centre, and the title capped how tall a standing figure could be. Now each shape (`formats.landscape.hud`, `formats.portrait.hud` in `config/theme.json`) picks a layout:

- `"layout": "auto"` (landscape default): the build measures the title with the real font and the figure's width and height, puts the block top-left or top-right (whichever leaves the figure more room), and lets a standing figure use the whole `free_h` (780 px). A title long enough to reach the figure shrinks the figure instead of covering it. A lying figure is wide, not tall, so it keeps the normal box.
- `"layout": "left"` or `"right"`: force a side. `"layout": "center"`: the old layout (portrait default, where the tall frame has room above).
- `"clock"`: `"opposite"` (default: the countdown sits bottom-right when the title is top-left), `"same"` (same side) or `"center"`.
- `"margin"`, `"gap"` and `"free_h"` tune the spacing and the tallest a standing figure may be.

`fit` in `config/strips.json` can be one number or one per shape, `{"landscape": 0.72, "portrait": 1.0}`: a lying figure is shrunk in landscape but fills the narrow portrait frame.

## Rules that matter

- **Form is checked by a person.** The generator makes plausible-but-wrong form. Check every strip against the booklet's words, and have someone who knows the exercises watch the final video.
- **The character is locked in `config/character.json`:** blue sneakers, no green shoes, original clothing. It is pasted into every prompt.
- **Don't fight the shadow.** The model adds a ground shadow even when told not to. The key removes it.
- **Key by hue, not by exact colour.** The background is not exactly #FF00FF. See `kit/keyer.py`.
- **Magenta or transparent: either works.** Default to magenta (works in every tool). A tool that gives a *real* transparent PNG can be used as is; a checkerboard painted into the picture is not transparency. See `docs/HOW-TO-GENERATE-STRIPS.md`.
- **Nothing about the plan is typed into this kit.** Reps, steps, breaks, jump windows all come from the data file.

## Known weak spots

- Scissor jumps: stance A and B look alike in profile. Only the shading differs.
- The run lifts the foot higher than the booklet's 4 inches.
- A crossfade shows a faint ghost when the head moves a long way (push-up). Shorten `fade_max_seconds` or use `--no-fade`.
- Run cadence: this kit plays one four-pose cycle per counted step (the booklet counts each left-foot landing). The older `5BX/video/chart.py` plays one cycle per four steps. Confirm which you want.
- Break cards have no character yet. No voiceover yet.
- Portrait works but has had one test, not a full review.

## Files

```
config/theme.json       look and wording
config/strips.json      which image is which exercise; which strip each chart slot uses
config/character.json   the boy, in words
sheets/                 the strips wired into videos; sheets/candidates/ = edit-test results, not wired in
library/                every kept take, indexed, measured and graded (kit/library.py)
builds/                 one record per finished video: what went in, so it can be checked and rebuilt (kit/builds.py)
assets/                 baked layers: sprites/, backdrops/, props/   (real files, committed)
exports/                a layer pack for chart 1 landscape (separate PNGs + scene.json)
config/scene.json       props between/in front of the layers; scene.example-mat.json is a ready example
docs/HOW-TO-GENERATE-STRIPS.md   the method for making strips with ANY image tool
prompts/PROMPTS.md      every prompt, settings, what went wrong and the fix (generated: `kit/prompt.py --all`)
docs/LAYERS-AND-IDEAS.md   brainstorm: every way to split this into layers, tagged by effort
docs/CHARTS-2-6.md      what the five remaining charts need, from the data
prompts/strips.json     the pose lists that produced them
kit/build.py            the builder     kit/library.py   the strip library     kit/builds.py   build records: list, check, rebuild     kit/prompt_bg.py   background prompts     kit/import_backdrop.py   generated layers -> a backdrop     kit/prompt.py   prompt maker     kit/make_demo.py   the demo page
kit/keyer.py            background -> transparency     kit/recolor.py   free recolour
tests/smoke.py          15-second check
```

Lessons from building it, what worked and what didn't: `cwarloe/lessons-learned` → `AI_SPRITE_VIDEO_LESSONS.md`.
