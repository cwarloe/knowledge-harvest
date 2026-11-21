# Retake list for ChatGPT

Append the "Fix" text below to the ORIGINAL job prompt in `briefs/` and attach the same
reference images as before. For retakes, also attach the previous sheet and say which one is
the better take. Measurements come from `tools/measure.py` and `tools/measure_backgrounds.py`.

Rules to add to every retake:
- Leave at least 8% of the image width between neighbouring figures (several sheets had 13-25 px).
- Background must be exactly #FF00FF.
- Keep the three-quarter / side / front camera exactly as the brief says; do not drift between figures.

## Sprites

| Job | Fix |
|-----|-----|
| JOB-01 (use v2) | Foot order is right: keep it. Hop arms must swing forward and a little up, elbows slightly bent, fists relaxed, not held in a boxing guard at the chest. Calm closed smile, eyes level (currently a smirk). Crouch: back straighter at about 45 degrees, head up. |
| JOB-02 | Touch left/right: fingertips on the floor about six inches OUTSIDE the outer edge of the foot, not at the shoe. Poses 1, 5, 6: arms straight and parallel, upper arms touching the ears. Figures 2-4 were 17 px apart: shrink every figure to ~85% so there is room. |
| JOB-04-v2 | Row 3, pose 1: the legs are lifted; he must lie completely flat. Check pose 1 in rows 1 and 2 the same way. Keep the T-shaped arms. |
| JOB-05 | FOREHEAD pose: the forehead must be level with or BEHIND the hands, with the hands visibly ahead of it; currently the head sits in front of the hands. CHIN pose: the chin must visibly touch the floor. |
| JOB-06-v2 | START: feet and shins flat on the floor (heels are lifted). TOP: lift the thighs, knees and shins clearly higher, with visible daylight between the thighs and the hands; the lift is only about 50 px now. |
| JOB-08 | Row 1 must be a real three-quarter FRONT view and row 2 a strict SIDE view; both rows currently look the same. In the jump poses the feet must be well off the floor (at least a quarter of the figure's height; now about one shoe height), legs together, arms crossing near the body. |
| JOB-09 and JOB-14 | Touch left/right: fingertips on the floor about six inches OUTSIDE the foot, not on the shoe. Figures 2-4 must be strict front view, not turned. They were 13-22 px apart: shrink every figure to ~80% so the gaps are wide. |
| JOB-17 | The brief asks for a three-quarter FRONT view with the head nearer the camera; the sheet is a pure side view. Redraw from the front-three-quarter camera. |

Optional: JOB-16 passes, but the "press" pose is only slightly higher than the top pose (arms about 30 px, legs about 20 px). If a clearer step is wanted, ask for roughly double the extra lift.

## Backgrounds

| Job | Fix |
|-----|-----|
| JOB-22, JOB-23 | Not worth another ChatGPT pass: the tall mats taper too much (far edge 10-90%, brief 5-95%) and the colours drift light. Draw them in code to the exact spec instead. |
| JOB-26 | A floor seam runs straight across the 73-86% strip (at about 74% down). Redraw the flagstones so the strip is perfectly smooth; seams only above 70% and below 90%. Gears are still large on the left: shrink them about 30% as briefed. |
| JOB-27 | Ask for two more variations with the ground starting at 56% down (variation 3 is at 58-59%; the others are 60-62%). Keep rocks and bushes out of the 73-86% strip. |
| JOB-29 | Optional and unapproved: the whole upper room differs from the keeper (about 6.5% of pixels changed evenly across left, middle and right), so it was re-rendered, not just edited. Skip unless the plain centre window is wanted; a pixel edit of the keeper would be more reliable. |

## Also needed

The reference images the briefs name are not in this repo and are needed again for any
retake: `c4-run-knees-waist-high.png` (the character), `REF-footswitch.png`,
`REF-backext-geometry.png`, `bg-keeper-gym-landscape-v1.png`, and the `c*-` and `ex5-` previous sheets.
