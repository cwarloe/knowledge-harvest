#!/usr/bin/env python3
"""Prompts for the background layers: one MASTER scene, then each depth layer redrawn from it so they all match.

  python3 kit/prompt_bg.py --env forest                       # print the master + 7 layer prompts (landscape, morning)
  python3 kit/prompt_bg.py --env beach --format portrait --light golden --plane master
  python3 kit/prompt_bg.py --publish                          # write prompts/backgrounds.json + BACKGROUNDS.md for every environment and both formats

Why two steps: separate generations never agree on horizon, scale or light. One master scene fixes them; each layer is then traced from it.
The numbers (horizon, floor line, clear strip, base lines) come from config/theme.json (formats: ground, box), so they follow the build.
Layer stack, back to front: sky, clouds, far, near, ground, back, front. The ground is drawn BEFORE the back row and the front frame.
"""
import argparse, json, os, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
def jload(p): return json.load(open(p))


def numbers(theme, spec, fmt, env):
    F = theme["formats"][fmt]; W, H, floor = F["W"], F["H"], round(F["ground"] * 100)
    hz = floor - spec["horizon_above_floor"]; top = "horizon"
    gt = hz if env["ground_top"] == "horizon" else hz + 10                    # a beach's land begins at the shoreline, below the horizon
    boy_h = round(F["box"][1] / H * 100)
    return {"W": W, "H": H, "aspect": "wide 16:9" if W > H else "tall 9:16", "floor": floor, "horizon": hz, "ground_top": gt, "boy_h": boy_h,
            "strip_top": floor - 7, "strip_bottom": floor + 6, "back": max(floor - 16, gt + 3), "front": floor - 6, "shore_band": f"{hz + 1}% to {gt}% down"}


def fill(text, n): return text.format(**n)


PLANE_BASE = {   # what to say about where each plane sits and what must overlap, in numbers
    "sky": "It fills the whole image, edge to edge.",
    "clouds": "Keep every cloud above the {horizon}% line.",
    "far": "Its base sits on the horizon ({horizon}% down); extend its bottom down to {ext}% so nothing shows through when the ground is stacked on top.",
    "near": "Its base sits at {ground_top}% down; extend its bottom down to {ext}% so nothing shows through when the ground is stacked on top.",
    "ground": "Its top edge is at {ground_top}% down and it runs to the bottom of the image.",
    "back": "Bases at {back}% down.",
    "front": "Bases at {front}% down.",
}


def master(theme, spec, fmt, envk, light):
    env = spec["environments"][envk]; n = numbers(theme, spec, fmt, env); n["light"] = spec["lights"][light]
    lines = [f"Create ONE complete {n['aspect']} ({n['W']}x{n['H']}) background scene for a cartoon fitness video: {env['setting']}. No characters, no people, no animals, no text, no frame, no border.", "",
             fill(spec["style"], n), "", fill(spec["camera"], n), "", fill(spec["stage"], n), "", fill(spec["light"], n), "", fill(spec["depth"], n), "", fill(spec["keying"], n), "",
             "THE SEVEN PLANES, from the farthest to the nearest. Draw exactly these, each at its own depth, and nothing else:"]
    for i, pl in enumerate(spec["planes"], 1):
        n2 = dict(n, ext=n["ground_top"] + 8); txt = fill(env["planes"][pl], n2)
        lines.append(f"{i}. {spec['plane_names'][pl]}: {txt} {fill(PLANE_BASE[pl], n2)}")
    land = f"the far layer stands on the horizon at {n['horizon']}%" + ("" if n["ground_top"] == n["horizon"] else f" and the near layer ends at the shoreline at {n['ground_top']}%")
    lines += ["", f"BASE LINES: {land}; the ground begins at {n['ground_top']}% and runs to the bottom; the back row's bases sit at {n['back']}%; the front frame's bases sit at {n['front']}%."]
    return "\n".join(lines)


def layer(theme, spec, fmt, envk, light, plane):
    env = spec["environments"][envk]; n = numbers(theme, spec, fmt, env); n["light"] = spec["lights"][light]; n["ext"] = n["ground_top"] + 8
    if plane == "sky": bg = "This layer is fully opaque and fills the whole image edge to edge (no magenta). Draw the sky completely, including the parts that were behind the clouds and the mountains in the reference."
    elif plane == "ground": bg = f"Everything above the ground's top edge is perfectly flat solid magenta (#FF00FF). The ground itself is fully opaque. Draw it completely, including the parts hidden behind the back row and front frame in the reference."
    else: bg = "Everything that is not part of this layer is perfectly flat solid magenta (#FF00FF), nothing else: no gradient, no shadow, no floor line, no other layer. Draw each object completely, including any part that was hidden behind a nearer object in the reference."
    lines = [f"Using the attached scene image as the EXACT reference for style, colors, light, perspective, horizon and positions, redraw ONLY the {spec['plane_names'][plane]} as a separate image.", "",
             f"- Same size and shape as the reference ({n['aspect']}), with this layer at exactly the same position and scale as in the reference. Trace it; do not redesign it.",
             f"- {bg}", "- No characters, no text, no frame, no shadows that belong to other layers.", "",
             f"THIS LAYER: {fill(env['planes'][plane], n)}", f"POSITION: {fill(PLANE_BASE[plane], n)}"]
    if plane in ("back", "front"): lines.append(f"Keep the strip {n['strip_top']}% to {n['strip_bottom']}% down completely empty, and the middle of the image calm.")
    lines += ["", fill(spec["keying"], n)]
    return "\n".join(lines)


def gym_keeper(theme, spec, fmt):
    g = spec["gym_keeper"]; F = theme["formats"][fmt]; W, H, floor = F["W"], F["H"], round(F["ground"] * 100)
    n = {"W": W, "H": H, "aspect": "wide 16:9" if W > H else "tall 9:16", "floor": floor, "wall_floor": floor - 19, "strip_top": floor - 7, "strip_bottom": floor + 6, "mat_top": floor - 7, "mat_bottom": floor + 10}
    half = min(.48, F["box"][0] / W / 2 + .06); n.update(near_left=round((.5 - half) * 100), near_right=round((.5 + half) * 100), far_left=round((.5 - half + .03) * 100), far_right=round((.5 + half - .03) * 100))
    items = []
    if fmt == "landscape": items.append({"plane": "finish", "title": "Finishing pass on the keeper (attach the grey-floor gym)", "file": f"bg-gym-{fmt}-final.png", "prompt": g["finish"].format(**n)})
    else: items.append({"plane": "portrait-room", "title": "Tall version of the room (attach the finished wide gym)", "file": f"bg-gym-{fmt}-final.png", "prompt": g["portrait_room"].format(**n)})
    for m in g["mats"]: items.append({"plane": "mat-" + m["id"], "title": f"Floor mat overlay, {m['name']} (attach the finished gym of this shape)", "file": f"bg-gym-{fmt}-mat-{m['id']}.png", "prompt": g["mat"].format(name=m["name"], hex=m["hex"], border=m["border"], edge=m["edge"], **n)})
    return {"title": g["title"], "numbers": {k: n[k] for k in ("W", "H", "floor", "strip_top", "strip_bottom")} | {"horizon": n["wall_floor"], "ground_top": n["wall_floor"], "boy_h": round(F["box"][1] / H * 100), "back": n["strip_top"], "front": n["strip_bottom"]}, "items": items}


def candidates(theme, spec):
    F = theme["formats"]["landscape"]; W, H, floor = F["W"], F["H"], round(F["ground"] * 100)
    n = {"W": W, "H": H, "aspect": "wide 16:9", "floor": floor, "strip_top": floor - 7, "strip_bottom": floor + 6}
    return {"title": spec["candidates"]["title"], "numbers": {"W": W, "H": H, "floor": floor, "strip_top": n["strip_top"], "strip_bottom": n["strip_bottom"], "horizon": floor - 19, "ground_top": floor - 19, "boy_h": round(F["box"][1] / H * 100), "back": n["strip_top"], "front": n["strip_bottom"]},
            "items": [dict(i, prompt=i["prompt"].format(**n)) for i in spec["candidates"]["items"]]}


def build_all(theme, spec, light="morning"):
    out = {}
    for fmt in ("landscape", "portrait"):
        for envk, env in spec["environments"].items():
            n = numbers(theme, spec, fmt, env); stem = f"bg-{envk}-{fmt}"
            items = [{"plane": "master", "title": "Master scene (make this first)", "file": f"{stem}-master.png", "prompt": master(theme, spec, fmt, envk, light)}]
            for i, pl in enumerate(spec["planes"], 1):
                items.append({"plane": pl, "title": f"Layer {i}: {spec['plane_names'][pl].title()}", "file": f"{stem}-{i:02d}-{pl}.png", "prompt": layer(theme, spec, fmt, envk, light, pl)})
            out.setdefault(fmt, {})[envk] = {"title": env["title"], "numbers": {k: n[k] for k in ("W", "H", "floor", "horizon", "ground_top", "boy_h", "strip_top", "strip_bottom", "back", "front")}, "items": items}
    for fmt in ("landscape", "portrait"): out[fmt]["gym-keeper"] = gym_keeper(theme, spec, fmt)
    out["landscape"]["candidates"] = candidates(theme, spec)
    return out


HOW = ["Open a new chat and make the MASTER scene first. Ask for 4 variations and pick one; the pick decides the look of every layer.",
       "In the SAME chat, attach the master you picked and paste layer 1, then layer 2, and so on, one at a time. Keeping one chat is what keeps the layers matching.",
       "If your tool cannot attach an image, say 'the scene above' instead of 'the attached scene'.",
       "Check each layer: the base lines match the master, the stage strip is empty, the middle is calm, and the edges against the magenta are crisp (no glow). Ask for a retake of just that layer if not.",
       "Send the layers back in the chat (or import them with kit/import_backdrop.py). They stack in this order, back to front: sky, clouds, far, near, ground, back, front.",
       "To mix and match, use layers from different environments: every set shares the same horizon, floor line and depth rules, so far layers from one scene sit on the ground of another. Keep the LIGHT line the same across the sets you combine."]


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--env", default="forest"); ap.add_argument("--format", default="landscape", choices=["landscape", "portrait"]); ap.add_argument("--light", default="morning")
    ap.add_argument("--plane", default="all", help="master, sky, clouds, far, near, ground, back, front, or all"); ap.add_argument("--publish", action="store_true")
    a = ap.parse_args(); theme = jload(os.path.join(ROOT, "config", "theme.json")); spec = jload(os.path.join(ROOT, "prompts", "backgrounds.spec.json"))
    if a.publish:
        allp = build_all(theme, spec)
        json.dump({"how": HOW, "lights": spec["lights"], "planes": spec["planes"], "formats": allp}, open(os.path.join(ROOT, "prompts", "backgrounds.json"), "w"), indent=1)
        L = ["# Background layer prompts", "", "Generated by `kit/prompt_bg.py --publish` from `prompts/backgrounds.spec.json` and `config/theme.json`. Landscape, morning light. Portrait numbers and other light settings: `kit/prompt_bg.py --help`.", "", "## How to use", ""] + [f"{i}. {t}" for i, t in enumerate(HOW, 1)]
        for envk, e in allp["landscape"].items():
            nn = e["numbers"]; L += ["", f"## {e['title']}  (`{envk}`)", "", f"Landscape {nn['W']}x{nn['H']}: horizon {nn['horizon']}%, ground starts {nn['ground_top']}%, boy's feet on {nn['floor']}%, back-row bases {nn['back']}%, front-frame bases {nn['front']}%.", ""]
            for it in e["items"]: L += [f"### {it['title']}  (save as `{it['file']}`)", "", "```", it["prompt"], "```", ""]
        open(os.path.join(ROOT, "prompts", "BACKGROUNDS.md"), "w").write("\n".join(L) + "\n"); print("wrote prompts/backgrounds.json and prompts/BACKGROUNDS.md ({} environments, 2 formats)".format(len(spec["environments"]))); return
    if a.plane in ("all", "master"): print("=== MASTER ===\n" + master(theme, spec, a.format, a.env, a.light))
    for pl in spec["planes"]:
        if a.plane in ("all", pl): print(f"\n=== LAYER: {pl} ===\n" + layer(theme, spec, a.format, a.env, a.light, pl))


if __name__ == "__main__": main()
