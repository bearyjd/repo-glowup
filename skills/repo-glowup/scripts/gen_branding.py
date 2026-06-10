#!/usr/bin/env python3
"""Generate on-brand hero/social SVG art for a repository.

Dependency-free (stdlib only). Emits three SVGs into the output directory:
  banner.svg        dark theme hero (README, dark mode)
  banner-light.svg  light theme hero (README, light mode)
  social-preview.svg  2:1 GitHub social card (rasterize -> PNG/JPG separately)

The motif is an isometric stack of "layers" (a tower) in a palette ramp with a
bright crown — generic enough for any project, evocative for layered systems
(container images, build pipelines, package stacks).

Usage:
  gen_branding.py --name NAME [--palette ocean] [--eyebrow ...] [--tagline ...]
                  [--subline ...] [--footnote ...] [--outdir docs/assets]
  gen_branding.py --config branding.json     # same keys as the flags

CLI flags override values from --config.
"""
from __future__ import annotations

import argparse
import json
import os
from typing import NamedTuple

# --- palette presets: 6 base colours bottom->top; the 6th doubles as the crown.
PALETTES: dict[str, list[str]] = {
    "ocean":   ["#143A6B", "#1E50A2", "#1D74C8", "#1D99F3", "#28B8E6", "#76B900"],
    "ember":   ["#4A1709", "#7A2A11", "#A8431B", "#D86A24", "#F0942E", "#FFC44C"],
    "violet":  ["#241A57", "#392A86", "#553CBE", "#7C5CE0", "#A586F2", "#22D3EE"],
    "forest":  ["#0E3B33", "#115E4D", "#178F6B", "#20B886", "#3FD49E", "#A3E635"],
    "slate":   ["#1E2430", "#2A3340", "#3A4658", "#4E5B72", "#6E7C96", "#E2E8F0"],
    "crimson": ["#3A0F1C", "#5E1730", "#8A2347", "#C03060", "#E85C86", "#FBBF24"],
}

FONT = "Cantarell, 'Segoe UI', 'Noto Sans', sans-serif"
MONO = "'Fira Code', 'DejaVu Sans Mono', ui-monospace, monospace"


def _hex(h: str) -> tuple[int, int, int]:
    h = h.lstrip("#")
    return int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)


def _clamp(x: float) -> int:
    return max(0, min(255, int(round(x))))


def _rgb(r: float, g: float, b: float) -> str:
    return f"#{_clamp(r):02X}{_clamp(g):02X}{_clamp(b):02X}"


def lighten(h: str, f: float) -> str:
    r, g, b = _hex(h)
    return _rgb(r + (255 - r) * f, g + (255 - g) * f, b + (255 - b) * f)


def darken(h: str, f: float) -> str:
    r, g, b = _hex(h)
    return _rgb(r * (1 - f), g * (1 - f), b * (1 - f))


def esc(s: str) -> str:
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def fit(size_max: float, avail: float, text: str, factor: float = 0.56) -> float:
    """Shrink a font size so `text` fits within `avail` px (rough advance model)."""
    if not text:
        return size_max
    need = len(text) * factor
    return min(size_max, avail / need) if need else size_max


class Geo(NamedTuple):
    cx: int
    w: int
    h: int
    t: int
    gap: int
    bottom_cy: int


def _slab(cx, cy, w, h, t, base) -> str:
    ct, cl, cr = lighten(base, 0.18), base, darken(base, 0.30)
    top = f"{cx},{cy-h} {cx+w},{cy} {cx},{cy+h} {cx-w},{cy}"
    left = f"{cx-w},{cy} {cx},{cy+h} {cx},{cy+h+t} {cx-w},{cy+t}"
    right = f"{cx+w},{cy} {cx},{cy+h} {cx},{cy+h+t} {cx+w},{cy+t}"
    return (f'    <polygon points="{left}" fill="{cl}"/>\n'
            f'    <polygon points="{right}" fill="{cr}"/>\n'
            f'    <polygon points="{top}" fill="{ct}"/>\n')


def _tower(g: Geo, ramp: list[str]) -> str:
    step = g.t + g.gap
    out = "".join(_slab(g.cx, g.bottom_cy - i * step, g.w, g.h, g.t, base)
                  for i, base in enumerate(ramp))
    cy = g.bottom_cy - (len(ramp) - 1) * step
    rim = lighten(ramp[-1], 0.35)
    out += (f'    <polygon points="{g.cx},{cy-g.h} {g.cx+g.w},{cy} {g.cx},{cy+g.h} '
            f'{g.cx-g.w},{cy}" fill="none" stroke="{rim}" stroke-width="2" opacity="0.9"/>\n')
    return out


def build(kind: str, theme: str, cfg: dict, ramp: list[str]) -> str:
    accent = ramp[3]
    crown = ramp[5]
    name = esc(cfg["name"])
    eyebrow = esc(cfg.get("eyebrow", ""))
    tagline = esc(cfg.get("tagline", ""))
    subline = esc(cfg.get("subline", ""))
    footnote = esc(cfg.get("footnote", ""))

    if theme == "dark":
        bg0, bg1, bg2 = "#0E1426", "#0A0E1C", "#070910"
        c_word, c_tag, c_sub, c_foot = "#F4F7FF", "#AEB9D6", "#6E7A9C", "#52607F"
        c_eye = lighten(accent, 0.40)
        c_div = accent
        dots = lighten(accent, 0.55)
    else:
        bg0, bg1, bg2 = "#FAFCFF", "#EFF3FA", "#E8EEF7"
        c_word, c_tag, c_sub, c_foot = "#10182B", "#44516B", "#7C8AA6", "#94A0B8"
        c_eye = darken(accent, 0.05)
        c_div = accent
        dots = darken(accent, 0.10)

    if kind == "social":
        W, H, rx = 1280, 640, 0
        g = Geo(cx=352, w=165, h=82, t=40, gap=16, bottom_cy=476)
        tx = 588
        avail = 1240 - tx
        ws = fit(84, avail, cfg["name"])
        ts = fit(30, avail, cfg.get("tagline", ""), 0.50)
        body = (
            f'  <text x="{tx}" y="236" font-family="{MONO}" font-size="24" '
            f'letter-spacing="6" fill="{c_eye}">{eyebrow}</text>\n'
            f'  <text x="{tx}" y="322" font-family="{FONT}" font-weight="800" '
            f'font-size="{ws:.0f}" fill="{c_word}">{name}</text>\n'
            f'  <text x="{tx}" y="374" font-family="{FONT}" font-size="{ts:.0f}" '
            f'fill="{c_tag}">{tagline}</text>\n'
            f'  <rect x="{tx}" y="402" width="{avail}" height="2" rx="1" '
            f'fill="{c_div}" opacity="0.40"/>\n'
            f'  <text x="{tx}" y="446" font-family="{MONO}" font-size="25" '
            f'fill="{c_sub}">{subline}</text>\n'
            f'  <text x="{tx}" y="486" font-family="{FONT}" font-size="22" '
            f'fill="{c_foot}">{footnote}</text>\n'
        )
    else:  # banner
        W, H, rx = 1280, 340, 24
        g = Geo(cx=150, w=70, h=35, t=18, gap=8, bottom_cy=250)
        tx = 300
        avail = 1240 - tx
        ws = fit(78, avail, cfg["name"])
        ts = fit(27, avail, cfg.get("tagline", ""), 0.50)
        body = (
            f'  <text x="{tx}" y="128" font-family="{MONO}" font-size="20" '
            f'letter-spacing="5" fill="{c_eye}">{eyebrow}</text>\n'
            f'  <text x="{tx}" y="206" font-family="{FONT}" font-weight="800" '
            f'font-size="{ws:.0f}" fill="{c_word}">{name}</text>\n'
            f'  <text x="{tx}" y="252" font-family="{FONT}" font-size="{ts:.0f}" '
            f'fill="{c_tag}">{tagline}</text>\n'
            f'  <text x="{tx}" y="290" font-family="{MONO}" font-size="22" '
            f'fill="{c_sub}">{subline}</text>\n'
        )

    # background depth: glows (dark) or a grounding shadow (light)
    if theme == "dark":
        depth = (
            f'    <circle cx="{g.cx}" cy="{g.bottom_cy-150}" r="{int(H*0.9)}" '
            f'fill="url(#glowA)"/>\n'
            f'    <circle cx="{g.cx}" cy="{g.bottom_cy-(len(ramp)-1)*(g.t+g.gap)-g.h}" '
            f'r="{int(H*0.45)}" fill="url(#glowB)"/>\n'
        )
    else:
        depth = (f'    <ellipse cx="{g.cx}" cy="{g.bottom_cy+g.h+10}" '
                 f'rx="{int(g.w*1.6)}" ry="{max(12,int(g.h*0.45))}" '
                 f'fill="#1D3A6B" opacity="0.12"/>\n')

    glow_defs = (
        f'    <radialGradient id="glowA" cx="0.5" cy="0.5" r="0.5">'
        f'<stop offset="0" stop-color="{accent}" stop-opacity="0.42"/>'
        f'<stop offset="1" stop-color="{accent}" stop-opacity="0"/></radialGradient>\n'
        f'    <radialGradient id="glowB" cx="0.5" cy="0.5" r="0.5">'
        f'<stop offset="0" stop-color="{crown}" stop-opacity="0.5"/>'
        f'<stop offset="1" stop-color="{crown}" stop-opacity="0"/></radialGradient>\n'
        if theme == "dark" else ""
    )
    clip = (f'  <clipPath id="r"><rect width="{W}" height="{H}" rx="{rx}"/></clipPath>\n'
            if rx else "")
    g_open = '<g clip-path="url(#r)">' if rx else "<g>"
    label = esc(f'{cfg["name"]} — {cfg.get("tagline", "")}'.rstrip(" —"))

    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" '
        f'width="{W}" height="{H}" role="img" aria-label="{label}">\n'
        f'  <defs>\n'
        f'    <linearGradient id="bg" x1="0" y1="0" x2="0.3" y2="1">'
        f'<stop offset="0" stop-color="{bg0}"/>'
        f'<stop offset="0.55" stop-color="{bg1}"/>'
        f'<stop offset="1" stop-color="{bg2}"/></linearGradient>\n'
        f'{glow_defs}'
        f'    <pattern id="dots" width="34" height="34" patternUnits="userSpaceOnUse">'
        f'<circle cx="2" cy="2" r="1.4" fill="{dots}" opacity="0.05"/></pattern>\n'
        f'  </defs>\n'
        f'{clip}  {g_open}\n'
        f'    <rect width="{W}" height="{H}" fill="url(#bg)"/>\n'
        f'    <rect width="{W}" height="{H}" fill="url(#dots)"/>\n'
        f'{depth}'
        f'{_tower(g, ramp)}'
        f'{body}'
        f'  </g>\n'
        f'</svg>\n'
    )


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--config", help="JSON file with any of the keys below")
    p.add_argument("--name")
    p.add_argument("--eyebrow", default=None)
    p.add_argument("--tagline", default=None)
    p.add_argument("--subline", default=None)
    p.add_argument("--footnote", default=None)
    p.add_argument("--palette", default=None,
                   help=f"one of: {', '.join(PALETTES)} (or pass 6 hex via --ramp)")
    p.add_argument("--ramp", default=None,
                   help="comma-separated 6 hex colours bottom->top (overrides --palette)")
    p.add_argument("--outdir", default=None)
    args = p.parse_args()

    cfg: dict = {"palette": "ocean", "outdir": "docs/assets"}
    if args.config:
        with open(args.config, encoding="utf-8") as f:
            cfg.update(json.load(f))
    for k in ("name", "eyebrow", "tagline", "subline", "footnote", "palette", "outdir", "ramp"):
        v = getattr(args, k)
        if v is not None:
            cfg[k] = v

    if not cfg.get("name"):
        p.error("a repo name is required (--name or \"name\" in --config)")

    if cfg.get("ramp"):
        ramp = [c.strip() for c in cfg["ramp"].split(",")]
        if len(ramp) != 6:
            p.error("--ramp needs exactly 6 comma-separated hex colours")
    else:
        ramp = PALETTES.get(cfg["palette"])
        if not ramp:
            p.error(f"unknown palette {cfg['palette']!r}; choices: {', '.join(PALETTES)}")

    outdir = cfg["outdir"]
    os.makedirs(outdir, exist_ok=True)
    outputs = {
        "banner.svg": build("banner", "dark", cfg, ramp),
        "banner-light.svg": build("banner", "light", cfg, ramp),
        "social-preview.svg": build("social", "dark", cfg, ramp),
    }
    for fname, svg in outputs.items():
        path = os.path.join(outdir, fname)
        with open(path, "w", encoding="utf-8") as f:
            f.write(svg)
        print(f"wrote {path}")


if __name__ == "__main__":
    main()
