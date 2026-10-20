"""Render a scene timeline page to MP4.

The page must define:
  window.TOTAL      -> total duration in seconds
  window.render(t)  -> draws the exact frame for time t (no CSS animations / timers)

Usage:
  python3 render.py scenes.html out.mp4 [--fps 24] [--stills 5,30,62]

Lessons baked in:
  * Deterministic frame capture (render(t) + screenshot) -> no dropped/janky frames.
  * Writes to a temp file, verifies a full decode, THEN moves into place, so nobody
    downloads a half-written file.
  * Encodes for broad compatibility: H.264 Main, yuv420p, constant fps, faststart,
    plus a silent AAC track (some players stop early on video-only MP4s).
"""
import argparse, asyncio, os, pathlib, shutil, subprocess, tempfile
from playwright.async_api import async_playwright

ap = argparse.ArgumentParser()
ap.add_argument("page"); ap.add_argument("out")
ap.add_argument("--fps", type=int, default=24)
ap.add_argument("--width", type=int, default=1280); ap.add_argument("--height", type=int, default=720)
ap.add_argument("--stills", default="", help="comma-separated seconds; save PNG stills instead of rendering")
a = ap.parse_args()
page_url = pathlib.Path(a.page).resolve().as_uri()


async def main():
    async with async_playwright() as p:
        b = await p.chromium.launch()
        pg = await b.new_page(viewport={"width": a.width, "height": a.height})
        await pg.goto(page_url); await pg.wait_for_timeout(800)
        total = await pg.evaluate("TOTAL")

        if a.stills:  # quick contact-sheet check before committing to a full render
            for t in a.stills.split(","):
                await pg.evaluate(f"render({float(t)})")
                await pg.screenshot(path=f"{a.out}_still_{t}.png")
            await b.close(); return

        tmpdir = tempfile.mkdtemp()
        raw = os.path.join(tmpdir, "raw.mp4"); final = os.path.join(tmpdir, "final.mp4")
        n = int(total * a.fps)
        ff = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "image2pipe",
                               "-framerate", str(a.fps), "-c:v", "mjpeg", "-i", "-",
                               "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "18", raw],
                              stdin=subprocess.PIPE)
        for i in range(n):
            await pg.evaluate(f"render({i / a.fps})")
            ff.stdin.write(await pg.screenshot(type="jpeg", quality=92))
            if i % (a.fps * 20) == 0: print(f"{i}/{n} frames", flush=True)
        ff.stdin.close(); ff.wait(); await b.close()

    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", raw, "-f", "lavfi", "-i", "anullsrc=r=48000:cl=stereo",
                    "-map", "0:v", "-map", "1:a", "-c:v", "libx264", "-profile:v", "main", "-level", "4.0",
                    "-pix_fmt", "yuv420p", "-r", str(a.fps), "-crf", "20", "-c:a", "aac", "-b:a", "64k",
                    "-shortest", "-movflags", "+faststart", final], check=True)
    subprocess.run(["ffmpeg", "-v", "error", "-i", final, "-f", "null", "-"], check=True)  # full-decode check
    shutil.move(final, a.out)
    print("wrote", a.out)

asyncio.run(main())
