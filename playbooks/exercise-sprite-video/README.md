# Exercise Sprite Video

A repeatable line for making exercise pose sprites and stage backgrounds for the 5BX video with ChatGPT:
generate the prompts from config, score what comes back, cut accepted sheets into transparent sprites.
The first overnight run (29 jobs) produced the material in `assets/` and the lessons in `LESSONS.md`.

**Start here:** [`pipeline/README.md`](pipeline/README.md) (how to run a cycle, or change the character) and
[`LESSONS.md`](LESSONS.md) (defect log, yields, what worked, what to test next).

## Layout

| Path | What it is |
|------|------------|
| `pipeline/` | The line: `sprite.py` plus config (`characters/`, `exercises.toml`, `rules.toml`, `stage.toml`, `fixes.toml`) and tests |
| `LESSONS.md` | Defect log, first-pass yield, CTQs, experiments to run next |
| `briefs/BATCH-A-sprites.md`, `BATCH-B-backgrounds.md`, `jobs.json` | The original hand-written prompts from run 1 (the generator reproduces them) |
| `briefs/BATCH-C-retakes.md` | The retake batch sent after run 1 (now produced by `sprite.py prompts --mode fix`) |
| `audits/` | ChatGPT's own notes on its output, unedited |
| `assets/sprites/`, `assets/backgrounds/` | Only the outputs that passed review (`mats-code/` was drawn by `pipeline/mats.py`) |
| `RETAKE-NEXT.md` | What to ask ChatGPT to redo, job by job |

The reference images the briefs name (`c4-run-knees-waist-high.png`, `REF-footswitch.png`,
`bg-keeper-gym-landscape-v1.png`, and so on) are not in this repo.

## What passed, and what did not

"Pass" means the output meets its brief on the points checked by eye or by the scripts, with a
2% tolerance on position targets. It does not mean anatomy was validated or that a pose is
correct exercise instruction. Every output is still a draft. I could not compare jobs 24-26
and 28 with their source images, which were not available, so "keep the same" was not checked.

### In `assets/`

| File | Job | Notes |
|------|-----|-------|
| `sprites/JOB-03-v2.png` | Sit-up toe touch (retake) | Arms stay against the head in all three poses; head tucked between the arms at the touch. The audit judged the retake a miss; on viewing, it meets the brief |
| `sprites/JOB-07.png` | Stationary run | Near/far foot alternates; lift is about one shoe height |
| `sprites/JOB-10.png` | Sit-up with a twist | Front view from the foot end, feet off the floor, elbow-to-opposite-knee. Limbs overlap, so contact is the least certain point |
| `sprites/JOB-11.png` | Back extension, arms overhead | Three clear stages, head left, knees straight. Gaps are tight (22 px) but figures do not touch |
| `sprites/JOB-12.png` | Clap push-up | Hands off the floor and together in pose 3, toes only |
| `sprites/JOB-13.png` | Semi-spread eagle jumps | Strict front view, three clear poses |
| `sprites/JOB-15.png` | Pike sit-up | Lying, rising and V poses are distinct; strict side view |
| `sprites/JOB-16.png` | Back extension with a press | Caveat: the press is only slightly higher than the top pose (about 30 px at the arms) |
| `sprites/JOB-18.png` | Jack jumps | Squat, take-off and pike clearly separate in height |
| `backgrounds/JOB-19-...-plain-window-candidate.png` | Tall gym | Wall/floor line 55.5%, strip flat, centre wall calm. The floor is about 10 levels lighter than the original |
| `backgrounds/JOB-20-...mat-teal*.png`, `JOB-21-...mat-navy*.png` | Wide mats | Background exactly `#FF00FF`; position within about 1.3%; transparent versions have no fringing but hard alpha. Mats are lighter than the requested hex |
| `backgrounds/JOB-24.png` | Arcade lounge | Emblem and dots gone, cabinets fully in frame, floor `#6d7a8a` with a gentle gradient, strip clean |
| `backgrounds/JOB-25.png` | Brick loft | Blue-grey brick, two windows in the outer thirds, strip flat. Caveat: a pale warm sunlight patch at top left and a faint streak that reaches the edge of the centre third |
| `backgrounds/JOB-27-variation-3.png` | Pine forest | Horizon about 58-59% (brief: 56%); stage strip empty in the middle; no pink |
| `backgrounds/JOB-28.png` | Mountain meadow | Flat blue-grey track (`#767d86`), no seams, centre calm. Caveat: the track starts at 74.4% down, brief asked for 73% |

### Mats drawn in code (`assets/backgrounds/mats-code/`)

JOB-20 to JOB-23, drawn by `pipeline/mats.py` (`sprite.py mats`) instead of ChatGPT, because its mats drifted from the brief (tall mats tapered too much, colours came out light). These match the brief exactly:

- Top surface is exactly `#217678` (teal) or `#243B66` (navy), flat, with the lighter border line and darker front edge from the brief.
- Position: near and far edges and x-ranges match to within one pixel (wide: near 90% / 5-95%, far 73% / 8-92%; tall: near 84% / 2-98%, far 67% / 5-95%).
- Each mat has a magenta version (background exactly `#FF00FF`, hard edges), a transparent version (antialiased alpha, no magenta), and a preview.
- Tall previews sit on the JOB-19 gym. The original wide gym (`bg-keeper-gym-landscape-v1.png`) is not available here, so the wide previews use JOB-29 as a stand-in room.

These replace the ChatGPT mats in `assets/backgrounds/` for jobs 20-21 and supply the missing 22-23.

### Not included (files stay in the original overnight folder)

- **Failed a brief requirement:** JOB-01-v2 (hop arms, smirk), JOB-02 (hands at the feet, figures
  17 px apart), JOB-04-v2 (row 3 start pose not flat), JOB-05 (forehead lands in front of the
  hands), JOB-06-v2 (lift too small, start feet raised), JOB-08 (both rows same camera, jumps
  barely leave the floor), JOB-09 and JOB-14 (hands touch the shoes, figures 13-22 px apart),
  JOB-17 (side view, brief asked for three-quarter front), JOB-26 (a floor seam crosses the stage strip), JOB-27 variations 1, 2 and 4
  (horizon 60-62%), JOB-19 original (gridded window behind the centre), JOB-29 (whole upper room
  re-rendered, not just the window).
- First takes superseded by a v2 (JOB-01, 03, 04, 06) were not reviewed.

### Cutting these out

No sheet has an exact `#FF00FF` background. Corners read about (250, 5, 252), and the JOB-10,
11, 14, 15 and 16 sheets drift further (green around 22-28). Use a chroma-key tolerance of at
least about 40.

