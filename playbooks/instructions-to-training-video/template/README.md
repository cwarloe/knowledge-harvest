`example-external-data.html` is the full 16-scene example. It references `assets/*.png` (screenshots from the
course instructions), which are intentionally **not** committed. Drop your own extracted images into `assets/`.
Edit the `SC` array: each entry is `[sectionId, durationSeconds, lt => { /* draw at local time lt */ }]`.

`example-wireshark-first-look.html` is the 11-scene, 2:14 Wireshark primer. It is self-contained (no `assets/` needed), and its data block holds real `tshark` output from a lab capture. It includes a small `winHTML()` helper that draws a Wireshark-style window (filter bar, packet list, details tree, hex pane), a typed-filter effect with red/green validity, and a right-click menu. Render it with `python3 ../scripts/render.py example-wireshark-first-look.html out.mp4`.
