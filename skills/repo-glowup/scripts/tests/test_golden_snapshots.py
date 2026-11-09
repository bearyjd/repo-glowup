"""Golden-output snapshot tests for gen_branding.py (stdlib unittest only).

Each case runs the real CLI with fixed inputs and byte-compares every emitted SVG
against a committed snapshot under tests/golden/<case>/. This catches unintended
visual drift from refactors. The generator is deterministic (no timestamps or
randomness), so any diff is a real change in output.

Run:
    python3 -m unittest discover -s skills/repo-glowup/scripts/tests

Intentional output change? Regenerate the snapshots, then review the git diff:
    GLOWUP_UPDATE_GOLDEN=1 python3 -m unittest \
        discover -s skills/repo-glowup/scripts/tests -p 'test_golden_snapshots.py'
"""
from __future__ import annotations

import difflib
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

TESTS_DIR = Path(__file__).resolve().parent
SCRIPTS_DIR = TESTS_DIR.parent
GOLDEN_DIR = TESTS_DIR / "golden"
SVG_NAMES = ("banner.svg", "banner-light.svg", "social-preview.svg")
UPDATE = os.environ.get("GLOWUP_UPDATE_GOLDEN") == "1"

BASE_TEXT = [
    "--name", "Demo Repo",
    "--eyebrow", "OPEN SOURCE",
    "--tagline", "A tidy tagline for snapshot tests",
    "--subline", "Second line of supporting copy",
    "--footnote", "v1.2.3 - MIT",
]

# case name -> extra CLI args. Palettes mirror gen_branding.PALETTES; the test
# below asserts the two stay in sync so a new palette cannot go unsnapshotted.
CASES: dict[str, list[str]] = {
    f"palette-{p}": [*BASE_TEXT, "--palette", p]
    for p in ("ocean", "ember", "violet", "forest", "slate", "crimson")
}
CASES["custom-ramp-short-hex"] = [*BASE_TEXT, "--ramp", "#111,#222,#333,#444,#555,#666"]
CASES["minimal-name-only"] = ["--name", "X"]
CASES["long-name-escaped-text"] = [
    "--name", "A-very-long-repository-name-that-must-shrink-or-truncate-to-fit",
    "--tagline", "Fish & Chips <b>\"quoted\"</b>",
    "--palette", "slate",
]


def generate(extra_args: list[str], outdir: Path) -> None:
    r = subprocess.run(
        [sys.executable, str(SCRIPTS_DIR / "gen_branding.py"), *extra_args,
         "--outdir", str(outdir)],
        capture_output=True, text=True, timeout=30,
    )
    if r.returncode != 0:
        raise AssertionError(f"gen_branding failed ({r.returncode}): {r.stderr}")


class GoldenSnapshotTests(unittest.TestCase):
    def test_every_palette_has_a_snapshot_case(self):
        sys.path.insert(0, str(SCRIPTS_DIR))
        import gen_branding as gb
        self.assertEqual({f"palette-{p}" for p in gb.PALETTES},
                         {c for c in CASES if c.startswith("palette-")})

    def test_no_orphaned_snapshot_dirs(self):
        if UPDATE or not GOLDEN_DIR.exists():
            self.skipTest("update mode / no golden dir")
        on_disk = {p.name for p in GOLDEN_DIR.iterdir() if p.is_dir()}
        self.assertEqual(on_disk, set(CASES), "golden dirs and CASES differ")


def _make_case_test(case: str, args: list[str]):
    def test(self):
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp)
            generate(args, out)
            self.assertEqual(sorted(p.name for p in out.iterdir()), sorted(SVG_NAMES))
            for name in SVG_NAMES:
                actual = (out / name).read_bytes()
                golden = GOLDEN_DIR / case / name
                if UPDATE:
                    golden.parent.mkdir(parents=True, exist_ok=True)
                    golden.write_bytes(actual)
                    continue
                self.assertTrue(
                    golden.exists(),
                    f"missing snapshot {golden}; run with GLOWUP_UPDATE_GOLDEN=1",
                )
                expected = golden.read_bytes()
                if actual != expected:
                    diff = "\n".join(list(difflib.unified_diff(
                        expected.decode().splitlines(), actual.decode().splitlines(),
                        "golden", "actual", lineterm="", n=1))[:40])
                    self.fail(f"{case}/{name} differs from snapshot:\n{diff}")
    return test


for _case, _args in CASES.items():
    setattr(GoldenSnapshotTests, "test_" + _case.replace("-", "_"),
            _make_case_test(_case, _args))


if __name__ == "__main__":
    unittest.main()
