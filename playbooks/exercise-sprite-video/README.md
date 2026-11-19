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

The data file is a parameter and is never copied here. The plan has one home (`cwarloe/5BX`,
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

## Add an exercise, or a whole chart

1. See what the plan says: `python3 kit/prompt.py --booklet --data … --chart 2 --slot ex3`
2. Write the pose list in `prompts/strips.json` (one pose per visible stage, plus a "must NOT" for
   the common error). Then `python3 kit/prompt.py --strip <name>` prints the prompt.
3. Generate 4 takes (`gemini-3-pro-image`, 16:9). First strip of a new character: no reference. After that,
   pin a **neutral standing strip** as the reference. Do not pin a strip that is lying down for a
   different lying exercise: its pose leaks in.
4. **Check each take against the booklet text before anything else.** Pick the one with the right form.
5. Save it in `sheets/`. Add an entry under `strips` in `config/strips.json` (`file`, `poses`, `anchor`, `cycle`).
6. Point the chart slot at it under `charts`. `build.py --list` shows what is still missing.
7. `python3 tests/smoke.py …`, then a `--preview` build.

Charts 2–6 use different exercises (sit-up with hands behind head, wide-hand push-up, jack jumps…),
so each one needs its own strips: **26 more across the five charts** (`docs/CHARTS-2-6.md`). `--list` refuses to build a chart that still has gaps and says which.

## The demo page

`kit/make_demo.py` builds a folder of plain files: a 40-second reel (about 1.6 MB), an interactive viewer where you switch backdrop layers, add the mat, shadow and bottle, and recolor the boy, and the edit-test pictures. About 4.6 MB in all. It reads everything from the kit's own assets and config, so rebuilding after any change refreshes it. A copy for the chart 1 look is in `docs/sprite-boy-demo/` at the repo root, ready for GitHub Pages (Settings → Pages → deploy from a branch → `/docs`; the page would be at `/sprite-boy-demo/`). Rebuild it with the command above.

## Rules that matter

- **Form is checked by a person.** The generator makes plausible-but-wrong form. Check every strip against the booklet's words, and have someone who knows the exercises watch the final video.
- **The character is locked in `config/character.json`:** blue sneakers, no green shoes, original clothing. It is pasted into every prompt.
- **Don't fight the shadow.** The model adds a ground shadow even when told not to. The key removes it.
- **Key by hue, not by exact colour.** The background is not exactly #FF00FF. See `kit/keyer.py`.
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
sheets/                 the chosen strips (chart 1); sheets/candidates/ = edit-test results, not wired in
assets/                 baked layers: sprites/, backdrops/, props/   (real files, committed)
exports/                a layer pack for chart 1 landscape (separate PNGs + scene.json)
config/scene.json       props between/in front of the layers; scene.example-mat.json is a ready example
docs/LAYERS-AND-IDEAS.md   brainstorm: every way to split this into layers, tagged by effort
docs/CHARTS-2-6.md      what the five remaining charts need, from the data
prompts/strips.json     the pose lists that produced them
kit/build.py            the builder     kit/prompt.py   prompt maker     kit/make_demo.py   the demo page
kit/keyer.py            background -> transparency     kit/recolor.py   free recolour
tests/smoke.py          15-second check
```

Lessons from building it, what worked and what didn't: `cwarloe/lessons-learned` → `AI_SPRITE_VIDEO_LESSONS.md`.
