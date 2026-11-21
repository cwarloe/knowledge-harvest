# The sprite line

One command, `sprite.py`, runs every stage. A new character, art style or body type is one config file; the
exercises, rules, checks and cutting all carry over.

```
characters/*.toml  ─┐
exercises.toml      ├─►  sprite.py prompts ─► ChatGPT ─► sheets ─► sprite.py qc ─► checklist ─► sprite.py cut ─► sprites
rules.toml          │         (stage)                                  │                          (feet pivot, lift)
stage.toml         ─┘                                          failures ─► LESSONS.md ─► rules.toml
```

## Setup

Python 3.11 or newer.

```powershell
pip install numpy pillow opencv-python-headless
cd playbooks/exercise-sprite-video/pipeline
python -m unittest discover tests      # all green = the config and generators are healthy
```

## Standard work for one cycle

1. **Pick the character.** Edit or copy `characters/boy.toml`. Put the reference image next to the refs.
2. **Write the batch.**
   ```powershell
   python sprite.py prompts --character boy --out batch.md --bundle out/attach --refs C:\refs --sheets C:\last-run
   ```
   `batch.md` is the paste-ready prompt (one job per exercise). `out/attach.zip` holds exactly the files each job needs.
   Use `--exercises 7,13` for a subset and `--mode fix` to retake the jobs listed in `fixes.toml`.
3. **Run it in ChatGPT.** Save each returned sheet as `JOB-NN.png` in one folder.
4. **Score the sheets.**
   ```powershell
   python sprite.py qc sheets C:\returned --character boy
   ```
   Fix anything marked FAIL (retake). WARN means look at it.
5. **Review the poses** (what a script cannot see).
   ```powershell
   python sprite.py checklist --character boy --exercises 7,13 --out review.md
   ```
6. **Cut accepted sheets into sprites.**
   ```powershell
   python sprite.py cut C:\returned\JOB-13.png --out sprites
   ```
   Each sprite is a transparent PNG. `*.manifest.json` gives the feet pivot and `lift_px` (how far the figure sits above
   its floor line), so a jump placed at `floor_y - lift_px` stays in the air.
7. **Log defects.** Anything seen twice gets a row in `../LESSONS.md` and a line in `rules.toml`; the next batch carries it.

Backgrounds and mats:

```powershell
python sprite.py stage --format wide --scene forest --out forest.md          # background prompt with exact rows
python sprite.py qc bg scene.png --format wide --horizon 0.56 --span 0.5 --no-floor-colour   # outdoor scene
python sprite.py qc bg room.png --format tall                                 # indoor room with the grey floor
python sprite.py mats --out mats --tall-room room_tall.png --wide-room room_wide.png   # mats drawn in code, with previews
python sprite.py qc mat mats/mat-wide-teal.png --format wide --colour teal
```

## What each file is

| File | Change it when |
|------|----------------|
| `characters/<name>.toml` | the look changes: age, body, hair, outfit, art style, pronouns, colour palette |
| `exercises.toml` | an exercise is added or its poses change (written once, reused for every character) |
| `rules.toml` | a defect repeats: one line, added to every prompt |
| `fixes.toml` | one exercise needs a specific fix for a retake |
| `stage.toml` | the stage changes: feet line, stage strip, mat sizes and colours, scenes |
| `sprite.py` | never, unless a new command is needed |

## Making a different character

Copy `characters/boy.toml`, edit the look, `noun`, `pronouns`, garment rule and palette hex values, and point
`reference_image` at the new picture. `characters/example-teen-girl.toml` is a worked example, and
`tests/test_pipeline.py` proves that every exercise prompt for her contains no word from the boy
(`boy`, `he`, `his`, red shorts, cyan, spiky hair) and no unfilled placeholders.

Limits: pronouns are he or she only. The palette check needs the new character's real colours, taken from
the reference image, or the QC "character palette" line will fail every figure.

## QC thresholds

| Check | Pass | Warn | Fail |
|-------|------|------|------|
| Background distance from `#FF00FF` | up to 30 | up to 60 | above 60 |
| Clearance between figures (share of sheet width) | 3% or more | 0.5-3% | under 0.5% (touching) |
| Grounded poses' floor line | within 3% of sheet height | within 6% | beyond 6% |
| Airborne lift | at least the exercise's minimum | | below it |
| Character palette | all colours present | a colour is thin | a colour is missing |
| Stage strip colour spread | 6 or less | | above 6, or a seam |
| Horizon | within 2% | within 4% | beyond 4% |

Thresholds were set from one run and are untuned. Change them in `qc.py` after each batch if the review disagrees.
