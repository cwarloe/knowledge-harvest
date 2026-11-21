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
| `tools/measure.py`, `tools/measure_backgrounds.py` | Pixel checks used for the review (hard-coded Windows paths; edit them before reuse) |
| `assets/sprites/`, `assets/backgrounds/` | Only the outputs that passed review |
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

### Not included (files stay in the original overnight folder)

- **Failed a brief requirement:** JOB-01-v2 (hop arms, smirk), JOB-02 (hands at the feet, figures
  17 px apart), JOB-04-v2 (row 3 start pose not flat), JOB-05 (forehead lands in front of the
  hands), JOB-06-v2 (lift too small, start feet raised), JOB-08 (both rows same camera, jumps
  barely leave the floor), JOB-09 and JOB-14 (hands touch the shoes, figures 13-22 px apart),
  JOB-17 (side view, brief asked for three-quarter front), JOB-22 and JOB-23 (tall mats taper
  too much), JOB-26 (a floor seam crosses the stage strip), JOB-27 variations 1, 2 and 4
  (horizon 60-62%), JOB-19 original (gridded window behind the centre), JOB-29 (whole upper room
  re-rendered, not just the window).
- First takes superseded by a v2 (JOB-01, 03, 04, 06) were not reviewed.

### Cutting these out

No sheet has an exact `#FF00FF` background. Corners read about (250, 5, 252), and the JOB-10,
11, 14, 15 and 16 sheets drift further (green around 22-28). Use a chroma-key tolerance of at
least about 40.
