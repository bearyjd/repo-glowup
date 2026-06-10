---
name: repo-glowup
description: >
  Use when the user wants to improve a repository's GitHub presence — "make the repo
  look cooler", add a README banner or badges, set up a social-preview card, or fix the
  repo description/topics. Triggers on "repo glow-up", "readme banner", "badges",
  "social preview", "repo branding".
argument-hint: "[--no-about] [--no-docs]"
allowed-tools:
  - Bash
  - Read
  - Edit
  - Write
  - AskUserQuestion
---

# Repo Glow-Up

Give the **current repository** a polished, intentional GitHub presence, adapted to its
stack: (1) a branded hero banner (light + dark), (2) status/tech badge chips, (3) a
1280×640 social-preview card, (4) accurate About metadata (description, topics, homepage).

Bundled tooling: `${CLAUDE_PLUGIN_ROOT}/skills/repo-glowup/scripts/` and
`${CLAUDE_PLUGIN_ROOT}/skills/repo-glowup/references/badges.md`.

Flags in `$ARGUMENTS`: `--no-about` skips the `gh` metadata step; `--no-docs` skips the
optional codemaps/CONTRIBUTING/RUNBOOK offer.

## 0 · Preflight (check deps, fail soft)

Confirm a git repo (`git rev-parse --is-inside-work-tree`), then probe and print a short
table; continue with whatever is available:

- `python3` — **required** (the banner generator; stdlib only).
- `rsvg-convert` **or** `google-chrome`/`chromium` — to rasterize the social PNG. If
  neither, generate the SVGs but skip the PNG and say so.
- `python3 -c "import PIL"` (Pillow) — to emit a **GitHub-safe** PNG/JPG. GitHub's
  social uploader rejects some raw rsvg PNGs ("can't process that picture"); the Pillow
  re-encode fixes it. If missing, warn and continue with the raw PNG.
- `gh auth status` — needed for About + live status badges. If missing, skip About and
  use a plain (non-status) build badge.
- Fonts: `fc-list | grep -i cantarell` and Fira Code. If absent the SVG still renders;
  only the rasterized PNG falls back to other fonts. Note it.

## 1 · Detect the project (read, don't guess)

- Current metadata: `gh repo view --json name,description,repositoryTopics,homepageUrl,licenseInfo`.
- Stack signals: `package.json` (node), `pyproject.toml`/`setup.*` (python),
  `Cargo.toml` (rust), `go.mod` (go), `composer.json` (php), `Gemfile` (ruby),
  `Containerfile`/`Dockerfile` or `kargs.d`/bootc (container/OS image), else generic.
- License → SPDX; `.github/workflows/*.yml` → the main build/test workflow filename(s)
  for status badges; the README's first paragraph for tagline material.

Derive a metadata draft:

| field | how |
|---|---|
| name | repo name |
| ecosystem | node / python / rust / go / php / ruby / container / generic |
| palette | node→`forest`, python→`ocean`, rust→`crimson`, go→`ocean`, container/bootc→`ocean`, php→`violet`, ruby→`ember`, generic→`slate` (or by vibe) |
| eyebrow | short uppercase mono, e.g. `TYPESCRIPT · EDGE RUNTIME` |
| tagline | one sentence (≤ ~60 chars) — condense the repo description |
| subline | install/run line: `npm i X` / `pipx install X` / `cargo add X` / `go install …` / `docker pull ghcr.io/<owner>/<name>` |
| footnote | 3 short value props (social card only) |
| description | ≤ 350 chars, accurate |
| topics | 8–15 lowercase-hyphen tags |

## 2 · Confirm with the user

Show the drafted metadata (name / eyebrow / tagline / subline / palette / description /
topics) and let them edit before applying — wording and palette are subjective. If the
palette is unclear, offer the six presets via AskUserQuestion.

## 3 · Generate the art

Write a temp `branding.json` with the confirmed fields, then:

```bash
python3 "${CLAUDE_PLUGIN_ROOT}/skills/repo-glowup/scripts/gen_branding.py" \
  --config branding.json --outdir docs/assets
bash "${CLAUDE_PLUGIN_ROOT}/skills/repo-glowup/scripts/rasterize.sh" docs/assets
```

Then **Read `docs/assets/social-preview.png`** and verify visually (no text overflow,
correct wording). Regenerate if anything is off.

## 4 · Wire the README hero (idempotent)

Insert a managed block at the very top, preserving the rest of the README. If the markers
already exist, replace only what's between them:

```
<!-- glowup:hero start -->
<div align="center">
<h1>
  <picture>
    <source media="(prefers-color-scheme: dark)" srcset="docs/assets/banner.svg">
    <img src="docs/assets/banner-light.svg" alt="NAME" width="880">
  </picture>
</h1>

BADGES
</div>
<!-- glowup:hero end -->
```

Pick badges from `${CLAUDE_PLUGIN_ROOT}/skills/repo-glowup/references/badges.md`: a CI
**status** badge (from the detected workflow), license, registry/version, and 4–6
ecosystem tech chips — all `style=for-the-badge`. Verify a couple resolve to
`image/svg+xml` (curl `-sI`) before finishing.

## 5 · GitHub About  (skip if `--no-about` or no `gh`)

```bash
gh repo edit --description "…" --homepage "<package/registry or docs URL>" \
  --add-topic tag1,tag2,tag3,…
```

## 6 · Docs  (optional; skip if `--no-docs`)

Offer to run `/update-codemaps` and `/update-docs` for codemaps + CONTRIBUTING/RUNBOOK.

## 7 · Social card upload  (manual — there is no API)

Tell the user to upload `docs/assets/social-preview.png` (or `.jpg`) at
**Settings → General → Social preview**. Print the absolute path.

## 8 · Verify & report

- A couple of badge SVG URLs return `200 image/svg+xml`.
- README image paths exist; `gh repo view` reflects the new About.
- Summarize what changed and restate the single manual step (the upload).
