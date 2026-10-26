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

# Non-blank (>1 distinct colour) and under GitHub's 1,000,000-byte-friendly size.
validate_social_content() {
    local png="$1"
    python3 -c "
import os, sys
from PIL import Image
im = Image.open(sys.argv[1]).convert('RGB')
assert len(im.getcolors(maxcolors=1 << 24)) > 1, 'social PNG is blank'
assert os.path.getsize(sys.argv[1]) < 1000000, 'social PNG >= 1,000,000 bytes'
" "$png"
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

# run_case LABEL GEN_ARGS... : generate, validate SVGs, rasterize (+preview), check PNGs.
run_case() {
    local label="$1"; shift
    local outdir="$WORKDIR/$label"
    local preview="$WORKDIR/$label-preview"
    mkdir -p "$outdir"
    local status="PASS"
    local detail=""

    if ! gen_out="$(python3 "$GEN" "$@" --outdir "$outdir" 2>&1)"; then
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
        if ! raster_out="$(bash "$RASTERIZE" "$outdir" "$preview" 2>&1)"; then
            status="FAIL"
            detail="rasterize.sh failed: $raster_out"
        elif [ ! -f "$preview/banner.png" ] || [ ! -f "$preview/banner-light.png" ]; then
            status="FAIL"
            detail="missing preview banner PNGs in $preview"
        elif [ -e "$outdir/banner.png" ] || [ -e "$outdir/banner-light.png" ]; then
            status="FAIL"
            detail="preview PNGs leaked into assets dir"
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
        elif ! content_out="$(validate_social_content "$png" 2>&1)"; then
            status="FAIL"
            detail="social-preview.png content check: ${content_out##*$'\n'}"
        fi
    fi

    if [ "$status" = "PASS" ]; then
        echo "PASS  $label"
    else
        echo "FAIL  $label  -- $detail"
        OVERALL_STATUS=1
    fi
}

for palette in "${PALETTES[@]}"; do
    run_case "$palette" --name "selfcheck-$palette" --palette "$palette" \
        --eyebrow "SELFCHECK" --tagline "self-check tagline" \
        --subline "npm i selfcheck" --footnote "a . b . c"
done

LONG="$(printf 'x%.0s' $(seq 1 300))"
run_case hostile --name "Q\"uo'te & <b> café 🚀 $LONG" \
    --eyebrow "E\"&<>$LONG" --tagline 'The "fast" thing & more' \
    --subline "$LONG \"q\" & <x>" --footnote "$LONG 'z' & 日本"
run_case short-hex-ramp --name ramp-check --ramp "#111,#222,#333,#444,#555,#666"

CFG="$WORKDIR/branding.json"
printf '%s' '{"name": 42, "tagline": "from \"config\"", "subline": 7, "palette": "violet", "ramp": ["#111", "#222", "#333", "#444", "#555", "#666"]}' > "$CFG"
run_case config --config "$CFG"

exit "$OVERALL_STATUS"
