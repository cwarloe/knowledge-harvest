# Lessons learned: overnight run 1 (2026-11-20)

Treat sprite and background production as a process with inputs, a measured output and a control plan.
This file is the record: what the process is, how well it ran, every defect with its cause and countermeasure,
what worked, and what to test next. Each defect that recurs becomes a line in `pipeline/rules.toml`, so the
prompt generator stops repeating it.

## 1. The process (SIPOC)

| Suppliers | Inputs | Process | Outputs | Customer |
|-----------|--------|---------|---------|----------|
| You (reference sprite, exercise charts) | `characters/*.toml`, `exercises.toml`, `stage.toml`, `rules.toml` | 1 generate prompts, 2 ChatGPT draws sheets, 3 QC gate, 4 human pose review, 5 retake or accept, 6 cut and key | Transparent sprites with feet pivots, backgrounds, mats | The 5BX exercise video |

Standard work for one cycle is in `pipeline/README.md`.

## 2. How the first run performed

First-pass yield = jobs accepted without a retake. Counts are from my review (small sample, one reviewer).

| Group | Jobs | Accepted first time | Yield |
|-------|------|---------------------|-------|
| Sprite sheets, first drawings | 11 (jobs 2, 9-18) | 7 (10, 11, 12, 13, 15, 16, 18) | 64% |
| Sprite sheets, retakes of earlier failures | 7 (jobs 1, 3-8) | 2 (03-v2, 07) | 29% |
| Backgrounds (ChatGPT) | 11 (jobs 19-29) | 7 | 64% |
| Mat overlays drawn in code | 4 | 4 | 100% |

Retakes did worse than first drawings. A plausible cause is that attaching the failed sheet anchors ChatGPT to its
own mistakes. That is a hypothesis from 7 samples, not a finding; section 7 describes the test.

## 3. Critical-to-quality (CTQ) characteristics

| CTQ | Limit | Checked by | Automated |
|-----|-------|-----------|-----------|
| Background exactly `#FF00FF`, flat | within 30 (pass), 60 (warn) of the key colour | `qc sheet` | yes |
| Figure count and rows | as in `exercises.toml` | `qc sheet` | yes |
| Clearance between figures | target 8% of width; warn under 3%; fail under 0.5% (touching) | `qc sheet` (true pixel distance) | yes |
| Grounded poses share a floor line | within 3% of sheet height | `qc sheet` | yes |
| Airborne poses clearly off the floor | per-exercise minimum lift (for example 8% for a full jump) | `qc sheet` | yes |
| Character stays the same character | skin, hair and clothing colours present in every figure | `qc sheet` (palette in `characters/*.toml`) | yes |
| Stage strip flat, horizon on target, floor colour, no pink | strip colour spread at most 6; horizon within 2%; floor within 14 per channel | `qc bg` | yes |
| Mat colour and edges | colour within 3, edges within 0.3% | `qc mat` | yes |
| Pose is the pose the exercise names; contacts land where named; camera is the one asked for; two arms and two legs | the pose text | `checklist` (human) | no |

Measurement system note: pose review is a human judgement. The checklist exists so every reviewer asks the same
questions. On this run the script alone would have passed 4 of the 9 sheets I rejected on review and warned on 4
more, so the two steps are both needed.

## 4. Defect log

| ID | Defect | Seen in | Root cause (best evidence) | Countermeasure | Where it lives |
|----|--------|---------|---------------------------|----------------|----------------|
| D-01 | Figures nearly touching | 02, 09, 11, 14 (clearance 1-3% of width); all three six-figure sheets (02, 09, 14) are the worst | Prompts said "wide gaps" without a number; six figures in one 16:9 row are crowded | Ask for 8% of width and 80-85% figure scale; measure it; try two rows of three for six-pose exercises | `R-GAP`, `qc`, section 7 |
| D-02 | Numeric targets missed by 2-6 points | Mat taper (far edge 10-90% vs 5-95%), mat colours 10-18 levels light, forest horizon 58-62% vs 56%, strip seams | Image generators approximate; a percent in a prompt is a wish | Draw anything numeric in code; for scenes, state the pixel row and measure | `mats.py`, `stage` prompt, `qc bg` |
| D-03 | Background not exactly `#FF00FF` (green channel 3-30) | All 22 sheets | Same cause as D-02 | Key with a measured colour and a tolerance of at least 40, never an exact match | `R-KEY`, `cut.py` |
| D-04 | Requested camera ignored: two rows that look alike, side view where three-quarter front was asked, "strict front" figures turned | 08, 17, 09, 14 | Camera words get averaged; a retake can repeat the old angle | Name the camera in each row, forbid turning in strict front, check in review | `R-CAMERA`, `R-FRONT`, checklist |
| D-05 | Fingertips land on the shoe, not outside the foot | 02, 09, 14 | Anatomy shortcut: hands drift to the nearest foot | State the offset in shoe-widths | `R-CONTACT` |
| D-06 | Start pose not flat (legs or feet lifted) | 04 row 3, 06-v2 | The model draws the "exercise" look in every frame | Say that only later poses lift | `R-FLAT` |
| D-07 | Lift too small, or the extra step is barely visible | 06-v2 (thighs), 08 (jumps), 16 (press, about 30 px) | "A little higher" is below what the model draws as a difference | Give lift as a share of figure height; measure airborne poses | `R-LIFT`, `qc` |
| D-08 | Smirk instead of a calm smile; hop arms in a boxing guard | 01-v2 | Style drift | Face rule is in the character file; arm action is in the pose text | `characters/*.toml`, `fixes.toml` |
| D-09 | Extra or missing limbs | None seen in the sheets reviewed | Rule worked | Keep "count the limbs" in every prompt | body rules line |
| D-10 | Near and far limbs hard to tell apart | Not seen | Darker far-side limbs worked | Keep the rule | `R-NEAR-FAR` |
| D-11 | "Keep everything else the same" edits re-render the whole image | 29 (about 6.5% of pixels changed everywhere), 19 plain-window (floor 10 levels lighter) | The model redraws; it does not edit | Do small edits in code or by hand, not by regeneration | open |
| D-12 | Retakes yield lower than first drawings | 7 retakes, 2 accepted | Possibly anchoring on the failed sheet | Test fresh prompt against fix prompt | section 7 |
| D-13 | Accidental duplicate or oddly named output files (`-preview-preview`) | 22, 23 | ChatGPT naming | The batch asks for one named file per job; rename on receipt | open |

## 5. What worked: keep doing

- **Three or four figures per row.** Every sheet with 3-4 poses in one row was either accepted (07, 10, 11, 12, 13, 15, 16, 18, 03-v2) or failed for a pose reason, not spacing. All three six-figure sheets had spacing and contact problems.
- **Darker far-side limbs.** Near and far limbs were easy to read in every sheet I opened.
- **Counting limbs in the prompt.** No extra limbs in any sheet I reviewed.
- **Magenta key background.** All 22 sheets cut into sprites without errors, and the JOB-13 cut-outs had no pink left on the edges when placed on a real background.
- **Per-job attachment folders and a zip.** Saved hunting for files; now `sprite.py prompts --bundle` does it.
- **Drawing the mats in code.** Exact colours and edges, one second per mat, zero retakes.
- **Auditing against the written brief.** The audit notes ChatGPT wrote itself were honest about doubt, which made review faster.

## 6. Ideas to reuse

- Put everything character-specific in one file (done: `characters/*.toml`). Swapping the character is one file.
- Keep poses and rules separate from the look so they carry across characters (done: `exercises.toml`).
- Turn every recurring defect into a one-line rule that is added to every prompt (done: `rules.toml`).
- Score a sheet in seconds with a script and keep human time for the poses (done: `qc.py`, `checklist`).
- Cut sprites with a feet pivot and a lift offset so jumps stay in the air when placed on a stage (done: `cut.py`).
- Draw numeric assets in code. Candidates next: floor strips, simple props, any overlay with a hard position.
- Write the horizon and strip as pixel rows in background prompts, and measure them on receipt.

## 7. Experiments to run next

1. **Retake anchoring (D-12).** For 3 of tonight's retakes, send the same job twice: once in fix mode (failed sheet
   attached) and once in fresh mode (no failed sheet, same rules). Compare QC and review results.
   `python sprite.py prompts --mode fix ...` and `--mode fresh ...`.
2. **Do the learned rules help?** Run 3 jobs with and without the "ALSO (lessons)" block and compare clearance and lift.
3. **Two-row sheets (04, 05, 08) and six-figure sheets (02, 09, 14).** Try one camera per image instead of two rows
   (two-row sheets repeated the same camera, D-04), and two rows of three for the six-pose exercises (D-01).
4. **Second character.** Build a real reference for `example-teen-girl`, run 3 exercises, and note what had to be
   hand-fixed. That measures how close we are to "no rework".

## 8. Control plan

| What | How often | Who |
|------|-----------|-----|
| `python -m unittest discover tests` in `pipeline/` | after any change to the config files or code | whoever edits |
| `sprite.py qc sheets` on every returned batch | every batch | script |
| `sprite.py checklist` pose review | every sheet that QC did not fail | human |
| Add a row to the defect log and a line to `rules.toml` | any defect seen twice | human |
| Re-check QC thresholds against the review | after each batch | human |

## 9. Limits of this record

- The QC thresholds (3% warn, 0.5% fail, minimum lifts) were set from this one run and are untuned.
- Only one reviewer judged the poses, and my viewing was by eye. Treat the yields as indicative.
- Only the boy has real reference art. The girl character file proves the prompts swap cleanly, not that the
  drawings will be good.
- Jobs 24-26 and 28 could not be compared with their source images, which were not available.
