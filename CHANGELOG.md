# Changelog

All notable changes to this project are documented here. Format follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

## [0.2.1]

### Fixed
- `gen_branding.py`: social-card text is no longer truncated by a float-boundary bug in
  the text-fitting logic.

### Changed (`SKILL.md` clarifications)
- Detection: `generic` is fallback only; default branch falls back to the local branch
  and `init.defaultBranch`; no-remote repos derive names from the directory/manifests and
  treat visibility as unknown; `bootc switch` subline form.
- Topics: existing topics are kept (additions only); `gh repo edit` is skipped when
  nothing changed; existing glowup assets dirs are reused; existing chips are listed.
- Art: `branding.json` keys listed; tighter tagline/subline limits for the social card,
  ellipsis treated as a failure; cleanup uses `rm -r --` on the two temp paths.
- README: blank line after `<div align="center">`, one badge per line, duplicate H1 and
  old banner handling, badge check retries once; step 8 gives an image-path check command.

## [0.2.0]

### Changed (generator and rasterizer, implemented separately from the skill spec)
- `gen_branding.py`: validation of short hex colors and ramps, quote escaping, text
  fitting to avoid overflow.
- `rasterize.sh`: banner previews written to a separate preview dir, size warning when
  the PNG exceeds 1 MB, exit code 2 when no rasterizer is available.

### Changed (`SKILL.md`)
- Added `Skill` to `allowed-tools`; flags are now `[--no-about] [--docs] [--dry-run]`
  (docs step is opt-in; `--dry-run` changes nothing in the repo).
- Default-branch and repo-visibility detection; private repos skip `github/*` badges.
- Ecosystem to palette mapping moved to `references/ecosystems.json`; polyglot repos
  prompt for a choice; go and container no longer share python's palette.
- `branding.json` is written to a temp dir; configurable asset dir with site-docs check.
- README handling for non-markdown, missing, and pre-existing hero cases, plus a diff.
- About step merges topics (approved removals only), keeps existing homepage, and
  prints the `gh` command on permission errors.
- Final step states that nothing is committed and shows `git status --short`.

### Added
- `references/badges.md`: Packagist, RubyGems, Maven Central, NuGet; tech chips for
  Ruby, PHP, Java, Kotlin, Swift, C++, Deno, Bun, Vue, Tailwind CSS, SQLite, Terraform,
  Nix, GitHub Actions; label-encoding and private-repo notes.
- Tests: `test_ecosystems.py`, `test_skill_frontmatter.py`.

## [0.1.0]
- Initial release: repo-glowup skill with SVG banner/social-card generator, rasterizer,
  badge reference, and README hero wiring.
