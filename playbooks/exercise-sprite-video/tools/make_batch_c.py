import re, sys
O = r"C:\Users\charl\OneDrive\Desktop\overnight"
out = sys.argv[1]

def sections(path):
    txt = open(path, encoding="utf-8").read()
    parts = re.split(r"(?m)^=== JOB-(\d\d) of \d+: (.*?) ===\n", txt)
    d = {}
    for i in range(1, len(parts), 3):
        d[parts[i]] = (parts[i + 1], parts[i + 2].strip())
    return d

A = sections(O + r"\BATCH-A-sprites.md")
B = sections(O + r"\BATCH-B-backgrounds.md")

COMMON = ("EXTRA RULES FOR THIS RETAKE (these override anything above that conflicts):\n"
          "- Leave at least 8% of the image width of empty magenta between neighbouring figures; never let figures touch or overlap.\n"
          "- The background must be one flat, exact #FF00FF with no noise or gradient.\n"
          "- Keep the camera angle exactly as the job says, the same in every figure of a row.\n"
          "- The attached JOB-NN sheet from last night is the best previous attempt. Wherever the prompt above says 'the previous sheet to fix' or 'image 1', it now means THAT attached sheet (do not use the older original sheet). Keep what it did right and fix only what is listed below.\n")

FIX = {
 "01": ("JOB-01 attempt 2 (the attached JOB-01-v2 is the base)",
  "KEEP: the foot order in all four poses is correct. Do not change which foot is ahead.\n"
  "FIX: (1) In both hop poses the arms must swing forward and a little up, elbows slightly bent, fists relaxed. Do NOT hold the fists in a boxing guard at the chest. (2) The face must be calm: a small closed smile, eyes level and looking ahead. It currently reads as a smirk. (3) In the crouches keep the back straight at about 45 degrees with the chest and head up."),
 "02": ("JOB-02 attempt 2",
  "FIX: (1) In the two side touches the fingertips must touch the floor about six inches OUTSIDE the outer edge of the foot, beyond the shoe, not at the shoe. (2) In poses 1, 5 and 6 the arms are straight and parallel with the upper arms touching the ears, not spread in a V. (3) Figures 2, 3 and 4 were 17 px apart. Draw every figure at about 85% scale so there is a wide gap between all six."),
 "04": ("JOB-04 attempt 3 (the attached JOB-04-v2 is the base)",
  "KEEP: the three rows, the T-shaped arms, and the progressive lift in all three poses.\n"
  "FIX: in ROW 3 pose 1 the legs are lifted off the floor. In pose 1 of every row he must lie completely flat with legs, belly and chest on the floor line. Only poses 2 and 3 lift."),
 "05": ("JOB-05 attempt 2",
  "FIX: (1) FOREHEAD pose: the forehead must be level with or BEHIND the line of the hands, with the hands visibly ahead of the forehead in the direction he faces. At the moment his head is in front of the hands. (2) CHIN pose: the chin must visibly touch the floor in front of the hands, with the elbows bent and the chest just above the floor, clearly lower than the UP pose. (3) Both rows: knees off the floor, palms and toes only."),
 "06": ("JOB-06 attempt 3 (the attached JOB-06-v2 is the base)",
  "FIX: (1) START: the feet and shins must lie flat on the floor, not raised. (2) TOP: lift the thighs, knees and shins clearly higher, so there is visible daylight between the thighs and the hands, at least twice the lift of the current sheet. (3) Keep both arms straight back with the palms under the front of the thighs."),
 "08": ("JOB-08 attempt 2",
  "FIX: (1) The two rows must be genuinely different cameras. ROW 1 a three-quarter FRONT view from the front and a little from the left; ROW 2 a strict SIDE view facing right. (2) In the jump poses both feet must be well off the floor: at least a quarter of the figure's height above the floor line (they are only one shoe-height up now), legs together under the hips, arms crossing near the body. (3) Stances: the front leg only slightly bent, the back leg straight, arms straight at shoulder height."),
 "09": ("JOB-09 attempt 2",
  "FIX: (1) In the two side touches the clasped fingertips must touch the floor about six inches OUTSIDE the outer edge of the foot, not on the shoe. (2) Poses 2, 3 and 4 must be a strict FRONT view, not turned. (3) Figures were 22 px apart. Draw every figure at about 80% scale so there is a wide gap between all six."),
 "14": ("JOB-14 attempt 2",
  "FIX: (1) In the two side touches the reverse-clasped fingertips must touch the floor about six inches OUTSIDE the outer edge of the foot, not on the shoe. (2) Poses 2, 3 and 4 must be a strict FRONT view, not turned. (3) Figures were 13 px apart. Draw every figure at about 80% scale so there is a wide gap between all six."),
 "17": ("JOB-17 attempt 2",
  "FIX: the brief asks for a three-quarter FRONT view, seen from the front and a little from one side, with his head nearer the camera and his feet farther away. The previous sheet is a pure side view. Redraw all three poses from the three-quarter front camera. Keep the three poses and the hands-slap-chest finish."),
 "26": ("JOB-26 attempt 2 (the attached JOB-26 is the base)",
  "FIX: (1) A floor seam runs straight across the 73% to 86% strip (at about 74% down). Redraw the flagstones so the whole strip from 73% to 86% is perfectly smooth with no seams or lines; put seams only above 70% and below 90%. (2) The large gold gears on the left are still big: make them about 30% smaller than they are now, in muted bronze. (3) Keep everything else as it is."),
}

lines = ["# Overnight batch C: retakes\n",
 "How to use: attach every file listed under ATTACH for each job (they are all in the `refs-A` / `refs-B` folders, plus last night's best sheet), then paste the whole job. "
 "One message per group is fine. Paste everything below the line.\n", "---\n",
 "Please do ALL of the jobs below, in order, by yourself, without asking me any questions. Give each result the label JOB-NN and show me the whole image. "
 "Count the limbs in every figure: exactly two arms and two legs. If a job cannot be done, say so in one line and continue. At the end list the finished and unfinished job numbers.\n",
 "ATTACH for sprite jobs: the character reference `c4-run-knees-waist-high.png` (always) plus the files named in each job.\n"]

ATTACH = {
 "01": "c4-run-knees-waist-high.png, REF-footswitch.png, JOB-01-v2.png (last night's best take)",
 "02": "c4-run-knees-waist-high.png, c3-ex1-toe-touching.png (layout only), JOB-02.png (last night's take)",
 "04": "c4-run-knees-waist-high.png, REF-backext-geometry.png, JOB-04-v2.png",
 "05": "c4-run-knees-waist-high.png, JOB-05.png",
 "06": "c4-run-knees-waist-high.png, JOB-06-v2.png",
 "08": "c4-run-knees-waist-high.png, JOB-08.png",
 "09": "c4-run-knees-waist-high.png, c3-ex1-toe-touching.png (layout only), JOB-09.png",
 "14": "c4-run-knees-waist-high.png, c3-ex1-toe-touching.png (layout only), JOB-14.png",
 "17": "c4-run-knees-waist-high.png, c4-ex4-wide-hand-push-up.png (layout only), JOB-17.png",
 "26": "bg-cand-workshop-landscape.png (the original base) and JOB-26.png (last night's take)",
}

order = ["01", "02", "04", "05", "06", "08", "09", "14", "17"]
for j in order:
    title, prompt = A[j]
    ft, fix = FIX[j]
    lines.append(f"=== JOB-{j} (RETAKE): {title} ===\nATTACH: {ATTACH[j]}\nPRODUCE: ONE image: the whole sheet. No separate figures.\nPROMPT:\n{prompt}\n\n{COMMON}\nWHAT TO FIX ({ft}):\n{fix}\n")

# JOB-26 background
title, prompt = B["26"]
ft, fix = FIX["26"]
lines.append(f"=== JOB-26 (RETAKE): {title} ===\nATTACH: {ATTACH['26']}\nPRODUCE: ONE image named bg-workshop-landscape-final.png\nPROMPT:\n{prompt}\n\nWHAT TO FIX ({ft}):\n{fix}\n")

# JOB-27 two more variations
title, prompt = B["27"]
lines.append("=== JOB-27 (MORE VARIATIONS): Pine forest master scene, two more variations ===\nATTACH: (nothing)\nPRODUCE: TWO more variations of the master scene\nPROMPT:\n" + prompt +
 "\n\nWHAT TO FIX: last night's variation 3 was the closest, but its ground started at about 58% down and the other variations at 60% to 62%. In both new variations the ground (the grass fringe along the horizon) must start exactly 56% down from the top, which is 605 px on a 1080 px high image, with the far mountains and foothills sitting on that line. The front trees, bushes and rocks keep their bases at about 74% down and nothing may extend below 76% down (last night's rocks and bushes dipped into the stage strip at the far edges). They stay in the far left and far right quarters; the middle half stays completely clear.\n")

open(out, "w", encoding="utf-8", newline="\n").write("\n".join(lines))
print("written", out, sum(len(x) for x in lines), "chars")
