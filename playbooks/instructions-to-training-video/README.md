# Instructions → Training Video

Turn a written, step-by-step procedure (docx, PDF, slides, web page, or rough notes) into a short
animated walkthrough video: one scene per step, schematic UI, real screenshots with callouts,
and a burned-in caption bar. No screen recording, no video editor.

First built from an ITM 310 Power BI assignment (External Data), reverse-engineered from an
instructor's Claude-made walkthrough video. Output: 2:37, 16 scenes, 1280×720, ~3.7 MB.

## Pipeline

| # | Stage | What happens | Only stage that changes per medium? |
|---|-------|--------------|------|
| 1 | **Extract** | `scripts/extract.sh <file>` → `extracted/text.md` + `extracted/media/` | **Yes** |
| 2 | **Storyboard** | One scene per numbered step: chip label, title, 1–4 numbered actions, caption, duration | No |
| 3 | **Build** | One HTML file; each scene is a `<section>`; `render(t)` draws the frame for time *t* | No |
| 4 | **Check** | `render.py scenes.html out --stills 5,30,62` → contact sheet; fix layout | No |
| 5 | **Render** | `render.py scenes.html out.mp4` → Playwright frames → ffmpeg | No |
| 6 | *(opt)* **Narrate** | TTS per caption; set each scene's duration to its clip length; mux | No |

Example scene file: `template/example-external-data.html` (copy it, swap the scenes array `SC`).

## Reusable lessons

### Reverse-engineering someone else's video
- **Read the artifact for clues before guessing tools.** Labels like "(schematic)", a constant caption
  bar, typing-cursor formulas, and "screenshots from your assignment" told us: HTML-drawn scenes +
  images pulled from the source doc + headless render. Not a screen recording.
- Sample frames at ~0%, 25%, 50%, 85% to see the scene grammar (title → step scenes → check → submit).

### Extraction
- **A .docx/.pptx is a zip.** Screenshots are in `word/media/` or `ppt/media/`.
- **Use pandoc for text**, because it keeps each image *in place* in the text, so you know which image goes with which step.
- **Crop big screenshots to the region that matters** (e.g., just the dialog, just the menu). Full screenshots shrink to unreadable.
- Tiny inline icons (e.g., a 52×60 px "Model view" button) work as inline glyphs, not hero images.

### Storyboarding (instructional design)
- **One step = one scene** (segmenting). Chip labels mirror the doc's numbering ("STEP 2c") so learners can cross-reference.
- **Caption = the exact action**, in imperative voice. It doubles as the narration script.
- **Schematic UI over screenshots for "do this" moments** (coherence and less extraneous load): show only the pane that matters.
  Use **real screenshots for "check your work" moments** (authenticity: "it should look like this").
- Pacing: 6–15 s per scene; reveal numbered actions one at a time (signaling). Learners can pause.
- End with a "should look similar to this" scene, then the turn-in step.

### Building scenes
- **Deterministic `render(t)` beats CSS animations.** Every frame comes from time alone, so you get frame-perfect
  renders, can jump to any moment for debugging (`render(42)` in the console), and there are no timer races.
- Small helpers cover almost everything: `P(lt, start, dur)` (eased 0→1), `fade(el, v)`, `stepIn(scene, lt, times)`,
  typed text via `s.slice(0, k*s.length)`, pulsing rings via `abs(sin(t))`.
- **Gotcha: a flex container eats the spaces around inline `<b>`.** Captions rendered as "theTop Salestable".
  Fix: wrap caption contents in a single `<span>`.
- **Gotcha: absolute-positioned diagrams overflow.** Check the bottom edge of canvases at the moment of greatest content.

### Verification
- **Render a contact sheet of stills before the full render.** It's about 5 s versus about 2.5 min, and it caught 3 layout bugs.
- After rendering, extract frames from the *MP4 itself* (not the HTML) and check them again.
- **Source docs contradict themselves.** ("Metric" vs. "Metrics" table, "YearSalesRank" vs. "YearsSalesRank".)
  Trust the screenshots, use that spelling, and flag the discrepancy.

### Delivery
- **Never render straight into the folder people download from.** A half-written MP4 got synced and the
  download cut off early. Render to temp, verify a full decode (`ffmpeg -i out.mp4 -f null -`), then move it in.
- **Compatibility encode:** H.264 Main@4.0, `yuv420p`, constant fps, `+faststart`, and a silent AAC track.
  `render.py` does all of this.

### Medium swap cheat sheet
| Source | Text | Images | Captions from |
|--------|------|--------|---------------|
| docx | `pandoc` | `word/media/` | step text |
| pptx | slide XML | `ppt/media/` | **speaker notes** |
| PDF | `pdftotext -layout` | `pdfimages -png` | step text |
| Web/wiki | saved HTML | saved images | headings + steps |
| Rough notes | as-is | none (all schematic) | write them |

### Process / tooling notes
- Browser-extension page reads can fail when the tab changes. If so, ask for the file as an upload instead of retrying.
- Budget: about 1 hour of Claude work for a 2–3 min video; the render itself takes ~1 min per minute of video at 24 fps.

## Run it with an agent

Paste this into Claude Code (or any agent that can run shell commands) with this folder available and your source file attached or in the working directory:

```
Turn <SOURCE FILE> into a short training walkthrough video.

Follow playbooks/instructions-to-training-video/README.md.

1. Run scripts/extract.sh on the source. Read extracted/text.md and look at the
   images in extracted/media/ so you know which image goes with which step.
2. Write a storyboard first and show it to me: one scene per numbered step, with
   chip label (match the source numbering), title, 1-4 actions, caption, and
   duration. Flag anything in the source that contradicts itself and say which
   version you will use. Wait for my OK.
3. Copy template/example-external-data.html and replace the SC array with the new
   scenes. Use schematic UI for "do this" steps and real screenshots (cropped to
   the part that matters) for "check your work" steps. Captions are imperative and
   double as the narration script.
4. Run render.py with --stills on a spread of times and fix any layout problems.
5. Run the full render to a temp file, verify it decodes, then move it into place.
6. Tell me the length, scene count, and any decisions I should look at.

Do not invent steps, menu names, or values that are not in the source.
```

**Install:** `pip install playwright pillow`, plus `ffmpeg` and `pandoc` (and `poppler-utils` for PDFs). If Playwright can't find its browser, point `CHROMIUM_PATH` at an installed Chromium and `render.py` will use it.

**Tested:** `extract.sh` on the ITM 310 External Data docx (140 lines of text, 10 images) and `render.py --stills` on the example scene file both ran cleanly from a fresh environment.

## Worked example

The first run used the ITM 310 *External Data* Power BI assignment (a Word file with 10 screenshots) and produced a 2:37, 16-scene, 1280×720 MP4 of about 3.7 MB. The scene file for it is `template/example-external-data.html`.

The source document and the finished video are course material, so they are **not** stored in this repository. Keep your own pair next to this folder when you work, and don't commit them unless you own the rights to share them.

### Second and third runs: web documentation as the source

Two more videos were built from online documentation instead of a Word file: a Security Onion *groupby* walkthrough (2:36, 13 scenes) and a Wireshark *first look* primer (2:14, 11 scenes). What they added to the playbook:

- **Web pages are a fine source.** `curl` the page, `pandoc -f html -t plain --wrap=none` for text, and list the `<img src>` tags to see which screenshots exist. If `curl` is refused, the sandbox's network allow-list is the first thing to check, not the page.
- **Real data beats placeholder data.** For the Wireshark primer, every packet row, byte and line of stream text was pulled from a real capture with `tshark`, then drawn into a schematic window. Nothing on screen was typed from memory.
- **Check every label against the docs.** The first draft of the right-click menu used item names from memory. The docs table had different ones. Look up each menu item, button and field name before it goes on screen.
- **If the video sits in front of a lesson, don't solve the lesson.** Practice on a part the lesson already explains, and finish with a hand-off scene that tells the learner what to do next. Written steps next to the video mean it's optional.
- **Know who owns the images and data.** The Wireshark primer uses no screenshots from the docs, only drawings built from the course's own capture. That capture comes from the Network Analyst Development Framework (CC BY-NC-SA 4.0); credit it if you reuse the example.

The Wireshark scene file is `template/example-wireshark-first-look.html`. Unlike the Power BI example it needs no images, so it renders as is: it's a better starting point for a first try. The Security Onion scene file isn't included because it leans on a screenshot from that project's documentation.

## Requirements
`python3`, `playwright` (Chromium), `ffmpeg`, `pandoc`, `Pillow`; `poppler-utils` for PDFs.
