#!/usr/bin/env bash
# Pull text + images out of a source document into ./extracted/
# Usage: ./extract.sh <file.docx|file.pptx|file.pdf>
set -euo pipefail
src="$1"; out="extracted"; mkdir -p "$out/media"
case "${src,,}" in
  *.docx)
    unzip -oq "$src" -d "$out/zip"
    cp "$out"/zip/word/media/* "$out/media/" 2>/dev/null || true
    pandoc "$src" -t markdown --extract-media="$out" -o "$out/text.md" ;;   # keeps image order + sizes in context
  *.pptx)
    unzip -oq "$src" -d "$out/zip"
    cp "$out"/zip/ppt/media/* "$out/media/" 2>/dev/null || true
    # slide text lives in ppt/slides/slideN.xml; speaker notes (great captions) in ppt/notesSlides/
    for f in $(ls "$out"/zip/ppt/slides/slide*.xml | sort -V); do
      echo "## $(basename "$f" .xml)"; sed -e 's/<\/a:p>/\n/g' -e 's/<[^>]*>//g' "$f"; echo
    done > "$out/text.md" ;;
  *.pdf)
    pdftotext -layout "$src" "$out/text.md"
    pdfimages -png "$src" "$out/media/img" ;;
  *) echo "Unsupported: $src (for web pages, save HTML + images; for notes, skip this step)"; exit 1 ;;
esac
python3 - "$out/media" <<'EOF'
import sys, glob
from PIL import Image
for f in sorted(glob.glob(sys.argv[1] + "/*")):
    try: print(f, Image.open(f).size)
    except Exception: pass
EOF
