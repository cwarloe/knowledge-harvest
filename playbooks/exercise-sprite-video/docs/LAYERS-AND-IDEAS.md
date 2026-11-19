# Layers and ideas: how to keep splitting this into pieces

Brainstorm, 2026-11-19. The rule behind all of it: **anything likely to change should be its own file, combined by the script.** Tags show effort:

- **[built]** works today
- **[config]** a setting or a new JSON file, no code
- **[small]** a small code change (about an hour)
- **[gen]** needs generated art (credits)
- **[idea]** bigger, or needs a decision from the author

Five more charts are coming (`CHARTS-2-6.md`), then ongoing changes. Items that help most with that are marked ★.

## 1. Backdrop layers

- **[built]** Seven separate files: sky, clouds, mountains-far, mountains-near, trees-back, trees-front, ground. Swap any one with `backdrop.overrides`.
- ★ **[config]** **One `theme.json` per chart**: morning in chart 1 to evening in chart 6, or six locations. A visible sense of progress for zero new boy art.
- **[small]** Parallax: nudge each layer slowly at a different speed so the scene breathes. The layers already exist.
- **[small]** Drifting clouds (a slow horizontal move on the clouds layer).
- **[config]** Time-of-day grade: a tint layer over everything (dawn orange, dusk blue) with an opacity.
- **[small]** Weather layers: light rain, snow, falling leaves, as transparent overlays.
- **[gen]** Whole alternative locations as layered plates: gym interior (wall, window, floor), living room, park, beach, school field, a "5BX in 1961" RCAF hall.
- **[gen]** A generated backdrop picture (`style: "image"`) for a one-off look, with the boy on top.
- **[small]** Depth of field: blur only the far layers.
- **[small]** Vignette and film grain as layers, so a retro look is one switch.
- **[config]** Backdrop packs: `assets/backdrops/<id>/` folders. Switch the whole scene by changing one id.
- **[idea]** The RCAF screen-print look from the 5BX design notes (parked there as a title card) as a backdrop pack.

## 2. Floor and props (between the backdrop and the boy, or in front)

- **[built]** Mat, contact shadow, and any PNG prop, switched on per exercise in `scene.json`.
- **[config]** A different mat colour per chart or per level (a colour belt idea: D- to A+).
- **[small]** More built-in prop kinds: towel, step, bench, dumbbell, jump rope, timer clock on a wall, boombox. Each is a PNG or a few lines.
- **[gen]** Generate props as sprites on magenta with the same key. A prop sheet of ten things is one generation.
- ★ **[small]** Props that follow the boy using anchors from `meta.json` (feet, head, hand). A sweatband at the head anchor, a towel on the mat edge.
- **[small]** Foreground blur layer (grass in front) for depth.
- **[config]** "Front" props such as a water bottle and a scoreboard that stay put between exercises, so the scene feels continuous.
- **[small]** Footprints or a light dust puff on each jump landing (a short effect layer on the jump beat).

## 3. The boy (the character layer)

- **[built]** One transparent file per pose, with anchors and offsets saved in `meta.json`. Recolour by hue (shoes, shorts, tank) with no credits.
- ★ **[small]** Save **colour-region masks** next to the sprites (shorts, shoes, tank, skin, hair). Recolour becomes exact, and you can add effects to one region only.
- **[small]** Team-colour presets: a `recolor` block per preset (red team, blue team), chosen per chart or per level.
- **[small]** Logo or number on the tank: a transparent layer placed at the tank region of each pose (the mask gives the position).
- **[small]** Accessories as layers attached to anchors: headband, glasses, cap, wristbands, a medal on the last level.
- **[gen]** **More characters** from the same recipe: a girl, an older adult, a kid. Same prompts with a different `character.json`. The whole kit is character-agnostic.
- **[small]** Two characters on screen: a demonstrator and a smaller "you try it" partner, or the same strips mirrored for a second figure.
- **[small]** Mirror a strip for left-handed or opposite-direction versions. Poses face right; flipping gives facing left (check each exercise still reads correctly).
- **[gen]** **Front-view and three-quarter strips** for the exercises a side view hides (astride jumps, jack jumps, chart 3's toe touch).
- **[small]** Far-side limb layer: the darker shaded far arm and leg split from the near ones, so they can be drawn in a different order.
- **[small]** Idle and break poses: a standing, hands-on-hips, breathing pose cut from an existing strip. The break card has no character today.
- **[idea]** Skeleton/keypoints per pose, so new in-between poses can be built by blending two sprites' parts instead of crossfading.

## 4. Motion and timing

- **[built]** Hold-and-cut with a short eased crossfade. All timing comes from the data file.
- **[config]** Crossfade length per exercise (the push-up ghosts; the run does not need one).
- **[small]** Gentle breathing bob (1-2 px) during holds so nothing is ever frozen.
- **[small]** A squash-and-stretch on the jump beat.
- **[small]** Onion skin: show the previous pose as a faint ghost on purpose, as a teaching aid ("here is where you came from").
- **[small]** Motion arrows for the key movement (a curved arrow on the fold, arrows on the leg lift) drawn in code, so they are never AI-hallucinated.
- **[small]** A rep dot trail: a dot lights up per rep done, a progress ring per exercise.
- **[small]** "Slow-mo demo" mode: the first rep of each exercise at half speed, then at pace.
- **[small]** An optional metronome tick layer at the true cadence (the run's 80 steps a minute) as audio and as a visual pulse.
- **[idea]** True keyframe tracks (a small timeline JSON per exercise: pose, hold, ease). Needed only if the cycle ever stops being "a loop of poses".

## 5. On-screen text (HUD) layers

- **[built]** Kicker, title, target, timer, "left", progress bar, break card, all from `theme.json` strings and colours.
- ★ **[config]** **Language packs**: `strings` per language. Plain and cheap. (Exercise names come from the data file, so translating those is a data question.)
- **[small]** Safe-area guides per format (phone notches, TV overscan).
- **[small]** High-contrast and large-text variants for accessibility, as theme presets.
- **[small]** Captions layer for any voiceover, built from the same script.
- **[small]** Level badge (D- to A+) and chart number in a corner. The data file already knows both.
- **[small]** Age-goal end card, from the `ageGroups` in the data ("age 35-39: chart 3, level B").
- **[small]** Brand layer: logo, URL, watermark, toggled per output.
- **[rule]** Form cues shown on screen ("keep legs straight") come **only from the booklet's own notes** (they are in the data file). No invented cues.

## 6. Audio layers (nothing built yet)

- **[small]** Voiceover per cue from ElevenLabs text-to-speech: "Exercise two, partial sit-up. Begin." The text is the HUD strings, so it follows any wording change.
- **[small]** Each cue is its own audio file, named by segment, so one re-recorded line replaces one file.
- **[small]** Count-in beeps for breaks; a distinct sound for the jump window.
- **[small]** Music bed as a separate track with automatic ducking under the voice.
- **[small]** Per-language voice packs, in step with the language packs above.
- **[idea]** Spoken rep counts ("one, two…") timed to the cycle. Works because cycle length is known exactly.

## 7. Structure around the video

- **[small]** Intro and outro cards as their own layer sets (title, "chart 1, level A+", the age goal).
- **[small]** A thumbnail generator: the composed frame plus the title text, one PNG per chart and level. (The RCAF screen-print idea fits here.)
- **[small]** Chapter markers in the MP4 for each exercise, so players show a menu.
- **[small]** Short per-exercise clips (one exercise, with its own HUD) for sharing. `--only` already does this.
- **[small]** A looping GIF per exercise for the app's reference screen. The 5BX app has a "Preview" screen that currently shows static figures; these would be its animations.

## 8. Outputs

- **[built]** Landscape 1920×1080; portrait 1080×1920 (tested on one exercise).
- **[config]** Square (1080×1080) as another `formats` entry.
- **[small]** 4K for TV (a `formats` entry, with the strips upscaled once).
- **[small]** Upscale the strips once with an image upscaler so the boy stays sharp at 4K.
- ★ **[built]** The **layer pack export**: separate PNGs plus `scene.json`, for any other tool.
- **[small]** Export the same pack as a sprite-sheet plus atlas JSON for a game engine (the original "video game 5BX" idea).
- **[small]** Interactive version: the same layers and manifest driving a web page with Play/Pause, a "follow along" mode and per-exercise tabs.

## 9. Making new strips cheaper (the real cost across 26 more)

- ★ **[built]** Prompt maker that pulls the booklet's wording (`kit/prompt.py --booklet`). Saved pose lists in `prompts/strips.json`.
- ★ **[built, tested]** **Edit instead of regenerate** for close variants: about a quarter of the cost, and untouched figures keep their shape.
- ★ **[small]** A batch script that prints the prompts for every missing strip in a chart and a cost estimate, so one session can queue a whole chart.
- ★ **[small]** A strip checklist generated from the booklet text (start position, what must not happen, pose count), used when picking a take.
- **[small]** Auto-checks on a strip before a human sees it: pose count, floor alignment, no stray blobs, far-side shading present.
- **[small]** A contact-sheet tool that lays a chart's strips side by side for one review pass.
- **[small]** Record every generation's id and model in `prompts/` so any strip can be traced and regenerated.
- **[idea]** Reuse strips between charts when the booklet wording is identical (the data comparison already does this).

## 10. Portability

- ★ **[built]** The plan (`5bx-charts.json`) is a parameter, never copied, so there is one source of truth.
- **[built]** Layer pack and manifest: Remotion, After Effects, a video editor or a web page can rebuild the same scene.
- **[idea]** A **Remotion version**: a component per layer, reading the same `scene.json`, with a visual preview you can scrub. This is the drag-and-nudge editor that does not exist yet.
- **[idea]** A SCORM or xAPI wrapper if this ever sits in an LMS, with per-exercise completion. (Not researched here; check the standard before building.)
- **[small]** Version the config: a `CHANGELOG` of look changes and a tag per released video.

## 11. Guardrails (so frequent changes stay safe)

- ★ **[built]** `tests/smoke.py` in about 20 seconds.
- ★ **[small]** A **theme check** like the one in your other repos (no raw colours or fonts outside `theme.json`). `build.py` still has a few built-in numbers (trunk colour, cloud white) that should move into the theme.
- **[small]** A visual regression check: render each strip's frames and compare with the last approved ones, flag differences over a threshold.
- **[small]** Fail the build if a chart slot has no strip, or a strip's pose count changed (already partly done).
- **[rule]** A person who knows the exercises signs off on every new strip and every finished video. The generator makes plausible-but-wrong form.

## If I had to pick the first five

1. A `theme.json` **per chart** (free; gives the six videos their own feel).
2. **Colour-region masks** saved with the sprites (small; makes every future recolour exact).
3. A **batch prompt and cost script** for a chart (small; makes the 26 strips a queue, not a project).
4. **Voiceover per cue** from the same strings (small; the biggest quality jump).
5. A **Remotion layer** reading `scene.json` (bigger; gives the visual editor).
