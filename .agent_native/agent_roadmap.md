# Agent-Native Roadmap — repo-glowup

Audit date: 2026-07-07. This repo is a Claude Code plugin (one skill: `repo-glowup`)
that generates README banners, badge chips, a social-preview card, and GitHub About
metadata. Stack: Python 3 stdlib-only generator (`gen_branding.py`), a bash rasterizer
(`rasterize.sh`, shells out to `rsvg-convert`/`chrome` + Pillow), a markdown workflow
spec (`SKILL.md`), and a static reference table (`badges.md`). **No test suite, no CI,
no fixtures, no CLAUDE.md existed before this audit.**

Items are ordered by **Human-Attention-Saved per Unit of Effort** — cheap changes that
remove a human from a currently-manual verification loop rank highest.

## Top 5 — immediately actionable

### 1. Add a stdlib-only unit test suite for `gen_branding.py` — ✅ DONE (2026-07-07)
**Effort:** low (helpers are pure functions; script has zero third-party deps to mock).
**Saves:** the only current way to check a generator edit didn't break output is a human
visually inspecting an SVG/PNG. Verified during this audit: `_hex`, `_clamp`, `_rgb`,
`lighten`, `darken`, `esc`, `fit`, and `PALETTES` are all pure and importable.

- Create `skills/repo-glowup/scripts/tests/test_gen_branding.py` using `unittest`
  (stdlib only — do not add `pytest` as a new dependency; the project's stated value is
  zero-dependency tooling).
- Cover: `lighten`/`darken` round-trip bounds (`_clamp` never exceeds 0–255), `esc`
  escapes `&`/`<`/`>`, `fit` shrinks font size when text exceeds available width, every
  key in `PALETTES` has exactly 6 hex colors matching `^#[0-9A-Fa-f]{6}$`.
- Add one subprocess smoke test: run `gen_branding.py --name X --palette ocean --outdir
  <tmp>`, assert the 3 expected files exist and each parses via
  `xml.etree.ElementTree.parse` without error.
- **Acceptance criteria:** `python3 -m unittest discover -s skills/repo-glowup/scripts/tests`
  exits 0 with no new pip installs.
- Implemented in `skills/repo-glowup/scripts/tests/test_gen_branding.py` (25 tests,
  stdlib `unittest`). Verified: `python3 -m unittest discover -s
  skills/repo-glowup/scripts/tests` → `Ran 25 tests in 0.35s / OK`.

### 2. Add a one-command self-check harness — ✅ DONE (2026-07-07)
**Effort:** low (shells out to scripts that already exist and were verified working).
**Saves:** an agent editing `SKILL.md` or the scripts currently has no way to confirm
"did this still work end-to-end" short of manually running each step (as this audit did).

- Create `skills/repo-glowup/scripts/selfcheck.sh`: loop over all 6 palette names, call
  `gen_branding.py` into a temp dir per palette, run `rasterize.sh` on each if
  `rsvg-convert` or `chrome`/`chromium` is present, then validate every `.svg` parses
  (`xml.etree.ElementTree`) and every `.png` opens via Pillow (`PIL.Image.open(...).size
  == (1280, 640)` for the social card). Print PASS/FAIL per palette; exit nonzero on any
  failure.
- **Acceptance criteria:** `bash skills/repo-glowup/scripts/selfcheck.sh` runs clean on a
  machine with `rsvg-convert` + Pillow present (both confirmed installed here) and
  degrades gracefully (skips rasterization, still validates SVGs) if absent.
- Implemented in `skills/repo-glowup/scripts/selfcheck.sh`. Verified: ran clean, all 6
  palettes → `PASS  ocean` / `PASS  ember` / `PASS  violet` / `PASS  forest` /
  `PASS  slate` / `PASS  crimson`, exit code 0.

### 3. Add ecosystem-detection fixtures — ✅ DONE (2026-07-07)
**Effort:** low (marker files only, no real projects needed).
**Saves:** `SKILL.md` step 1's stack-detection table (node/python/rust/go/php/ruby/
container/generic → palette) is currently only exercised against whatever real repo a
human happens to run `/repo-glowup` in. An agent has no repeatable way to confirm the
detection logic without borrowing an unrelated project.

- Create `.agent_native/fixtures/<ecosystem>/` for each of: `node` (`package.json`),
  `python` (`pyproject.toml`), `rust` (`Cargo.toml`), `go` (`go.mod`), `php`
  (`composer.json`), `ruby` (`Gemfile`), `container` (`Dockerfile`), `generic` (empty
  dir + a plain `README.md`). Each fixture needs only the marker file — content can be
  a minimal valid stub.
- **Acceptance criteria:** an agent can `cd .agent_native/fixtures/rust && ls` and
  independently confirm which marker file `SKILL.md` step 1 says should map to which
  palette, without needing network access or a real upstream project.
- Implemented: `.agent_native/fixtures/{node,python,rust,go,php,ruby,container,generic}/`
  each with the minimal marker file (`package.json`, `pyproject.toml`, `Cargo.toml`,
  `go.mod`, `composer.json`, `Gemfile`, `Dockerfile`, plain `README.md` for `generic`).

### 4. Write `CLAUDE.md` (this audit's other deliverable)
**Effort:** trivial (write-only, already done as part of this task).
**Saves:** every future agent session currently starts with zero repo-specific
conventions — frontmatter schema for `SKILL.md`, the dry-run recipe, and the
zero-dependency constraint were all tribal knowledge inferable only by reading the one
existing skill closely. Codified now; see `/home/user/Documents/vibe-code/repo-glowup/CLAUDE.md`.

### 5. Add minimal CI (`.github/workflows/ci.yml`) — ✅ DONE (2026-07-07)
**Effort:** low-medium (needs a Linux runner with `librsvg2-tools` installed via apt).
**Saves:** closes a specifically ironic gap — `references/badges.md` documents how to
add a live CI-status badge to *other* repos, but this repo has no CI itself, so there is
no automated signal after a skill edit besides a human re-running the dry run.

- Workflow: on push/PR, `apt-get install -y librsvg2-tools`, `pip install pillow`, then
  run `python3 -m py_compile skills/repo-glowup/scripts/*.py`, the unit tests from item
  1, and `selfcheck.sh` from item 2.
- **Acceptance criteria:** workflow passes on a fresh checkout with only `apt`/`pip`
  installs, no manual steps.
- Implemented: `.github/workflows/ci.yml` (runs py_compile, the item-1 unit tests, and
  item-2's `selfcheck.sh` on push/PR). YAML validity checked locally (`yaml.safe_load`
  succeeded); not yet exercised on an actual GitHub Actions runner since this repo has
  no remote configured in this environment.

## Lower-priority (worth doing, not top-5)

- **Golden-output snapshot tests** — byte-diff each palette's generated SVG against a
  committed snapshot to catch unintended visual drift from refactors (more valuable
  once the generator has more than one contributor).
- **`SKILL.md` frontmatter lint** — a tiny script asserting required YAML keys
  (`name`, `description`, `allowed-tools`) exist and `allowed-tools` only lists real
  tool names, so a malformed edit fails fast instead of silently breaking on load.
- **`CHANGELOG.md` + version-bump convention** tied to `.claude-plugin/plugin.json`'s
  `version` field (currently `0.1.0`, no history of bumps yet).
- **Refactor `rasterize.sh`'s Pillow re-encode into a small tested Python module** if
  it grows more logic — currently it's a 4-line inline `python3 -` heredoc, too small
  to warrant extraction today.

## Structural boundaries (cannot be automated away)

- **Step 7 (social-preview upload)** has no GitHub API; this is a genuine, permanent
  human-in-the-loop step. `SKILL.md` already flags it clearly — no change needed.
- **Step 2 (confirm metadata/palette wording)** is deliberately human-gated because
  wording and palette choice are subjective; codifying the *fields* shown (already done
  in `SKILL.md`'s table) is as far as this should go — do not try to auto-approve it.
- **`gh`-dependent steps** (About metadata, live workflow-status badges) require a real
  authenticated `gh` and a GitHub remote; they cannot be exercised in the fixtures above
  and should be tested manually against a throwaway repo when touched.
