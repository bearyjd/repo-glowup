# repo-glowup — agent guide

A Claude Code **plugin** (not an app): one skill, `repo-glowup`, that gives a target
repository a branded README hero, badge chips, a social-preview card, and accurate
GitHub About metadata. This file is repo-specific guidance for agents editing the
plugin itself (the skill, its scripts, its docs) — not for repos the skill is *run
against*.

## Layout

- `skills/repo-glowup/SKILL.md` — the workflow spec (frontmatter + 8 numbered steps).
  This *is* the prompt Claude Code loads when the skill triggers; treat edits to it like
  edits to a spec, not prose.
- `skills/repo-glowup/scripts/gen_branding.py` — SVG generator. **Stdlib-only, no
  third-party imports.** Do not add a dependency here without discussing it — the
  README explicitly advertises "Python (stdlib only)" as a feature.
- `skills/repo-glowup/scripts/rasterize.sh` — shells out to `rsvg-convert` (preferred)
  or `google-chrome`/`chromium` (fallback) to rasterize SVG → PNG, then re-encodes
  through Pillow if available for a GitHub-safe upload. Degrades gracefully step by
  step if a dependency is missing — preserve that behavior in any edit.
- `skills/repo-glowup/references/badges.md` — static shields.io lookup table (hex
  colors, simple-icons slugs). Verify slugs at simpleicons.org before adding new rows;
  an unknown slug silently drops the logo rather than erroring.
- `.claude-plugin/plugin.json` / `marketplace.json` — plugin manifest and marketplace
  entry. Keep `version` in `plugin.json` in sync with any user-visible behavior change.
- `.agent_native/agent_roadmap.md` — prioritized list of testing/verification gaps and
  the recommended next changes to make this repo more agent-operable.

## Conventions when editing `SKILL.md`

- Frontmatter requires `name`, `description` (used for trigger-matching — keep it
  specific to the phrases a user would actually type), `argument-hint`, and
  `allowed-tools` (must list only tools Claude Code actually grants; don't add tools the
  workflow doesn't use).
- Steps reference `${CLAUDE_PLUGIN_ROOT}` for bundled script/reference paths — never
  hardcode a path relative to some other assumed cwd, since the skill runs from
  whatever repo it was invoked in, not from this plugin's own checkout.
- The README hero block is wrapped in `<!-- glowup:hero start/end -->` markers and must
  stay idempotent — re-running the skill replaces only the content between the markers,
  never duplicates or drops the rest of the README.

## Validating a change (no test suite existed before this audit — this is the verified manual recipe)

There is currently no `pytest`/`npm test`/CI entry point in this repo. Until
`.agent_native/agent_roadmap.md` item 1 (unit tests) and item 5 (CI) are done, validate
any change to the generator or rasterizer by actually running them:

```bash
# 1. Script still parses/compiles
python3 -m py_compile skills/repo-glowup/scripts/gen_branding.py
bash -n skills/repo-glowup/scripts/rasterize.sh

# 2. Generate into a scratch dir and inspect the SVGs
python3 skills/repo-glowup/scripts/gen_branding.py \
  --name test-proj --palette ocean --eyebrow "TEST" \
  --tagline "A test tagline" --subline "npm i test-proj" \
  --footnote "a . b . c" --outdir /tmp/glowup_check
# expect: "wrote /tmp/glowup_check/{banner.svg,banner-light.svg,social-preview.svg}"

# 3. Rasterize and confirm GitHub-safe PNG/JPG output
bash skills/repo-glowup/scripts/rasterize.sh /tmp/glowup_check
file /tmp/glowup_check/social-preview.png  # expect: PNG image data, 1280 x 640
```

Confirmed present in this environment: `python3` (3.14), `rsvg-convert`, `google-chrome`,
Pillow (`python3 -c "import PIL"` succeeds), and `gh` (2.87.3) — so the full pipeline
including the Pillow re-encode step can be exercised end-to-end, not just the
degraded/fallback paths. If you only have a subset installed, the scripts are designed
to warn and continue rather than fail hard — treat a *new* hard failure on a missing
optional dependency as a regression.

Re-run the same recipe for **every palette** (`ocean`, `ember`, `violet`, `forest`,
`slate`, `crimson`) after touching `PALETTES`, `lighten`/`darken`, or the SVG layout
constants in `build()` — a change to shared geometry/color logic affects all six.

Do not hand-wave "looks right" — actually read the generated SVG file or the rasterized
PNG (e.g. via the `Read` tool) before claiming a visual change works.

## Style

- Keep `gen_branding.py` dependency-free; keep `rasterize.sh`'s dependency checks
  (`command -v rsvg-convert`, `python3 -c "import PIL"`) as soft, warn-and-continue
  checks, not hard requirements.
- Match existing code density: `gen_branding.py` is intentionally compact (single-file,
  ~270 lines, no framework) — don't split it into a package for a small feature.
- Any new user-facing behavior in `SKILL.md` must specify what happens when its
  dependency is missing (mirrors the existing preflight table in step 0).
