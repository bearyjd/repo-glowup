---
name: repo-glowup
description: >
  Use when the user wants to improve a repository's GitHub presence — "make the repo
  look cooler", add a README banner or badges, set up a social-preview card, or fix the
  repo description/topics. Triggers on "repo glow-up", "readme banner", "badges",
  "social preview", "repo branding".
argument-hint: "[--no-about] [--docs] [--dry-run]"
allowed-tools:
  - Bash
  - Read
  - Edit
  - Write
  - AskUserQuestion
  - Skill
---

# Repo Glow-Up

Give the **current repository** a polished, intentional GitHub presence, adapted to its
stack: (1) a branded hero banner (light + dark), (2) status/tech badge chips, (3) a
1280×640 social-preview card, (4) accurate About metadata (description, topics, homepage).

Bundled tooling: `${CLAUDE_PLUGIN_ROOT}/skills/repo-glowup/scripts/`,
`${CLAUDE_PLUGIN_ROOT}/skills/repo-glowup/references/badges.md`,
`${CLAUDE_PLUGIN_ROOT}/skills/repo-glowup/references/ecosystems.json`.

Flags in `$ARGUMENTS`: `--no-about` skips step 5; `--docs` opts in to step 6; `--dry-run`
generates into temp dirs, prints the drafted metadata, README diff and planned `gh`
commands, and **changes nothing in the repo**. Nothing is ever committed.

## 0 · Preflight (check deps, fail soft)

Confirm a git repo (`git rev-parse --is-inside-work-tree`), then probe and print a short
table; continue with whatever is available:

- `python3` — **required** (banner generator; stdlib only).
- `rsvg-convert` **or** `google-chrome`/`chromium` — rasterizing. `rasterize.sh` exit
  code 2 means none found: a **soft failure** (keep SVGs, skip PNG, say so).
- `python3 -c "import PIL"` (Pillow) — GitHub-safe PNG/JPG re-encode (raw rsvg PNGs are
  sometimes rejected by the social uploader). If missing, warn and use the raw PNG.
- `gh auth status` — needed for About, visibility and default branch. If missing, skip
  About and use a plain (non-status) build badge.

## 1 · Detect the project (read, don't guess)

- Metadata: `gh repo view --json name,description,repositoryTopics,homepageUrl,licenseInfo,isPrivate,defaultBranchRef`.
- Default branch: `defaultBranchRef.name`, else `git symbolic-ref --short refs/remotes/origin/HEAD`
  (strip `origin/`), else `main`. Use it in the status badge.
- Visibility: for private repos **skip every shields.io `github/*` badge** (they don't
  render) and tell the user why; use static `badge/…` chips and registry badges only. If
  visibility can't be determined (no `gh`), ask via AskUserQuestion, defaulting to
  static/registry-only badges.
- Ecosystem: match root files against `references/ecosystems.json`
  (`{ecosystem: {markers, alt_markers, palette}}`). If **more than one** ecosystem
  matches (polyglot/monorepo), list them and let the user pick in step 2; do not take
  the first match. None matches → `generic`. The file gives each ecosystem's palette.
- License → SPDX; `.github/workflows/*.yml` → main build/test workflow for the status
  badge; README's first paragraph for tagline material.

Draft metadata:

| field | how |
|---|---|
| name | repo name |
| ecosystem / palette | from `ecosystems.json` (or by vibe) |
| eyebrow | short uppercase mono, e.g. `TYPESCRIPT · EDGE RUNTIME` |
| tagline | one sentence (≤ ~60 chars) — condense the repo description |
| subline | install/run line: `npm i X` / `pipx install X` / `cargo add X` / `go install …` / `docker pull ghcr.io/<owner>/<name>` |
| footnote | 3 short value props (social card only) |
| description | ≤ 350 chars, accurate |
| topics | 8–15 lowercase-hyphen tags |

## 2 · Confirm with the user

Show the draft (name / eyebrow / tagline / subline / palette / description / topics) and
let them edit — wording and palette are subjective; offer the six presets via
AskUserQuestion if unclear. Also settle here:

- **Ecosystem** if step 1 found several.
- **Topics diff**: existing topics vs proposed, as old→new with additions and removals
  listed separately. Removals happen only for topics the user approves.
- **Homepage**: if one already exists, keep it unless the user confirms a change.
- **Asset dir** (`ASSETS`): default `docs/assets`. If `docs/` is a site (has an index or
  config file) or already holds unrelated files, ask for another dir (suggest
  `.github/assets`). Use `ASSETS` consistently in steps 3, 4 and 7.

## 3 · Generate the art

Write `branding.json` into a `mktemp -d` dir (never the user's repo). Overwrite only
glowup-owned files: `banner.svg`, `banner-light.svg`, `social-preview.*`.

```bash
CFG=$(mktemp -d); PREVIEW=$(mktemp -d)   # write $CFG/branding.json first
OUT=<ASSETS dir from step 2>             # with --dry-run: OUT=$(mktemp -d) instead
python3 "${CLAUDE_PLUGIN_ROOT}/skills/repo-glowup/scripts/gen_branding.py" \
  --config "$CFG/branding.json" --outdir "$OUT"
bash "${CLAUDE_PLUGIN_ROOT}/skills/repo-glowup/scripts/rasterize.sh" "$OUT" "$PREVIEW"
echo "CFG=$CFG PREVIEW=$PREVIEW OUT=$OUT"   # shell state doesn't persist — keep these paths
```

Then **Read** `$OUT/social-preview.png` plus `$PREVIEW/banner.png` and
`$PREVIEW/banner-light.png` (use the literal paths echoed above); verify visually (no
overflow, correct wording) and regenerate if off. Finally clean up:
`rm -rf "$CFG" "$PREVIEW"` (plus the dry-run `$OUT`).

- Exit 1 from `rasterize.sh`: generation failed (no `social-preview.svg`). Stop and report.
- Exit 2 from `rasterize.sh`: no rasterizer, or Chrome rendered nothing. Keep the SVGs,
  skip PNG checks, and tell the user the social-card upload is unavailable until
  `rsvg-convert` or a working Chrome is installed.
- If it prints a WARN that the PNG exceeds 1 MB, point the user to the `.jpg` in step 7.

## 4 · Wire the README hero (idempotent)

Find the README: `README.md`, `.github/README.md` or `docs/README.md`.

- Not markdown (`.rst`, `.adoc`, other): offer a hero in that format's equivalent image
  syntax, or skip this step with a message.
- No README: offer to create a minimal one; create it only if the user agrees.
- Existing top-of-file `<h1>` or banner image **without** glowup markers: show it and ask
  replace or keep. Never silently duplicate.
- Insert the managed block at the very top, preserving the rest. If the markers exist,
  replace only what's between them:

```
<!-- glowup:hero start -->
<div align="center">
<h1>
  <picture>
    <source media="(prefers-color-scheme: dark)" srcset="ASSETS/banner.svg">
    <img src="ASSETS/banner-light.svg" alt="NAME" width="880">
  </picture>
</h1>

BADGES
</div>
<!-- glowup:hero end -->
```

(Relative to the README's own directory if it isn't the repo root.) Pick badges from
`references/badges.md` (all `style=for-the-badge`): CI **status** (detected workflow, on
the detected default branch), license, registry/version, and 4–6 tech chips for the
chosen ecosystem. Tech chips come from `badges.md` rows matching stack signals actually
seen in the repo, not only the `ecosystems.json` match. Verify a couple resolve to
`image/svg+xml` (`curl -sI`). Before finishing, show the README diff (`git diff --stat`
and `git diff -- <README>`). With `--dry-run`, show the diff against a temp copy instead
of editing.

## 5 · GitHub About  (skip if `--no-about` or no `gh`; with `--dry-run` print only)

Merge, don't clobber. Apply only approved changes:

```bash
gh repo edit --description "…" --add-topic a,b --remove-topic old1,old2 \
  [--homepage "<url>"]   # homepage only if empty or the user confirmed
```

Omit `--remove-topic` unless the user approved removals. If there is no remote, or `gh`
errors (no push/admin permission), print the exact `gh repo edit …` command for the user
to run and continue.

## 6 · Docs  (only with `--docs`)

Offer `/update-codemaps` and `/update-docs` via the Skill tool; if not installed, say so and skip.

## 7 · Social card upload  (manual — there is no API)

Tell the user to upload `ASSETS/social-preview.png` (or `.jpg`) at
**Settings → General → Social preview**; print the absolute path. Unavailable if step 3
had no rasterizer.

## 8 · Verify & report

- Badge URLs return `200 image/svg+xml`; README image paths exist; `gh repo view` shows
  the new About (unless skipped or dry-run).
- **Nothing was committed**: show `git status --short`. For private repos, restate that
  `github/*` badges were omitted. Restate the one manual step (the upload).
