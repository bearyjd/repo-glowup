#!/usr/bin/env bash
# Rasterize the social-preview SVG to a GitHub-safe PNG (+ JPG fallback).
#
# GitHub's social-preview uploader rejects some valid rsvg PNGs ("Something went
# really wrong and we can't process that picture"). Re-encoding through Pillow
# normalizes the file; the JPG is an even-more-reliable fallback.
#
# Usage: rasterize.sh [ASSETS_DIR]      (default: docs/assets)
set -euo pipefail
DIR="${1:-docs/assets}"
SVG="$DIR/social-preview.svg"
PNG="$DIR/social-preview.png"
JPG="$DIR/social-preview.jpg"

[ -f "$SVG" ] || { echo "rasterize: no $SVG — run gen_branding.py first" >&2; exit 1; }

# 1 - SVG -> PNG (rsvg-convert preferred; headless Chrome as a best-effort fallback)
if command -v rsvg-convert >/dev/null 2>&1; then
    rsvg-convert -w 1280 -h 640 "$SVG" -o "$PNG"
elif command -v google-chrome >/dev/null 2>&1 || command -v chromium >/dev/null 2>&1; then
    CH="$(command -v google-chrome || command -v chromium)"
    "$CH" --headless --no-sandbox --force-device-scale-factor=1 \
          --window-size=1280,640 --hide-scrollbars \
          --screenshot="$PNG" "file://$(readlink -f "$SVG")" >/dev/null 2>&1
else
    echo "rasterize: no rsvg-convert or chrome — cannot make the social PNG." >&2
    echo "  install: dnf install librsvg2-tools | apt install librsvg2-bin | brew install librsvg" >&2
    exit 2
fi

# 2 - Re-encode through Pillow (GitHub-safe baseline PNG + JPG)
if python3 -c "import PIL" >/dev/null 2>&1; then
    python3 - "$PNG" "$JPG" <<'PY'
import sys
from PIL import Image
png, jpg = sys.argv[1], sys.argv[2]
im = Image.open(png).convert("RGB")
im.save(png, format="PNG", optimize=True)
im.save(jpg, format="JPEG", quality=92, subsampling=0, progressive=False)
print(f"rasterize: wrote {png} and {jpg}")
PY
else
    echo "rasterize: Pillow not found — keeping the raw PNG." >&2
    echo "  If GitHub rejects it, run: python3 -m pip install --user pillow  (then re-run)" >&2
    echo "rasterize: wrote $PNG"
fi
