# repo-glowup

A [Claude Code](https://docs.claude.com/en/docs/claude-code) plugin that gives any
repository a polished, intentional GitHub presence — adapted to its stack:

- 🖼️ A branded **README hero banner** (light + dark, theme-aware via `<picture>`)
- 🔖 **Badge chips** — live CI status, license, registry/version, tech stack
- 🃏 A **1280×640 social-preview card** (PNG + JPG, GitHub-upload-safe)
- 🧾 Accurate **About** metadata (description, topics, homepage) via `gh`

The motif is an isometric stack of "layers" in a palette ramp with a bright crown —
generic enough for any project, evocative for layered systems (container images, build
pipelines, package stacks).

## Install (Claude Code)

```
/plugin marketplace add bearyjd/repo-glowup
/plugin install repo-glowup@bearyjd
```

Then, inside any repo:

```
/repo-glowup
```

Local/dev install (before pushing anywhere): `/plugin marketplace add /path/to/repo-glowup`.

## Prerequisites

| Tool | Needed for | Install |
|---|---|---|
| `python3` | the banner generator (stdlib only) | preinstalled on most systems |
| `rsvg-convert` | SVG → PNG (social card) | `dnf install librsvg2-tools` · `apt install librsvg2-bin` · `brew install librsvg` |
| Pillow | GitHub-safe PNG/JPG re-encode | `python3 -m pip install --user pillow` |
| `gh` | About metadata + live status badges | <https://cli.github.com> |
| Cantarell + Fira Code fonts | on-brand rasterized text (falls back gracefully) | your distro's font packages |

The skill checks for these on startup and degrades gracefully when something is missing.

## Use the generator standalone (no Claude)

```bash
python3 skills/repo-glowup/scripts/gen_branding.py \
  --name my-project --palette forest \
  --eyebrow "RUST · CLI" \
  --tagline "A blazing-fast thing that does the thing" \
  --subline "cargo install my-project" \
  --footnote "single binary · zero config · cross-platform" \
  --outdir docs/assets
bash skills/repo-glowup/scripts/rasterize.sh docs/assets
```

Palettes: `ocean`, `ember`, `violet`, `forest`, `slate`, `crimson` — or pass your own
6-color ramp with `--ramp "#111,#222,#333,#444,#555,#666"`. Run with `--help` for all
flags, or pass everything in one `--config branding.json`.

## The one manual step

GitHub has **no API** for the social-preview image. Upload
`docs/assets/social-preview.png` (or `.jpg`) at **Settings → General → Social preview**.

## License

MIT — see [LICENSE](LICENSE).
