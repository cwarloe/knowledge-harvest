# How to make the exercise strips with any image tool

The strips were made with ElevenLabs' image tools. Nothing about the method needs ElevenLabs. This guide plus `prompts/PROMPTS.md` (the paste-ready text) is everything required to make them elsewhere, which may be cheaper or free.

## What a strip is

One image per exercise. The same boy drawn 3 or 4 times, left to right, one for each stage of the movement. Same character, same scale, same camera angle, flat magenta background. Examples are in `sheets/`.

Why one image and not one image per pose: generated separately, the character drifts (different shoes, hair, build) and the loop flickers. Drawn together in one image, he stays the same boy.

## What you need

1. **The prompt for the exercise.** `prompts/PROMPTS.md`, or `python3 kit/prompt.py --strip <name>`. There are two versions: one for when you can attach a reference image, one for the very first strip (the boy described in words only).
2. **The character in words.** `config/character.json`. Already inside every prompt.
3. **A reference image of the boy**, if the tool accepts one. Use `sheets/ex1-toe-touching.png`: it is a neutral standing strip. Do **not** use a lying-down strip as the reference for a different lying exercise: its pose leaks in (the leg raise failed four times in a row that way).
4. **Image settings:** wide 16:9, at least about 1300 pixels across, 4 takes per prompt.
5. **The plan's own wording for the exercise**, so you can check form: `python3 kit/prompt.py --booklet --data path/to/5bx-charts.json --chart 1 --slot ex3`.

## Magenta background or a transparent one?

The kit accepts either. **Default to magenta**; use a transparent PNG only if your tool gives you a real one.

| | Flat magenta background (the default) | Transparent PNG straight from the tool |
|---|---|---|
| Works in | Any image tool, because it is just a colour in the prompt | Only tools that really output transparency. Support varies, and some will not |
| Cutting out | The kit keys it out (one rule, `kit/keyer.py`) | Nothing to do |
| Edges | Clean, with a despill step for the pink rim | Depends on the tool: soft or haloed edges are common |
| Main risk | The background is not exactly #FF00FF, and a ground shadow appears anyway (both handled) | **A checkerboard drawn into the picture instead of real transparency.** That is not transparency, and the boy ends up surrounded by grey squares |
| Tested here | Yes, end to end, on all six strips | Tested with a stand-in: a transparent version of a real strip gives identical sprites. Not tested with a tool that makes its own |

How to tell a real transparent PNG from a fake: open it on a dark or coloured background. A real one shows that colour through the gaps. A fake still shows grey and white squares. The kit also refuses to treat a picture with painted-in squares as transparent.

If you try a transparent route, check the edges at full size (look for a light halo around the hair and shoes) and compare one pose against the magenta version before committing to it.

## The steps

1. Open `prompts/PROMPTS.md` and copy the prompt for your exercise.
2. In your tool, attach the reference image (if it can) and paste the prompt. Say nothing else. Set 16:9. Ask for 4 takes.
3. Pick a take with the checklist below. **Check form against the booklet's wording, not against taste.** Generators make plausible-but-wrong form.
4. Save the PNG into `sheets/` with the file name shown in `config/strips.json` (or a new name, then register it).
5. Run `python3 tests/smoke.py path/to/5bx-charts.json`. It checks that the strip splits into the right number of poses.
6. Preview the exercise: `python3 kit/build.py --data ... --only <slot> --preview`. Look at it.
7. Fix a bad pose by editing, or regenerate (see the end).

## Pick a take: the checklist

- [ ] The right number of poses, left to right, none touching or overlapping
- [ ] Strict side view in every pose (unless the strip is meant to be a front view)
- [ ] The same boy in every pose: spiky black hair, cyan tank, red shorts, white socks, **blue** sneakers. No green shoes.
- [ ] The far arm and leg a darker shade, so near and far limbs read
- [ ] Feet or hands on one shared floor line (airborne poses clearly higher)
- [ ] Flat magenta background, no text, no labels, no arrows. A ground shadow is fine; the key removes it.
- [ ] **Form matches the booklet.** The things to look for are in each strip's "must NOT" lines: knees bent when they should be straight, hips piked on a knee push-up, hands behind the head when they should be at the sides, a lunge when it should be an upright stance.

## What goes wrong, and the fix

| Problem | Fix |
|---|---|
| The reference pose leaks into a different exercise | Use a standing strip as the reference. Say "use it only for the character's appearance, ignore its poses." Spell out the geometry in words. |
| The same leg does all the work (run, leg raise) | Name the near and far limb, shade the far one, and say "the two lifts must use DIFFERENT legs". |
| Knees bent in the sit-up | Put "legs STRAIGHT" and "knees NOT bent" in every pose line. |
| A ground shadow appears although you said none | Ignore it. The key removes it. |
| The lifted foot is too high (run) | An edit pass: "lower the lifted foot to about 4 inches, keep everything else". |
| Stance A and B look the same in profile (scissor jumps) | Not fixable by editing. It needs a front view. |
| The character slowly changes between strips | Pin the reference, and repeat the character description in the prompt. |

## Using other tools: what I can and cannot tell you

I only ran this through ElevenLabs: `gemini-3-pro-image` to generate, `gpt-image-2.5-sunburst` to edit. The prompts are plain English and should transfer, but I have not tested other tools, so treat the next points as things to check, not promises.

- **Most current image models accept a reference image** in the chat or API. Some have a dedicated "character reference" or "style reference" setting. Read the tool's own current documentation for how, and test with the leg-raise prompt, which shows quickly whether the reference is leaking.
- **If a tool cannot take a reference image at all:** use the first-strip prompt (character in words) for every strip, expect more drift between exercises, and fix drift with recolouring and edit passes.
- **If a tool will not draw a flat magenta background:** either ask it for a real transparent PNG (the kit takes that as is, see above) or use any flat plain colour. The key is one short rule in `kit/keyer.py` and is easy to change to another colour.
- **If the image is not exactly 16:9 or the size differs:** that is fine. Poses are cut out by shape and scaled, so only the pose count and clean separation matter.
- **Check each tool's terms** before using generated art in anything you publish or sell.

## Registering a new strip

Add an entry in `config/strips.json`:

```json
"my-new-strip": {"file": "my-new-strip.png", "poses": 3, "anchor": "span-center", "cycle": [1, 2, 3, 2], "reps_per_cycle": 1}
```

- `anchor` pins each pose so the boy does not slide: `span-right` (feet stay put, lying on his back), `span-left`, `span-center` (standing), `head` (run and jumps), or `hips` (the red shorts: for any exercise where he lies and the hips stay on the floor, such as the back extension).
- `cycle` is the order poses play in. `[1, 2, 1, 3]` is "stand, fold, stand, bend back".
- Then point a chart slot at it under `charts`, run `build.py --list` and `tests/smoke.py`.

## Cost, and cheaper ways

On ElevenLabs: about 1,218 credits for a first strip, 1,827 with a reference, about 433 for an edit, all per take, and 4 takes each. A whole chart's six strips came to about $2 to $8 depending on retries. Edits are about a quarter the price of regenerating. With another tool the numbers will differ, and some tools are free.

Cost-cutters that do not depend on the tool: derive a harder variant of an exercise by **editing** its easier cousin's strip; ask for fewer takes once the prompt is proven; reuse strips across charts when the booklet wording is identical (`docs/CHARTS-2-6.md` lists which).

## Always

A person who knows the exercises looks at every finished strip and the finished video before it is shared as instruction.
