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
- `rsvg-convert` **or** `google-chrome`/`chromium` — rasterizing (none: soft failure, see step 3).
- `python3 -c "import PIL"` (Pillow) — GitHub-safe PNG/JPG re-encode. If missing, warn
  and use the raw PNG (the social uploader sometimes rejects it).
- `gh auth status` — needed for About, visibility and default branch. If missing, skip
  About and use a plain (non-status) build badge.

## 1 · Detect the project (read, don't guess)

- Metadata: `gh repo view --json name,description,repositoryTopics,homepageUrl,licenseInfo,isPrivate,defaultBranchRef`.
- Default branch: `defaultBranchRef.name`, else `git symbolic-ref --short refs/remotes/origin/HEAD`
  (strip `origin/`), else `git config init.defaultBranch`, else `git branch --show-current`
  if it is the repo's only branch, else `main`. Use it in the status badge.
- Visibility: for private repos **skip every shields.io `github/*` badge** (they don't
  render) and tell the user why; use static `badge/…` chips and registry badges only. If
  visibility can't be determined (no `gh`, or `gh repo view` fails because there is no
  remote), ask via AskUserQuestion, defaulting to static/registry-only badges.
- Names: repo name = directory name; package name from `package.json` `name` / pyproject
  `[project].name` / Cargo `[package].name` / go.mod `module` / `composer.json` `name` /
  `*.gemspec`; owner from the remote, else omit owner-dependent badges.
- Ecosystem: match root files against `references/ecosystems.json` (it also gives each
  palette). If **more than one** matches (polyglot/monorepo), list them and let the user
  pick in step 2; never take the first. `generic` is the no-match fallback only, not a
  second match.
- License → SPDX; `.github/workflows/*.yml` → main build/test workflow for the status
  badge; README's first paragraph for tagline material.

Draft metadata:

| field | how |
|---|---|
| name | repo name |
| ecosystem / palette | from `ecosystems.json` (or by vibe) |
| eyebrow | short uppercase mono, e.g. `TYPESCRIPT · EDGE RUNTIME` |
| tagline | one sentence, ≤ ~40 chars (the social card is narrower than the banner) — condense the repo description |
| subline | install/run line, ≤ ~50 chars (more shows an ellipsis on the card): `npm i X` / `pipx install X` / `cargo add X` / `go install …` / `docker pull ghcr.io/<owner>/<name>` / `bootc switch ghcr.io/<owner>/<name>:latest` (container/bootc OS images) |
| footnote | 3 short value props (social card only) |
| description | ≤ 350 chars, accurate |
| topics | lowercase-hyphen tags; 8–15 only when proposing for a repo with none/few |

## 2 · Confirm with the user

Show the draft and let them edit — wording and palette are subjective; offer the six
presets via AskUserQuestion if unclear. Also settle here:

- **Ecosystem** if step 1 found several.
- **Topics**: KEEP existing ones and propose additions only; remove one only if the user
  asks. **Homepage**: keep an existing one unless the user confirms a change.
- **Asset dir** (`ASSETS`): default `docs/assets`; reuse it without asking if it already
  holds glowup-owned files the README references. If `docs/` is a site (has an index or
  config file) or holds unrelated files (ignore dot-dirs like `.omc`), ask for another
  (suggest `.github/assets`). Use `ASSETS` in steps 3, 4 and 7.
- **Emphasis**: the repo can't say where it is heading. Ask what the card should
  emphasize beyond what the repo states (a new direction, a flagship component). Work it
  into the eyebrow, tagline or footnote, only as far as the user says is true now ("built
  around X", not "ships X by default", if X is opt-in or in progress).
- **Existing chips**: when replacing a glowup block, list its current chips and carry
  over any the user doesn't drop.

## 3 · Generate the art

Shell state doesn't persist between Bash calls, so create the temp dirs first and reuse
the **literal printed paths** below (never inside the user's repo):

```bash
CFG=$(mktemp -d); PREVIEW=$(mktemp -d); DRYOUT=$(mktemp -d); echo "$CFG $PREVIEW $DRYOUT"
```

Write `<CFG>/branding.json` with keys `name`, `palette`, `eyebrow`, `tagline`, `subline`,
`footnote`, `ramp`, `outdir` (CLI flags override). Overwrite only glowup-owned files:
`banner.svg`, `banner-light.svg`, `social-preview.*`. Then run, substituting paths
(`OUT` = the step 2 `ASSETS` dir, or `<DRYOUT>` with `--dry-run`):

```bash
python3 "${CLAUDE_PLUGIN_ROOT}/skills/repo-glowup/scripts/gen_branding.py" \
  --config <CFG>/branding.json --outdir <OUT>
bash "${CLAUDE_PLUGIN_ROOT}/skills/repo-glowup/scripts/rasterize.sh" <OUT> <PREVIEW>
```

Then **Read** `<OUT>/social-preview.png` plus `<PREVIEW>/banner.png` and
`<PREVIEW>/banner-light.png`; verify visually (no overflow, correct wording) and
regenerate if off, reusing the same temp dirs. An ellipsis (…) on the card counts as off:
shorten the text and regenerate rather than accept truncation. Finally clean up:
`rm -r -- <CFG> <PREVIEW> <DRYOUT>` (the mktemp paths only).

- `rasterize.sh` exit 1: generation failed (no `social-preview.svg`); stop and report.
  Exit 2: no rasterizer, or Chrome rendered nothing, a **soft failure**: keep the SVGs,
  skip PNG checks, say the upload is unavailable until one is installed.
- A WARN that the PNG exceeds 1 MB: point the user to the `.jpg` in step 7.

## 4 · Wire the README hero (idempotent)

Find the README: `README.md`, `.github/README.md` or `docs/README.md`.

- Not markdown (`.rst`, `.adoc`, other): offer a hero in that format's equivalent image
  syntax, or skip this step with a message.
- No README: offer to create a minimal one; create it only if the user agrees.
- Existing top-of-file `<h1>` or banner image **without** glowup markers: show it and ask
  replace or keep. Never silently duplicate. When replacing, remove only that banner
  element (e.g. the `<h1>…<img…></h1>` or image line) plus its trailing blank lines.
- A plain markdown `# Title` H1 (no image) equal to the repo name: ask whether to drop it
  (the hero's `<h1>` is the title); default drop.
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

(Image paths are relative to the README's own directory if it isn't the repo root.)

- BADGES: markdown syntax, one per line, from `references/badges.md` (all
  `style=for-the-badge`): CI **status** (detected workflow, on the detected default
  branch; omit if no workflow), license, registry/version, and 4–6 tech chips whose
  `badges.md` rows match stack signals seen in the repo.
- Verify a couple resolve to `image/svg+xml` (`curl -sI`; on empty/non-200 retry once
  before reporting failure).
- Show the README diff (`git diff -- <README>`); with `--dry-run`, diff against a temp
  copy instead of editing. An empty diff means the README is already up to date: say so.

## 5 · GitHub About  (skip if `--no-about` or no `gh`; with `--dry-run` print only)

Merge, don't clobber. Apply only approved changes:

```bash
gh repo edit [--description "…"] [--add-topic a,b] [--remove-topic old1,old2] \
  [--homepage "<url>"]   # homepage only if empty or the user confirmed
```

Omit any flag with no change; if nothing changed, skip `gh repo edit` entirely. If there
is no remote, or `gh` errors (no push/admin permission), print the exact command for the
user to run and continue.

## 6 · Docs  (only with `--docs`)

Offer `/update-codemaps` and `/update-docs` via the Skill tool; if not installed, say so and skip.

## 7 · Social card upload  (manual — there is no API)

Tell the user to upload `ASSETS/social-preview.png` (or `.jpg`) at
**Settings → General → Social preview**; print the absolute path. Skip with `--dry-run`
(nothing was written to `ASSETS`) or when there was no rasterizer.

## 8 · Verify & report

- Badge URLs return `200 image/svg+xml`; the hero's image paths exist:
  `grep -oE '(src|srcset)="[^"]+"' "<README>" | cut -d'"' -f2 | grep -v '^http' | while read -r p; do test -f "$(dirname "<README>")/$p" || echo "missing: $p"; done`
  (hero `<img>`/`<source>` only; with `--dry-run` run it on the temp README copy);
  `gh repo view` shows the new About (unless skipped or dry-run).
- **Nothing was committed**: show `git status --short`. For private repos, restate that
  `github/*` badges were omitted. Restate the one manual step (the upload).
