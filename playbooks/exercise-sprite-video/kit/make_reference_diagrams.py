#!/usr/bin/env python3
"""Draw the two schematic references an image tool needs for movements it keeps getting wrong. Stick figures on purpose: they say WHERE the limbs are, not how the boy looks.

  python3 kit/make_reference_diagrams.py        # writes prompts/refs/REF-footswitch.png and REF-backext-geometry.png
The prompts tell the tool to copy the positions only, never the drawing style or the labels.
"""
import os
from PIL import Image, ImageDraw, ImageFont

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); OUT = os.path.join(ROOT, "prompts", "refs"); os.makedirs(OUT, exist_ok=True)
FONT = os.path.join(ROOT, "assets", "fonts", "DejaVuSans-Bold.ttf")
def font(n): return ImageFont.truetype(FONT, n)
NEAR, FAR, INK, BG, GRID = (240, 150, 40), (40, 70, 140), (30, 30, 30), (245, 245, 240), (200, 200, 195)


def limb(d, pts, col, w=14): d.line(pts, fill=col, width=w, joint="curve"); [d.ellipse([x - w // 2, y - w // 2, x + w // 2, y + w // 2], fill=col) for x, y in pts]
def shoe(d, x, y, col): d.rounded_rectangle([x - 8, y - 12, x + 62, y + 6], radius=8, fill=col, outline=INK, width=2)     # toe points right; x is the heel, one shoe length is 70


def foot_pose(d, ox, kind, ahead, title, sub):
    """Side view, facing right. NEAR = his right (orange); FAR = his left (dark blue). kind: crouch | hop. ahead: 'near' | 'far'."""
    gy = 430; d.line([(ox - 20, gy), (ox + 380, gy)], fill=INK, width=3)
    off = 70                                                      # one full shoe length between the toes
    if kind == "crouch":
        hip, sh, head = (ox + 110, 300), (ox + 190, 215), (ox + 215, 170)
        legs = {"near": ((ox + 235, 345), (ox + 225 + (off if ahead == "near" else 0), gy - 6)), "far": ((ox + 220, 345), (ox + 215 + (off if ahead == "far" else 0), gy - 6))}
        arms = [sh, (ox + 232, 290), (ox + 238, 338)]             # straight arm from the shoulder to the knee
    else:
        hip, sh, head = (ox + 150, 235), (ox + 150, 130), (ox + 150, 88)
        fx = {"near": ox + 130 + (off if ahead == "near" else -20), "far": ox + 130 + (off if ahead == "far" else -20)}
        legs = {"near": ((ox + 160, 305), (fx["near"], 365)), "far": ((ox + 150, 305), (fx["far"], 360))}
        arms = [sh, (ox + 205, 175), (ox + 235, 150)]             # arms swing forward and a little up
    for who in ("far", "near"):                                   # far limb first, so near ends up on top
        col = FAR if who == "far" else NEAR; knee, foot = legs[who]; limb(d, [hip, knee, foot], col, 16); shoe(d, foot[0] - 8, foot[1] + 8, col)
    limb(d, [hip, sh], INK, 18); limb(d, arms, NEAR, 12); d.ellipse([head[0] - 26, head[1] - 26, head[0] + 26, head[1] + 26], fill=(250, 210, 170), outline=INK, width=3)
    pass


def footswitch():
    im = Image.new("RGB", (1680, 700), BG); d = ImageDraw.Draw(im)
    for i, (kind, ahead, title, sub) in enumerate((("crouch", "near", "1  CROUCH", "RIGHT (near, orange) foot ahead"), ("hop", "far", "2  HOP", "feet swapped: LEFT (far, dark) ahead"),
                                                  ("crouch", "far", "3  CROUCH", "LEFT (far, dark) foot ahead"), ("hop", "near", "4  HOP", "feet swapped: RIGHT (near) ahead"))):
        tile = Image.new("RGB", (420, 480), BG); foot_pose(ImageDraw.Draw(tile), 0, kind, ahead, title, sub); im.paste(tile, (10 + i * 415, 95))
        d.text((10 + i * 415, 18), title, fill=INK, font=font(24)); d.text((10 + i * 415, 52), sub, fill=INK, font=font(17))
    d.text((10, 590), "Schematic of WHERE the feet are, seen from the side, boy facing right. Near foot = his right (orange). Far foot = his left (dark blue).", fill=INK, font=font(18))
    d.text((10, 620), "The foot that is ahead is ahead by one full shoe length. In the air the feet have already swapped, ready to land the other way round.", fill=INK, font=font(18))
    d.text((10, 650), "Copy the foot POSITIONS only. Do NOT copy the stick-figure style or any of this text. Draw the cartoon boy from the character reference.", fill=(170, 30, 30), font=font(18))
    im.save(os.path.join(OUT, "REF-footswitch.png")); return im


def backext():
    im = Image.new("RGB", (1680, 800), BG); d = ImageDraw.Draw(im); gy = 300
    import math
    def lying(ox, chest_deg, thigh_deg, title):
        d.line([(ox - 190, gy), (ox + 290, gy)], fill=INK, width=3)
        hipx, hipy = ox + 180, gy - 14                              # the hips and lower belly stay on the floor
        # legs rise from the hips toward the left (feet on the left), straight and together
        lx = hipx - 170 * math.cos(math.radians(thigh_deg)); ly = hipy - 170 * math.sin(math.radians(thigh_deg)); limb(d, [(hipx, hipy), (lx, ly)], NEAR, 18); shoe(d, int(lx) - 52, int(ly) - 8, NEAR)
        # chest rises toward the right; head on the right
        cx = hipx + 150 * math.cos(math.radians(chest_deg)); cy = hipy - 150 * math.sin(math.radians(chest_deg)); limb(d, [(hipx, hipy), (cx, cy)], INK, 24)
        d.ellipse([cx + 4, cy - 38, cx + 56, cy + 14], fill=(250, 210, 170), outline=INK, width=3); d.text((ox - 190, 30), title, fill=INK, font=font(22))
    lying(200, 0, 0, "START: flat on the floor"); lying(660, 14, 12, "LIFTING"); lying(1130, 38, 28, "TOP: chest about 35 deg, legs about 25 deg")
    d.text((20, 62), "SIDE VIEW, head on the right, feet on the left. Belly, hips and lower belly stay on the floor line in every pose.", fill=INK, font=font(17))
    # top-down panel
    oy = 400; d.text((20, oy), "TOP-DOWN VIEW of any pose: the arms stretch straight out SIDEWAYS at right angles, like the letter T (exactly two arms).", fill=INK, font=font(17))
    cx, cy = 840, oy + 170; d.rounded_rectangle([cx - 230, cy - 26, cx + 130, cy + 26], radius=24, fill=INK)             # body, head on the right
    d.ellipse([cx + 118, cy - 34, cx + 190, cy + 34], fill=(250, 210, 170), outline=INK, width=3)
    limb(d, [(cx + 60, cy - 20), (cx + 60, cy - 135)], NEAR, 16); limb(d, [(cx + 60, cy + 20), (cx + 60, cy + 135)], FAR, 16)  # one arm each side, perpendicular
    limb(d, [(cx - 230, cy - 12), (cx - 330, cy - 12)], NEAR, 14); limb(d, [(cx - 230, cy + 12), (cx - 330, cy + 12)], NEAR, 14)  # legs together
    d.text((cx + 85, cy - 150), "arm", fill=INK, font=font(16)); d.text((cx + 85, cy + 130), "arm", fill=INK, font=font(16))
    d.text((20, 750), "Copy the ANGLES and positions only. Do NOT copy the stick-figure style or any of this text. Draw the cartoon boy from the character reference.", fill=(170, 30, 30), font=font(18))
    im.save(os.path.join(OUT, "REF-backext-geometry.png")); return im


def scissor_stances():
    """Chart 1 scissor jumps. Booklet: 'Stand with right leg and left arm extended forward, and left leg and right arm extended
    backward. Jump up, change position of arms and legs before landing (arms shoulder high).' Side view facing right, so his
    RIGHT side is the near side (orange) and his LEFT side the far side (dark blue)."""
    im = Image.new("RGB", (1680, 760), BG); d = ImageDraw.Draw(im); gy = 520

    def figure(ox, front, airborne=False):
        lift = 70 if airborne else 0; hip = (ox + 200, 340 - lift); sh = (ox + 200, 215 - lift); head = (ox + 203, 172 - lift)
        legs = {}
        for who in ("near", "far"):
            fwd = (who == front)
            if airborne: knee, foot = (hip[0] + (35 if fwd else -20), hip[1] + 95), (hip[0] + (20 if fwd else -35), hip[1] + 175)
            elif fwd: knee, foot = (hip[0] + 70, hip[1] + 95), (hip[0] + 110, gy - 6)               # front leg: slight bend
            else: knee, foot = (hip[0] - 50, hip[1] + 95), (hip[0] - 105, gy - 6)                 # back leg: straight
            legs[who] = (knee, foot)
        arm_front = "far" if front == "near" else "near"                                          # opposite arm to the front leg
        arms = {who: [sh, (sh[0] + (95 if who == arm_front else -95), sh[1] + 4), (sh[0] + (175 if who == arm_front else -175), sh[1] + 6)] for who in ("near", "far")}
        if airborne: arms = {who: [sh, (sh[0] + (40 if who == arm_front else -40), sh[1] + 60), (sh[0] + (60 if who == arm_front else -60), sh[1] + 120)] for who in ("near", "far")}
        for who in ("far", "near"):
            col = FAR if who == "far" else NEAR; knee, foot = legs[who]; limb(d, [hip, knee, foot], col, 16); shoe(d, foot[0] - 8, foot[1] + 8, col)
        limb(d, [hip, sh], INK, 18)
        for who in ("far", "near"): limb(d, arms[who], FAR if who == "far" else NEAR, 12)
        d.ellipse([head[0] - 26, head[1] - 26, head[0] + 26, head[1] + 26], fill=(250, 210, 170), outline=INK, width=3)

    for i, (title, sub, front, air) in enumerate((("1  STANCE A", "RIGHT leg (orange) forward\nLEFT arm (blue) forward", "near", False),
                                                  ("2  JUMP", "both feet off the floor,\nswitching", "far", True),
                                                  ("3  STANCE B", "LEFT leg (blue) forward\nRIGHT arm (orange) forward", "far", False),
                                                  ("4  JUMP", "both feet off the floor,\nswitching", "near", True))):
        ox = 10 + i * 415; d.line([(ox + 10, gy), (ox + 400, gy)], fill=INK, width=3); figure(ox, front, air)
        d.text((ox + 10, 18), title, fill=INK, font=font(24)); d.multiline_text((ox + 10, 52), sub, fill=INK, font=font(16), spacing=4)
    d.text((10, 600), "Side view, boy facing right. His RIGHT side is nearer the camera (orange); his LEFT side is farther (dark blue).", fill=INK, font=font(18))
    d.text((10, 630), "Stances: front knee slightly bent, back leg STRAIGHT, body upright, arms straight at shoulder height. Each stance is the mirror of the other.", fill=INK, font=font(18))
    d.text((10, 690), "Copy the POSITIONS only. Do NOT copy the stick-figure style or any of this text. Draw the cartoon boy from the character reference.", fill=(170, 30, 30), font=font(18))
    im.save(os.path.join(OUT, "REF-scissor-stances.png")); return im


def backext_hands():
    """Chart 2 back extension. Booklet: 'Front lying, palms placed under thighs. Raise head, shoulders, and both legs. Keep legs
    straight, both thighs must clear the palms.' Side view, head on the right, feet on the left."""
    import math
    im = Image.new("RGB", (1680, 620), BG); d = ImageDraw.Draw(im); gy = 330

    def lying(ox, chest_deg, leg_deg, title):
        d.line([(ox - 20, gy), (ox + 760, gy)], fill=INK, width=3)
        hip = (ox + 400, gy - 16)
        hand = (hip[0] - 95, gy - 6)                                          # palm flat under the front of the thigh, fixed
        sh = (hip[0] + 190 * math.cos(math.radians(chest_deg)), hip[1] - 190 * math.sin(math.radians(chest_deg)))
        knee = (hip[0] - 170 * math.cos(math.radians(leg_deg)), hip[1] - 170 * math.sin(math.radians(leg_deg)))
        foot = (hip[0] - 340 * math.cos(math.radians(leg_deg)), hip[1] - 340 * math.sin(math.radians(leg_deg)))
        limb(d, [hip, knee, foot], NEAR, 20); shoe(d, int(foot[0]) - 52, int(foot[1]) - 6, NEAR)
        limb(d, [hip, sh], INK, 26)
        elbow = ((sh[0] + hand[0]) / 2, (sh[1] + hand[1]) / 2 + 4); limb(d, [sh, elbow, hand], (200, 120, 30), 11)   # straight arm back to the hand
        d.ellipse([hand[0] - 16, hand[1] - 6, hand[0] + 16, hand[1] + 6], fill=(200, 120, 30))
        hx, hy = sh[0] + 34 * math.cos(math.radians(chest_deg)), sh[1] - 34 * math.sin(math.radians(chest_deg))
        d.ellipse([hx - 28, hy - 28, hx + 28, hy + 28], fill=(250, 210, 170), outline=INK, width=3)
        d.text((ox, 30), title, fill=INK, font=font(22))
        d.text((hand[0] - 40, gy + 14), "hand", fill=INK, font=font(16))

    lying(20, 0, 0, "START: completely flat. Palms under the front of the thighs.")
    lying(860, 22, 26, "TOP: head, chest and BOTH legs up. Thighs clear the hands.")
    d.text((20, 470), "Side view, head on the right, feet on the left. The hands do NOT move: same spot under the thighs in every pose.", fill=INK, font=font(18))
    d.text((20, 500), "In TOP there is a visible gap between each thigh and the hand under it. Legs straight, knees locked. LIFTING is halfway between.", fill=INK, font=font(18))
    d.text((20, 560), "Copy the POSITIONS only. Do NOT copy the stick-figure style or any of this text. Draw the cartoon boy from the character reference.", fill=(170, 30, 30), font=font(18))
    im.save(os.path.join(OUT, "REF-backext-hands.png")); return im


if __name__ == "__main__": footswitch(); backext(); scissor_stances(); backext_hands(); print("wrote", OUT)
