#!/usr/bin/env python3
"""Make a Word document with every image prompt a chart still needs, ready to paste into an image tool.

  python3 kit/make_prompt_doc.py --data path/to/5bx-charts.json --chart 2 --out chart2-prompts.docx

Everything comes from prompts/strips.json, config/character.json and the data file, so rebuilding
after any change refreshes the document. Needs: pip install python-docx pillow
"""
import argparse, io, json, os, sys
from docx import Document
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Inches, Pt, RGBColor
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE); sys.path.insert(0, HERE)
from prompt import build, booklet_text
SITE = "https://cwarloe.github.io/knowledge-harvest"
INK, MUTED, ACCENT = RGBColor(0x12, 0x1C, 0x26), RGBColor(0x4B, 0x5B, 0x69), RGBColor(0x13, 0x5A, 0x9E)


def shade(cell, hex_fill):
    tcPr = cell._tc.get_or_add_tcPr(); shd = OxmlElement("w:shd"); shd.set(qn("w:val"), "clear"); shd.set(qn("w:color"), "auto"); shd.set(qn("w:fill"), hex_fill); tcPr.append(shd)

def borders(table, color="C9D6E0"):
    tblPr = table._tbl.tblPr; b = OxmlElement("w:tblBorders")
    for edge in ("top", "left", "bottom", "right", "insideH", "insideV"):
        e = OxmlElement(f"w:{edge}"); e.set(qn("w:val"), "single"); e.set(qn("w:sz"), "4"); e.set(qn("w:space"), "0"); e.set(qn("w:color"), color); b.append(e)
    tblPr.append(b)

def para(doc, text="", size=11, bold=False, color=INK, after=6, italic=False, style=None):
    p = doc.add_paragraph(style=style); r = p.add_run(text); r.font.size = Pt(size); r.bold = bold; r.italic = italic; r.font.color.rgb = color
    p.paragraph_format.space_after = Pt(after); return p

def box(doc, text, label):
    """A shaded single-cell box holding text to copy, in a monospace face."""
    lab = para(doc, label, size=10, bold=True, color=MUTED, after=2)
    t = doc.add_table(rows=1, cols=1); t.alignment = WD_TABLE_ALIGNMENT.CENTER; borders(t); c = t.rows[0].cells[0]; shade(c, "F1F5F8")
    trPr = t.rows[0]._tr.get_or_add_trPr(); cs = OxmlElement("w:cantSplit"); trPr.append(cs)          # the box moves whole to the next page, never splits
    lab.paragraph_format.keep_with_next = True
    c.paragraphs[0].text = ""
    first = True
    for line in text.split("\n"):
        p = c.paragraphs[0] if first else c.add_paragraph(); first = False
        r = p.add_run(line); r.font.name = "Consolas"; r._element.rPr.rFonts.set(qn("w:eastAsia"), "Consolas"); r.font.size = Pt(9); p.paragraph_format.space_after = Pt(1)
    sp = doc.add_paragraph(); sp.paragraph_format.space_after = Pt(0); sp.paragraph_format.space_before = Pt(0)
    for r in sp.runs: r.font.size = Pt(4)

def bullets(doc, items, size=10):
    for it in items:
        p = doc.add_paragraph(style="List Bullet"); r = p.add_run(it); r.font.size = Pt(size); p.paragraph_format.space_after = Pt(1)

def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--data", required=True); ap.add_argument("--chart", type=int, required=True); ap.add_argument("--out", required=True)
    a = ap.parse_args()
    data = json.load(open(a.data)); ch = json.load(open(os.path.join(ROOT, "config", "character.json"))); sp = json.load(open(os.path.join(ROOT, "prompts", "strips.json")))
    reg = json.load(open(os.path.join(ROOT, "config", "strips.json")))
    order = ["ex1", "ex2", "ex3", "ex4", "run", "jump"]
    specs = sorted([(k, v) for k, v in sp["strips"].items() if v.get("chart") == a.chart], key=lambda kv: order.index(kv[1]["slot"]))
    if not specs: sys.exit(f"no prompts for chart {a.chart} in prompts/strips.json")
    chart = next(c for c in data["charts"] if c["id"] == a.chart)
    def pretty(v):
        i = {"ex1": 0, "ex2": 1, "ex3": 2, "ex4": 3, "run": 4}.get(v["slot"])
        name = chart["exercises"][i]["name"] if i is not None else chart["exercises"][4].get("jumpName", v["exercise"])
        return name[0].upper() + name[1:]

    doc = Document(); sec = doc.sections[0]; sec.left_margin = sec.right_margin = Inches(0.75); sec.top_margin = sec.bottom_margin = Inches(0.6)
    st = doc.styles["Normal"]; st.font.name = "Calibri"; st.font.size = Pt(11)
    for name, size in (("Heading 1", 20), ("Heading 2", 15), ("Heading 3", 12)):
        h = doc.styles[name]; h.font.name = "Calibri"; h.font.size = Pt(size); h.font.bold = True; h.font.color.rgb = INK

    doc.add_heading(f"Chart {a.chart}: image prompts", 0).runs[0].font.size = Pt(26)
    para(doc, f"Everything to make the chart {a.chart} pose strips in an image tool such as Grok Imagine. Paste-ready, with the plan's own wording next to each prompt.", size=12, color=MUTED, after=10)

    doc.add_heading("What to make", 1)
    rows = [(k, v) for k, v in specs]
    t = doc.add_table(rows=1, cols=5); borders(t); t.alignment = WD_TABLE_ALIGNMENT.CENTER
    for i, h in enumerate(("#", "Image", "Poses", "View", "Save it as")):
        c = t.rows[0].cells[i]; shade(c, "E3ECF2"); c.paragraphs[0].text = ""; r = c.paragraphs[0].add_run(h); r.bold = True; r.font.size = Pt(10)
    for n, (k, v) in enumerate(rows, 1):
        cells = t.add_row().cells; view = "Front" if "FRONT" in v.get("view", "") else "Side"
        for c, txt in zip(cells, (str(n), pretty(v), str(len(v["poses"])), view, v["suggest"]["file"])):
            c.paragraphs[0].text = ""; r = c.paragraphs[0].add_run(txt); r.font.size = Pt(10)
    for row in t.rows:
        for c, w in zip(row.cells, (0.4, 2.2, 0.7, 0.7, 2.7)): c.width = Inches(w)
    doc.add_paragraph().paragraph_format.space_after = Pt(2)
    if not any(v["slot"] == "run" for _, v in specs):
        para(doc, f"Nothing to make for the stationary run: chart {a.chart} words it the same as an earlier chart, so that chart's run strip is reused.", size=10.5, color=MUTED)

    doc.add_heading("How to use it", 1)
    bullets(doc, [
        "For each image below, copy a prompt into your tool. Ask for a wide 16:9 picture, at least about 1300 pixels across, and 4 variations if the tool offers that.",
        "Two prompts are given for every image. If your tool lets you attach a reference image, attach the standing reference strip (below) and use the first prompt. If not, use the second, which describes the character in words.",
        "Pick the take whose form matches the booklet wording shown above each prompt, not the prettiest one. Use the 'check before you keep a take' list.",
        "Background: a flat magenta is what the prompts ask for. If your tool gives a real transparent PNG instead, that works too. A checkerboard painted into the picture does not count as transparent.",
        "Send me the best take of each image (all four if you like) by attaching them in the chat. I will check the form against the booklet, cut them out, and build chart 2.",
    ])

    h = doc.add_heading("The reference image", 2); h.paragraph_format.keep_with_next = True
    q = para(doc, "Chart 1's standing strip. Download the full-size file from:", size=10.5, after=2); q.paragraph_format.keep_with_next = True
    q = para(doc, f"{SITE}/strips/ex1-toe-touching.png", size=10.5, color=ACCENT, after=6); q.paragraph_format.keep_with_next = True
    img = Image.open(os.path.join(ROOT, "sheets", "ex1-toe-touching.png")).convert("RGB"); img.thumbnail((1100, 1100)); buf = io.BytesIO(); img.save(buf, "JPEG", quality=82); buf.seek(0)
    doc.add_picture(buf, width=Inches(5.6)); para(doc, "This is a preview. Use the full-size file from the link when you attach it. For a prone exercise (lying down), the standing strip is the right reference: a lying-down strip can leak its pose into a different exercise.", size=9.5, color=MUTED, italic=True)

    for n, (k, v) in enumerate(specs, 1):
        doc.add_page_break(); doc.add_heading(f"{n}. {pretty(v)}", 1)
        b = booklet_text(data, a.chart, v["slot"])
        para(doc, f"Save as: {v['suggest']['file']}   |   {len(v['poses'])} poses   |   {'FRONT view' if 'FRONT' in v.get('view', '') else 'Side view'}", size=10.5, bold=True, color=ACCENT, after=6)
        para(doc, "What the booklet says", size=11, bold=True, after=2)
        bullets(doc, [f"Starts: {b['start']}", f"Movement: {b['movement']}"] + [f"Note: {x}" for x in b["notes"]])
        para(doc, "Check before you keep a take", size=11, bold=True, after=2); bullets(doc, v["check"])
        if v.get("draft"): para(doc, "My decisions, for you to check", size=11, bold=True, after=2); bullets(doc, v["draft"])
        box(doc, build(v, ch, True), "PROMPT 1: with the reference image attached")
        box(doc, build(v, ch, False), "PROMPT 2: no reference image (the character described in words)")

    doc.add_page_break(); doc.add_heading("The character, on its own", 1)
    para(doc, "Already inside every prompt above. Here for tools where you set the character once.", size=10.5, color=MUTED)
    box(doc, ch["description"] + ".", "The character"); box(doc, ch["background"], "The background")
    para(doc, "Locked: " + " ".join(ch["locked"]), size=10.5)
    doc.add_heading("What to look out for", 2)
    bullets(doc, ["Shoes must be blue. No green shoes.", "The same boy in every pose: spiky black hair, cyan tank, red shorts, white socks.",
                  "A ground shadow under the feet is fine; it gets removed. Text, labels and arrows in the picture are not.",
                  "Form is checked against the booklet's wording, not by an exercise expert. Someone who knows the exercises should look at the finished video.",
                  "I have not used Grok Imagine. If it cannot take a reference image or a wide shape, tell me what it offers and I will adjust the prompts."])
    para(doc, f"Generated by kit/make_prompt_doc.py from the project's own files. Method and every earlier prompt: {SITE}/prompts.html", size=9, color=MUTED, italic=True)
    doc.save(a.out); print("wrote", a.out)

if __name__ == "__main__":
    main()
