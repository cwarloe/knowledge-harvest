# Charts 2–6: what is still to build

Generated from `data/5bx-charts.json` (the booklet's own wording), 2026-11-19. Chart 1 is built. Counting by exercise name, starting position and movement, **all six charts need 32 distinct strips; 26 are still to build.** Levels inside a chart (D- to A+) only change numbers, so each chart's six levels are free once its strips exist.

## What changes from chart to chart

- **Every exercise changes** each chart, except the run: the run is the same wording in charts 1–3 ("lift feet approximately 4 inches") and charts 4–6 ("lift knees waist high"). That is **two run strips in total**.
- **The jump changes every chart:** scissor, astride, half knee bends, semi-squat, semi-spread eagle, jack.
- **Some of these cannot be seen from the side.** Astride jumps and jack jumps spread the legs sideways. Chart 3's toe touch says "touch floor 6 inches outside left foot, again between feet… outside right foot". A strict side view hides all of that. **Decision for the author:** those strips probably need a front or three-quarter view. The kit supports it: a strip in `prompts/strips.json` can carry its own `view`. Mixing views inside one video is a look decision, so it is yours to make. [JUDGMENT, not from the booklet]
- **Some are the same exercise made harder.** Sit-up → sit-up with hands behind head → sit-up with a twist. Push-up → wide-hand → clap. Cheaper to derive these by **editing** the nearest strip (about 1,700 credits for 4 takes) than to generate from nothing (about 7,300).

## Rough cost (estimates from this run's measured rates; the checking is the real time)

| | Per strip, 4 takes | 26 strips |
|---|---|---|
| Generate fresh | about 7,300 credits (about $1.33) | about 190,000 credits (about $35) |
| Derive by editing a close strip | about 1,700 credits (about $0.31) | about $8 if all could be edited; realistically half and half, **about $20** |

Add 1 to 2 retries on the hard ones (the leg raise and the run each needed one). Every strip still has to be checked against the booklet wording below, and a person who knows the exercises should watch each finished video.

## Suggested order

1. **The knees-high run and the five other jumps** first: the run is reused by charts 4–6 and is 6 of every 11 minutes. (Chart 1's run and scissor jumps are done, and the 4-inch run already covers charts 2–3.)
2. **Chart 2**, because it is the nearest to chart 1 (same run, sit-up and push-up are close relatives of chart 1's).
3. Then charts 3–6, each reusing the previous chart's strips as the reference for editing.
4. After each chart: `build.py --list`, `tests/smoke.py`, a `--preview`, then the full build.

## The strips


### Chart 1 (**done**)

| Slot | Exercise | Starts | Movement (booklet wording) |
|---|---|---|---|
| ex1 | Toe touching | Feet astride, arms upward. | Forward bend to floor touching then stretch upward and backward bend. |
| ex2 | Partial sit-up | Back lying, feet 6" apart, arms at sides. | Sit up just far enough to see your heels. |
| ex3 | Alternate leg raise | Front lying, palms placed under the thighs. | Raise head and one leg, repeat using legs alternately. |
| ex4 | Knee push-up | Front lying, hands under the shoulders, palms flat on the floor. | Straighten arms lifting upper body, keeping the knees on the floor. Bend arms to lower body. |
| run | Stationary run | Count a step each time left foot touches floor. Lift feet approximately 4 inches off floor. | Every 75 steps do 10 "scissor jumps". |
| jump | scissor jumps | — | Scissor jumps - Stand with right leg and left arm extended forward, and left leg and right arm extended backward.; Jump up - change position of arms and legs before landing. Repeat (arms shoulder high). |

### Chart 2 (5 to build)

Reuse: run, lift 4 inches (same as chart 1)

| Slot | Exercise | Starts | Movement (booklet wording) |
|---|---|---|---|
| ex1 | Toe touching | Feet astride, arms upward. | Touch floor and press (bounce) once then stretch upward and backward bend. |
| ex2 | Sit-up | Back lying, feet 6" apart, arms at sides. | "Sit up" to vertical position, keep feet on floor even if it is necessary to hook them under a chair. |
| ex3 | Back extension | Front lying, palms placed under thighs. | Raise head, shoulders, and both legs. |
| ex4 | Push-up | Front lying, hands under the shoulder, palms flat on floor. | Straighten arms to lift body with only palms and toes on the floor. Back straight. |
| jump | astride jumps | — | Astride jumps - feet together, arms at side.; Jump and land with feet astride and arms raised sideways to slightly above shoulder height. Return with a jump to the starting position for count of one.; Keep arms straight. |

### Chart 3 (5 to build)

Reuse: run, lift 4 inches (same as chart 1)

| Slot | Exercise | Starts | Movement (booklet wording) |
|---|---|---|---|
| ex1 | Toe touching | Feet astride, arms upward. | Touch floor 6" outside left foot, again between feet and press once then 6" outside right foot, bend backward as far as possible, repeat, reverse direction after half the number of counts. |
| ex2 | Sit-up, hands behind head | Back lying, feet 6" apart, arms clasped behind head. Allow knees to bend slightly. | Sit up to vertical position, keep feet on floor, hook feet under chair, etc., only if necessary. |
| ex3 | Back extension, hands behind back | Front lying, hands interlocked behind the back. | Lift head, shoulders, chest and both legs as high as possible. |
| ex4 | Chin-forehead push-up | Front lying, hands under the shoulders, palms flat on floor. | Touch chin to floor in front of hands - touch forehead to floor behind hands before returning to up position. |
| jump | half knee bends | — | Half knee bends - Feet together, hands on hips, knees bent to form an angle of about 110 degrees. Do not bend knees past a right angle.; Straighten to upright position, raising heel off floor, return to starting position |

### Chart 4 (6 to build)

| Slot | Exercise | Starts | Movement (booklet wording) |
|---|---|---|---|
| ex1 | Toe touching, circle bend | Feet astride, arms upward. | Touch floor outside left foot, between feet, press once then outside right foot, circle bend backwards as far as possible, reverse direction after half the number of counts. |
| ex2 | Sit-up, toe touch | Back lying, legs straight, feet together, arms straight overhead. | Sit up and touch the toes keeping the arms and legs straight. Use chair to hook feet under only if necessary. |
| ex3 | Back extension, arms sideways | Front lying, hands and arms stretched sideways. | Lift head, shoulders, arms, chest and both legs as high as possible. |
| ex4 | Wide-hand push-up | Front lying, palms of hands flat on floor, approximately 1 foot from ears directly to side of head. | Straighten arms to lift body. |
| run | Stationary run | Count a step each time left foot touches floor. Lift knees waist high. | Every 75 steps do 10 "semi-squat jumps". |
| jump | semi-squat jumps | — | Semi-squat jumps - Drop to a half crouch position with hands on knees and arms straight, keep back as straight as possible, right foot slightly ahead of left.; Jump to upright position with body straight and feet leaving |

### Chart 5 (5 to build)

Reuse: run, lift knees waist high (same as chart 4)

| Slot | Exercise | Starts | Movement (booklet wording) |
|---|---|---|---|
| ex1 | Toe touching, hands clasped | Feet astride, arms upward, hands clasped, arms straight. | Touch floor outside left foot, between feet, press once then outside right foot, circle bend backwards as far as possible. Reverse direction after half the number of counts. |
| ex2 | Sit-up with twist | Back lying, legs straight, feet together, hands clasped behind head. | Sit up and raise legs in bent position at same time twist to touch right elbow to left knee. This completes one movement. Alternate the direction of twist each time. |
| ex3 | Back extension, arms overhead | Front lying, arms extended overhead. | Raise arms, head, chest and both legs as high as possible. |
| ex4 | Clap push-up | Front lying, hands under shoulder, palms flat on floor. | Push off floor and clap hands before returning to starting position. |
| jump | semi-spread eagle jumps | — | Semi-spread eagle jumps - Feet together, drop to a half crouch position hands on knees with arms straight.; Jump up to feet astride swing arms overhead in mid-air, return directly to starting position on landing.; Raise  |

### Chart 6 (5 to build)

Reuse: run, lift knees waist high (same as chart 4)

| Slot | Exercise | Starts | Movement (booklet wording) |
|---|---|---|---|
| ex1 | Toe touching, reverse clasp | Feet astride, arms upward, hands reverse clasped, arms straight. | Touch floor outside left foot, between feet, press once then outside right foot, circle bend backwards as far as possible. Reverse direction after half the number of counts. |
| ex2 | Pike sit-up | Back lying, legs straight, feet together, arms straight over the head. | Sit up and at the same time lifting both legs to touch the toes in a pike (V) position. |
| ex3 | Back extension with press | Front lying, arms extended over head. | Raise arms, head, chest and both legs as high as possible then press back once. |
| ex4 | Chest-slap push-up | Front lying, hands under shoulders, palms flat on floor. | Push off floor and slap chest before returning to starting position. |
| jump | jack jumps | — | Jack jumps - Feet together, knees bent, sit on heels, finger tips touch floor.; Jump up, raise legs waist high, keep legs straight and touch toes in midair.; Keep legs straight, raise feet level to "standing waist height |

## Per-chart look (idea, not decided)

Six charts means six videos that can look alike. A different backdrop per chart (morning in chart 1 to evening in chart 6, or six locations) is **one `theme.json` per chart and no new boy**. See `docs/LAYERS-AND-IDEAS.md`.
