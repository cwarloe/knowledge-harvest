# Exercise Sprite Video

Raw material and review notes for the 5BX exercise video: pose sprite sheets of a cartoon boy
and stage backgrounds, produced in one overnight ChatGPT batch (29 jobs) and then reviewed
against the written briefs.

## Layout

| Path | What it is |
|------|------------|
| `briefs/BATCH-A-sprites.md` | The 18 sprite-sheet prompts (jobs 01-18), as pasted into ChatGPT |
| `briefs/BATCH-B-backgrounds.md` | The 11 background prompts (jobs 19-29) |
| `briefs/jobs.json` | Job list: title, reference files to attach, expected output |
| `audits/` | ChatGPT's own notes on its output, unedited |
| `tools/measure.py` | Pixel checks used for the review below (hard-coded Windows paths; edit `A` and `B`) |
| `assets/sprites/`, `assets/backgrounds/` | Only the outputs that passed review |

The reference images the briefs name (`c4-run-knees-waist-high.png`, `REF-footswitch.png`,
`bg-keeper-gym-landscape-v1.png`, and so on) are not in this repo.

## What passed, and what did not

"Pass" means it meets the brief on the points checked by eye or by `measure.py`. It does not
mean anatomy was validated or that the pose is correct exercise instruction. Every output is
still a draft.

### In `assets/`

| File | Job | Notes |
|------|-----|-------|
| `sprites/JOB-07.png` | Stationary run | Lifted foot alternates near/far; side view, arms bent; gaps 163 px. Lift is roughly one shoe height, near the 4-inch target |
| `sprites/JOB-13.png` | Semi-spread eagle jumps | Strict front view, three clear poses, gaps 197 px |
| `sprites/JOB-18.png` | Jack jumps | Strict side view; squat, take-off and pike clearly separate in height |
| `backgrounds/JOB-19-...-plain-window-candidate.png` | Tall gym | Wall/floor line 55.5%, floor strip flat (std ~1.5), centre wall calm. Floor is ~10 levels lighter than the original; use the original only if you need an exact floor match |
| `backgrounds/JOB-20-...mat-teal*.png`, `JOB-21-...mat-navy*.png` | Wide mats | Background exactly `#FF00FF`; bbox within ~1.3% of the brief; transparent versions have no fringing but hard (non-antialiased) alpha. Mats are lighter than the requested hex and the far edge is slightly narrower (about 11-89% vs 8-92%) |
| `backgrounds/JOB-27-variation-3.png` | Pine forest | Horizon ~58-59% (brief: 56%); middle of the 73-86% strip is empty; no pink/magenta. Closest of the four variations |

### Not included (files stay in the original overnight folder)

- **Failed a brief requirement:** JOB-01-v2 (hop arms are in a boxing guard, smirk), JOB-08 (both
  rows same camera, jumps barely leave the floor), JOB-14 (hands land at the feet, figures 13 px
  apart), JOB-17 (side view, brief asked for three-quarter front), JOB-22 and JOB-23 (tall mats
  taper far more than the brief: far edge about 10-90%, brief 5-95%), JOB-27 variations 1, 2
  and 4 (horizon ~60-62%), JOB-19 original (gridded window behind the centre).
- **Not reviewed against the brief:** JOB-02 to 06, 09 to 12, 15, 16, 24 to 26, 28, 29.
  Audit notes flag problems on several (for example 26: floor seams cross the exercise area;
  29: not an exact-preservation edit).
- Gaps between figures are under 45 px in JOB-02, 06, 09, 11, 14, 15 and 16, which will make them
  hard to cut apart.

### Cutting these out

No sheet has an exact `#FF00FF` background. Corners read about (250, 5, 252), and the JOB-10,
11, 14, 15 and 16 sheets drift further (green around 22-28). Use a chroma-key tolerance of at
least about 40.
