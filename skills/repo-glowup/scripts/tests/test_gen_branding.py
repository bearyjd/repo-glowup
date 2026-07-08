"""Stdlib-only unit tests for gen_branding.py's pure helpers, plus a subprocess
smoke test of the CLI end-to-end.

Run with:
    python3 -m unittest discover -s skills/repo-glowup/scripts/tests
No third-party imports — mirrors the zero-dependency constraint on the
generator itself (see CLAUDE.md).
"""
from __future__ import annotations

import re
import subprocess
import sys
import tempfile
import unittest
import xml.etree.ElementTree as ET
from pathlib import Path

SCRIPTS_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(SCRIPTS_DIR))

import gen_branding as gb  # noqa: E402

HEX_RE = re.compile(r"^#[0-9A-Fa-f]{6}$")


class ClampTests(unittest.TestCase):
    def test_clamp_within_range(self):
        self.assertEqual(gb._clamp(128), 128)

    def test_clamp_never_below_zero(self):
        self.assertEqual(gb._clamp(-50), 0)

    def test_clamp_never_above_255(self):
        self.assertEqual(gb._clamp(500), 255)

    def test_clamp_rounds(self):
        self.assertEqual(gb._clamp(127.6), 128)


class LightenDarkenTests(unittest.TestCase):
    def test_lighten_darken_roundtrip_bounds(self):
        for hexcolor in ("#000000", "#FFFFFF", "#1D74C8", "#7A2A11"):
            for f in (0.0, 0.18, 0.5, 1.0):
                lightened = gb.lighten(hexcolor, f)
                darkened = gb.darken(hexcolor, f)
                for value in (lightened, darkened):
                    self.assertRegex(value, HEX_RE)
                    r, g, b = gb._hex(value)
                    for channel in (r, g, b):
                        self.assertGreaterEqual(channel, 0)
                        self.assertLessEqual(channel, 255)

    def test_lighten_moves_toward_white(self):
        result = gb.lighten("#000000", 1.0)
        self.assertEqual(result, "#FFFFFF")

    def test_lighten_zero_factor_is_identity(self):
        self.assertEqual(gb.lighten("#123456", 0.0), "#123456")

    def test_darken_moves_toward_black(self):
        result = gb.darken("#FFFFFF", 1.0)
        self.assertEqual(result, "#000000")

    def test_darken_zero_factor_is_identity(self):
        self.assertEqual(gb.darken("#123456", 0.0), "#123456")


class EscTests(unittest.TestCase):
    def test_escapes_ampersand(self):
        self.assertEqual(gb.esc("A & B"), "A &amp; B")

    def test_escapes_angle_brackets(self):
        self.assertEqual(gb.esc("<script>"), "&lt;script&gt;")

    def test_escapes_all_together(self):
        self.assertEqual(gb.esc("<a & b>"), "&lt;a &amp; b&gt;")

    def test_no_special_chars_unchanged(self):
        self.assertEqual(gb.esc("plain text"), "plain text")

    def test_ampersand_escaped_before_reintroducing_entities(self):
        # & must be escaped first so lt;/gt; below aren't double-escaped.
        self.assertEqual(gb.esc("<&>"), "&lt;&amp;&gt;")


class FitTests(unittest.TestCase):
    def test_empty_text_returns_max_size(self):
        self.assertEqual(gb.fit(84, 500, ""), 84)

    def test_short_text_returns_max_size(self):
        size = gb.fit(84, 1000, "hi")
        self.assertEqual(size, 84)

    def test_long_text_shrinks_below_max(self):
        long_text = "a" * 200
        size = gb.fit(84, 500, long_text)
        self.assertLess(size, 84)

    def test_shrunk_size_is_never_negative(self):
        size = gb.fit(84, 10, "a" * 500)
        self.assertGreater(size, 0)

    def test_custom_factor_changes_result(self):
        text = "a" * 100
        default_size = gb.fit(84, 500, text)
        smaller_factor_size = gb.fit(84, 500, text, factor=0.20)
        self.assertGreater(smaller_factor_size, default_size)


class PalettesTests(unittest.TestCase):
    def test_expected_palette_names_present(self):
        expected = {"ocean", "ember", "violet", "forest", "slate", "crimson"}
        self.assertEqual(set(gb.PALETTES.keys()), expected)

    def test_every_palette_has_six_colors(self):
        for name, colors in gb.PALETTES.items():
            with self.subTest(palette=name):
                self.assertEqual(len(colors), 6)

    def test_every_color_is_valid_hex(self):
        for name, colors in gb.PALETTES.items():
            for color in colors:
                with self.subTest(palette=name, color=color):
                    self.assertRegex(color, HEX_RE)


class BuildTests(unittest.TestCase):
    """Sanity-check the SVG builder produces well-formed, parseable XML."""

    def test_build_produces_valid_xml_for_all_kinds_and_themes(self):
        cfg = {
            "name": "test-proj",
            "eyebrow": "TEST",
            "tagline": "A test tagline",
            "subline": "npm i test-proj",
            "footnote": "a . b . c",
        }
        ramp = gb.PALETTES["ocean"]
        for kind in ("banner", "social"):
            for theme in ("dark", "light"):
                with self.subTest(kind=kind, theme=theme):
                    svg = gb.build(kind, theme, cfg, ramp)
                    ET.fromstring(svg)

    def test_build_escapes_name_in_output(self):
        cfg = {"name": "A & B <script>"}
        ramp = gb.PALETTES["ocean"]
        svg = gb.build("banner", "dark", cfg, ramp)
        self.assertNotIn("<script>", svg)
        ET.fromstring(svg)  # must still be well-formed


class SmokeTest(unittest.TestCase):
    """End-to-end subprocess run of gen_branding.py's CLI."""

    def test_cli_generates_three_valid_svgs(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            result = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPTS_DIR / "gen_branding.py"),
                    "--name", "X",
                    "--palette", "ocean",
                    "--outdir", tmpdir,
                ],
                capture_output=True,
                text=True,
                timeout=30,
            )
            self.assertEqual(result.returncode, 0, msg=result.stderr)

            expected_files = ("banner.svg", "banner-light.svg", "social-preview.svg")
            for fname in expected_files:
                path = Path(tmpdir) / fname
                with self.subTest(file=fname):
                    self.assertTrue(path.exists(), f"missing {path}")
                    ET.parse(path)  # raises on malformed XML


if __name__ == "__main__":
    unittest.main()
