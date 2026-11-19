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
python3 tests/smoke.py path/to/5bx-charts.json            # 15 s: did my change break anything?
```

The data file is a parameter and is never copied here. The plan has one home (`cwarloe/5BX`,
`data/5bx-charts.json`), so this kit cannot drift from it.

## Change something

Measured on the first build (one machine; treat as rough).

| I want to change… | Edit | Credits | Time to see it |
|---|---|---|---|
| Shoe, shorts or tank colour | `config/theme.json` → `recolor` (hue in degrees) | none | seconds for one exercise, about 30 s for two |
| Backdrop colours | `theme.json` → `backdrop` | none | one re-render |
| Backdrop as a picture | `backdrop.style: "image"`, `backdrop.image: "sheets/…"` | none (or one generated image) | one re-render |
| Wording ("BREAK", "LEFT", the title line), other languages | `theme.json` → `strings` | none | one re-render |
| Timer, title or bar colours, fonts, sizes | `theme.json` → `hud`, `formats` | none | one re-render |
| Crossfade length, or no crossfade | `fade_max_seconds`, or `--no-fade` | none | one re-render |
| Portrait instead of landscape | `--format portrait` | none | one exercise took 8 s |
| Another level of the same chart | `--level "B"` | none | full build about 6 min |
| Where the boy stands, or his size | `formats.*.box`, or `anchor` in `strips.json` | none | one exercise |
| One pose is wrong | regenerate that strip (below), replace the PNG | about 7,300 for 4 takes (about $1.33) | about a minute to generate, then the check |
| The boy's look | `config/character.json`, regenerate every strip | about 56,000 for the whole set, with retries | an afternoon |
| A new exercise or a new chart | add strips (below) and map them | about 7,300 per strip | per strip, as above |

Everything is cached by what it depends on (the strip file, the theme, the code). An unchanged
rebuild took 3 seconds; a one-exercise change re-renders only that exercise.

## How it is layered

| Layer | Where it comes from |
|---|---|
| Backdrop | drawn from `theme.json`, or an image. Its own file in `.work/` |
| The boy | cut out of the strip onto transparency. Each pose is saved alone as `layer_pN.png` (boy only) and `pN.png` (boy over backdrop) in `.work/frames/` |
| Timer, titles, bar, break cards | drawn on top at render time from `theme.json` |

There is no drag-and-drop editor. Layers are placed by settings. If you need to scrub and
nudge visually, the same layers map directly onto a Remotion project.

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
so each one needs its own strips. `--list` refuses to build a chart that still has gaps and says which.

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
sheets/                 the chosen strips (chart 1)
prompts/strips.json     the pose lists that produced them
kit/build.py            the builder     kit/prompt.py   prompt maker
kit/keyer.py            background -> transparency     kit/recolor.py   free recolour
tests/smoke.py          15-second check
```

Lessons from building it, what worked and what didn't: `cwarloe/lessons-learned` → `AI_SPRITE_VIDEO_LESSONS.md`.
