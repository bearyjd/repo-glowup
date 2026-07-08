#!/usr/bin/env bash
# End-to-end self-check: generate + (if possible) rasterize every palette, then
# validate every artifact actually parses/opens. Prints PASS/FAIL per palette
# and exits nonzero on any failure.
#
# Usage: bash skills/repo-glowup/scripts/selfcheck.sh
set -uo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
GEN="$SCRIPT_DIR/gen_branding.py"
RASTERIZE="$SCRIPT_DIR/rasterize.sh"

PALETTES=(ocean ember violet forest slate crimson)

CAN_RASTERIZE=0
if command -v rsvg-convert >/dev/null 2>&1 || command -v google-chrome >/dev/null 2>&1 || command -v chromium >/dev/null 2>&1; then
    CAN_RASTERIZE=1
fi

HAS_PIL=0
if python3 -c "import PIL" >/dev/null 2>&1; then
    HAS_PIL=1
fi

if [ "$CAN_RASTERIZE" -eq 0 ]; then
    echo "selfcheck: no rsvg-convert/chrome found — will validate SVGs only, skip rasterization" >&2
fi
if [ "$HAS_PIL" -eq 0 ]; then
    echo "selfcheck: Pillow not found — will skip PNG dimension checks" >&2
fi

OVERALL_STATUS=0
WORKDIR="$(mktemp -d)"
trap 'rm -rf "$WORKDIR"' EXIT

validate_svg() {
    local svg="$1"
    python3 -c "import sys, xml.etree.ElementTree as ET; ET.parse(sys.argv[1])" "$svg"
}

validate_social_png() {
    local png="$1"
    python3 -c "
import sys
from PIL import Image
im = Image.open(sys.argv[1])
size = im.size
assert size == (1280, 640), f'expected (1280, 640), got {size}'
" "$png"
}

for palette in "${PALETTES[@]}"; do
    outdir="$WORKDIR/$palette"
    mkdir -p "$outdir"
    status="PASS"
    detail=""

    if ! gen_out="$(python3 "$GEN" --name "selfcheck-$palette" --palette "$palette" \
            --eyebrow "SELFCHECK" --tagline "self-check tagline" \
            --subline "npm i selfcheck" --footnote "a . b . c" \
            --outdir "$outdir" 2>&1)"; then
        status="FAIL"
        detail="gen_branding.py failed: $gen_out"
    fi

    if [ "$status" = "PASS" ]; then
        for svg in "$outdir"/*.svg; do
            if ! validate_svg "$svg" >/dev/null 2>&1; then
                status="FAIL"
                detail="invalid SVG: $svg"
                break
            fi
        done
    fi

    if [ "$status" = "PASS" ] && [ "$CAN_RASTERIZE" -eq 1 ]; then
        if ! raster_out="$(bash "$RASTERIZE" "$outdir" 2>&1)"; then
            status="FAIL"
            detail="rasterize.sh failed: $raster_out"
        fi
    fi

    if [ "$status" = "PASS" ] && [ "$CAN_RASTERIZE" -eq 1 ] && [ "$HAS_PIL" -eq 1 ]; then
        png="$outdir/social-preview.png"
        if [ ! -f "$png" ]; then
            status="FAIL"
            detail="missing $png after rasterize"
        elif ! validate_social_png "$png" >/dev/null 2>&1; then
            status="FAIL"
            detail="social-preview.png is not 1280x640"
        fi
    fi

    if [ "$status" = "PASS" ]; then
        echo "PASS  $palette"
    else
        echo "FAIL  $palette  -- $detail"
        OVERALL_STATUS=1
    fi
done

exit "$OVERALL_STATUS"
