# Making the videos with a new character

Everything about *what the exercise looks like* lives in `prompts/strips.json` and the booklet drawings in
`prompts/refs/BOOKLET-*.png`. Everything about *who is doing it* lives in one character file. So a new
character is one new file plus a few test takes. No exercise wording changes.

## 1. Write the character file

Copy `config/characters/_template.json` to `config/characters/<name>.json` and fill it in. Rules that held
for the first character:

- **One concrete sentence** for the description: age, hair, skin, face, build, each clothing item *with its color*, shoes, then the art style.
- **No pink, purple or magenta** on the character: the background is magenta and gets keyed out.
- **Colors with a clear darker shade**, because the far arm and leg are drawn darker so near and far limbs read apart.
- **Lock decisions with a date** in `locked` (the first character's blue sneakers took two rounds to settle).

## 2. Pilot: the first sheet with no reference

There is no picture of the new character yet, so the first sheet describes them in words only:

```bash
python3 kit/prompt.py --strip knee-push-up-c1 --first --character config/characters/<name>.json
```

Ask for 4 takes. The knee push-up is the pilot because it came out right 4 times out of 4 for the first
character: simple, side-on, easy to judge. Keep the best take; it becomes the **character reference**
(the file every later job attaches as image 1). Save it under `sheets/` and point `CH` at it, or pass it
by hand.

## 3. Everything else: remake batches

```bash
python3 kit/make_batch.py --out batches/<date>-<letter> --remake <strip>,<strip>,... --name <letter> \
    --character config/characters/<name>.json
```

Each job attaches at most three images: the character reference, the booklet drawing of the exercise,
and a position diagram where one exists. That fits Grok (3 to 5 images per edit) and ChatGPT. Each job
also gets an `ALL-REFS` image (the same pictures side by side) for tools that take a single attachment.
Order the strips by chart so the ones the game needs first come first.

## 4. Grade and keep

Log every result with `kit/library.py add`, grade it against the strip's `check` list, and `choose` the
pick. Raw takes and rejects go to the Google Drive folder *Sprite Art 5BX Workout*, not into git.

## What we learned with the first character (applies to every character)

- **Attach the booklet drawing, not the failed take.** Attaching a bad sheet as "fix this" anchored the
  tool to its mistakes; batch C kept most of them. The one job that got the form right (semi-squat jumps)
  had a position diagram attached.
- **When the tool keeps failing a pose, check the wording against the booklet first.** Our Chart 3
  push-up wording asked for a body shape the booklet does not show; no tool could satisfy it.
- **Hands, feet and head placement relative to the body** (outside the foot, under the thigh, behind the
  hands) is where every tool struggles. Draw a diagram for it rather than adding more words.
- **Strict side views hide left/right differences** (scissor stance A vs B). Use a three-quarter front
  view when the difference between poses is which side is forward.
- **Tools grade themselves with invented rules** (ChatGPT failed its own sheets on an "8% gap" no prompt
  asked for). The prompts now say the figures only need to not touch.
