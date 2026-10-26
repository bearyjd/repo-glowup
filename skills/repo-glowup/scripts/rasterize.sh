#!/usr/bin/env bash
# Rasterize the social-preview SVG to a GitHub-safe PNG (+ JPG fallback).
#
# GitHub's social-preview uploader rejects some valid rsvg PNGs ("Something went
# really wrong and we can't process that picture"). Re-encoding through Pillow
# normalizes the file; the JPG is an even-more-reliable fallback.
#
# Usage: rasterize.sh [ASSETS_DIR [PREVIEW_DIR]]      (ASSETS_DIR default: docs/assets)
#   PREVIEW_DIR (optional): also render banner.svg / banner-light.svg (1280x340) to
#   PREVIEW_DIR/banner.png and banner-light.png for review only; never written to ASSETS_DIR.
# Exit: 0 ok, 1 missing social-preview.svg, 2 no rasterizer available.
set -euo pipefail
DIR="${1:-docs/assets}"
PREVIEW="${2:-}"
SVG="$DIR/social-preview.svg"
PNG="$DIR/social-preview.png"
JPG="$DIR/social-preview.jpg"

[ -f "$SVG" ] || { echo "rasterize: no $SVG — run gen_branding.py first" >&2; exit 1; }

# 1 - SVG -> PNG (rsvg-convert preferred; headless Chrome as a best-effort fallback)
MAC_CHROME="/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
CH=""
for c in google-chrome chromium; do
    if command -v "$c" >/dev/null 2>&1; then CH="$(command -v "$c")"; break; fi
done
[ -z "$CH" ] && [ -x "$MAC_CHROME" ] && CH="$MAC_CHROME"

# render SVG PNG WIDTH HEIGHT
render() {
    if command -v rsvg-convert >/dev/null 2>&1; then
        rsvg-convert -w "$3" -h "$4" "$1" -o "$2"
    else
        "$CH" --headless --no-sandbox --force-device-scale-factor=1 \
              --window-size="$3,$4" --hide-scrollbars \
              --screenshot="$2" "file://$(readlink -f "$1")" >/dev/null 2>&1
    fi
}

if ! command -v rsvg-convert >/dev/null 2>&1 && [ -z "$CH" ]; then
    echo "rasterize: no rsvg-convert or chrome — cannot make the social PNG." >&2
    echo "  install: dnf install librsvg2-tools | apt install librsvg2-bin | brew install librsvg" >&2
    exit 2
fi
render "$SVG" "$PNG" 1280 640 || true
if [ ! -s "$PNG" ]; then
    echo "rasterize: WARN render produced no $PNG — cannot make the social PNG." >&2
    echo "  install: dnf install librsvg2-tools | apt install librsvg2-bin | brew install librsvg" >&2
    exit 2
fi

if [ -n "$PREVIEW" ]; then
    mkdir -p "$PREVIEW"
    for b in banner banner-light; do
        if [ -f "$DIR/$b.svg" ]; then
            render "$DIR/$b.svg" "$PREVIEW/$b.png" 1280 340 || true
            if [ -s "$PREVIEW/$b.png" ]; then
                echo "rasterize: wrote $PREVIEW/$b.png (review only)"
            else
                echo "rasterize: WARN render produced no $PREVIEW/$b.png — skipping its preview" >&2
            fi
        else
            echo "rasterize: WARN no $DIR/$b.svg — skipping its preview" >&2
        fi
    done
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
    rm -f "$JPG"   # never leave a stale jpg that the size warning might recommend
    echo "rasterize: Pillow not found — keeping the raw PNG." >&2
    echo "  If GitHub rejects it, run: python3 -m pip install --user pillow  (then re-run)" >&2
    echo "rasterize: wrote $PNG"
fi

# 3 - GitHub caps social-preview uploads at 1 MB; flag an oversized PNG (exit stays 0)
if [ "$(wc -c < "$PNG")" -gt 1000000 ]; then
    if [ -f "$JPG" ]; then
        echo "rasterize: WARN $PNG is over 1,000,000 bytes — upload $JPG instead for GitHub's social preview." >&2
    else
        echo "rasterize: WARN $PNG is over 1,000,000 bytes — GitHub may reject it; install Pillow to get a smaller .jpg." >&2
    fi
fi
