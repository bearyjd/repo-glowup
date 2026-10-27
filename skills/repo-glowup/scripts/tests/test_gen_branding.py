"""Stdlib-only unit tests for gen_branding.py's pure helpers, plus a subprocess
smoke test of the CLI end-to-end.

Run with:
    python3 -m unittest discover -s skills/repo-glowup/scripts/tests
No third-party imports — mirrors the zero-dependency constraint on the
generator itself (see CLAUDE.md).
"""
from __future__ import annotations

import json
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
        # inputs chosen so the 60% size floor doesn't clamp both results to the same value
        text = "a" * 20
        default_size = gb.fit(84, 700, text)
        smaller_factor_size = gb.fit(84, 700, text, factor=0.20)
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


class HexShorthandTests(unittest.TestCase):
    def test_three_digit_expands(self):
        self.assertEqual(gb._hex("#111"), (17, 17, 17))
        self.assertEqual(gb._hex("abc"), (0xAA, 0xBB, 0xCC))

    def test_six_digit_unchanged(self):
        self.assertEqual(gb._hex("#1D74C8"), (0x1D, 0x74, 0xC8))


class ParseRampTests(unittest.TestCase):
    def test_string_with_shorthand_normalised(self):
        got = gb.parse_ramp("#111,#222,#333,#444,#555,#666")
        self.assertEqual(got, ["#111111", "#222222", "#333333",
                               "#444444", "#555555", "#666666"])

    def test_list_input_and_missing_hash(self):
        got = gb.parse_ramp(["abc", "#def", "112233", "#445566", "#778899", "#aabbcc"])
        self.assertEqual(got[0], "#AABBCC")
        self.assertEqual(got[5], "#AABBCC")
        for c in got:
            self.assertRegex(c, HEX_RE)

    def test_bad_colour_raises_with_message(self):
        with self.assertRaises(ValueError) as cm:
            gb.parse_ramp("#111,#222,#333,#444,#555,zzz")
        self.assertIn("zzz", str(cm.exception))

    def test_wrong_count_raises(self):
        with self.assertRaises(ValueError):
            gb.parse_ramp("#111,#222")

    def test_bad_type_raises(self):
        with self.assertRaises(ValueError):
            gb.parse_ramp(12345)

    def test_four_or_five_digit_hex_rejected(self):
        with self.assertRaises(ValueError):
            gb.parse_ramp("#1234,#222,#333,#444,#555,#666")


class EscQuoteTests(unittest.TestCase):
    def test_escapes_double_quote(self):
        self.assertEqual(gb.esc('say "hi"'), "say &quot;hi&quot;")

    def test_escapes_single_quote(self):
        self.assertEqual(gb.esc("it's"), "it&#39;s")


class FitFloorTests(unittest.TestCase):
    def test_default_floor_is_sixty_percent(self):
        self.assertAlmostEqual(gb.fit(100, 10, "a" * 500), 60)

    def test_explicit_size_min(self):
        self.assertAlmostEqual(gb.fit(100, 10, "a" * 500, size_min=40), 40)

    def test_spacing_shrinks_size(self):
        self.assertLess(gb.fit(24, 300, "a" * 20, 0.6, spacing=0.25),
                        gb.fit(24, 300, "a" * 20, 0.6))


class TruncateTests(unittest.TestCase):
    def test_fits_unchanged(self):
        self.assertEqual(gb.truncate("short", 500, 20, 0.6), "short")

    def test_too_long_gets_ellipsis_and_fits(self):
        out = gb.truncate("x" * 100, 200, 20, 0.6)
        self.assertTrue(out.endswith("\u2026"))
        self.assertLessEqual(len(out) * 20 * 0.6, 200)

    def test_empty(self):
        self.assertEqual(gb.truncate("", 10, 20, 0.6), "")

    def test_tiny_avail_still_returns_ellipsis(self):
        self.assertEqual(gb.truncate("abcdef", 1, 20, 0.6), "\u2026")


class FitTextBoundaryTests(unittest.TestCase):
    """Text that fit() shrinks to exactly fit must not then be truncated (float edge)."""

    def test_real_social_card_strings_are_kept(self):
        tagline = "Bazzite KDE + NVIDIA, tuned for a Meteor Lake ThinkPad"
        subline = "bootc switch ghcr.io/bearyjd/bazzite-tower:latest"
        self.assertEqual(gb.fit_text(tagline, 30, 652, 0.50)[1], tagline)
        self.assertEqual(gb.fit_text(subline, 25, 652, 0.62)[1], subline)

    def test_no_truncation_whenever_fit_did_not_hit_the_floor(self):
        for avail in (300, 652, 940):
            for factor in (0.50, 0.56, 0.62):
                for n in range(1, 121):
                    text = "x" * n
                    size = gb.fit(30, avail, text, factor)
                    if size > 30 * 0.6:  # shrunk (or not) but above the floor: it fits
                        self.assertEqual(gb.fit_text(text, 30, avail, factor)[1], text,
                                         (avail, factor, n))


class CoerceTests(unittest.TestCase):
    def test_numbers_become_strings_and_missing_default_empty(self):
        out = gb.coerce_text({"name": 123, "tagline": 4.5, "eyebrow": None})
        self.assertEqual(out["name"], "123")
        self.assertEqual(out["tagline"], "4.5")
        self.assertEqual(out["eyebrow"], "")
        self.assertEqual(out["subline"], "")
        self.assertEqual(out["footnote"], "")

    def test_does_not_mutate_input(self):
        src = {"name": 1}
        gb.coerce_text(src)
        self.assertEqual(src, {"name": 1})


HOSTILE = [
    'The "fast" thing',
    "it's a & b < c > d",
    "caf\u00e9 \u65e5\u672c\u8a9e \u0645\u0631\u062d\u0628\u0627",
    "rocket \U0001F680 launch \U0001F468\u200d\U0001F4BB",
    "x" * 400,
]


class HostileBuildTests(unittest.TestCase):
    def test_all_fields_hostile_parse_everywhere(self):
        ramp = gb.PALETTES["ocean"]
        for text in HOSTILE:
            cfg = {"name": text, "eyebrow": text, "tagline": text,
                   "subline": text, "footnote": text}
            for kind in ("banner", "social"):
                for theme in ("dark", "light"):
                    with self.subTest(text=text[:12], kind=kind, theme=theme):
                        ET.fromstring(gb.build(kind, theme, cfg, ramp))

    def test_long_text_is_truncated_with_ellipsis(self):
        cfg = {"name": "n", "subline": "y" * 400, "footnote": "z" * 400,
               "eyebrow": "E" * 400}
        svg = gb.build("social", "dark", cfg, gb.PALETTES["ocean"])
        self.assertNotIn("y" * 400, svg)
        self.assertGreaterEqual(svg.count("\u2026"), 3)

    def test_normal_text_not_truncated(self):
        cfg = {"name": "proj", "eyebrow": "TEST", "tagline": "A tagline",
               "subline": "npm i proj", "footnote": "a . b . c"}
        svg = gb.build("social", "dark", cfg, gb.PALETTES["ocean"])
        self.assertNotIn("\u2026", svg)
        self.assertIn('font-size="24" letter-spacing="6"', svg)
        self.assertIn('font-size="84"', svg)


def run_cli(*args):
    return subprocess.run([sys.executable, str(SCRIPTS_DIR / "gen_branding.py"), *args],
                          capture_output=True, text=True, timeout=30)


class CliTests(unittest.TestCase):
    def test_short_hex_ramp_generates(self):
        with tempfile.TemporaryDirectory() as d:
            r = run_cli("--name", "X", "--ramp", "#111,#222,#333,#444,#555,#666",
                        "--outdir", d)
            self.assertEqual(r.returncode, 0, r.stderr)
            ET.parse(Path(d) / "social-preview.svg")

    def test_bad_ramp_exits_2_without_traceback(self):
        with tempfile.TemporaryDirectory() as d:
            r = run_cli("--name", "X", "--ramp", "#111,#222,#333,#444,#555,nope",
                        "--outdir", d)
            self.assertEqual(r.returncode, 2)
            self.assertNotIn("Traceback", r.stderr)
            self.assertIn("nope", r.stderr)

    def test_bad_ramp_in_config_list_exits_2(self):
        with tempfile.TemporaryDirectory() as d:
            cfgp = Path(d) / "c.json"
            cfgp.write_text(json.dumps({"name": "X", "outdir": d,
                                        "ramp": ["#111", "#222", "#333", "#444", "#555", "#12"]}))
            r = run_cli("--config", str(cfgp))
            self.assertEqual(r.returncode, 2)
            self.assertNotIn("Traceback", r.stderr)

    def test_config_ramp_list_and_string_and_numeric_scalars(self):
        ramps = [["#111", "#222", "#333", "#444", "#555", "#666"],
                 "#111,#222,#333,#444,#555,#666"]
        for ramp in ramps:
            with self.subTest(ramp=ramp), tempfile.TemporaryDirectory() as d:
                cfgp = Path(d) / "c.json"
                cfgp.write_text(json.dumps({"name": 123, "tagline": 4.5, "subline": 7,
                                            "outdir": d, "ramp": ramp}))
                r = run_cli("--config", str(cfgp))
                self.assertEqual(r.returncode, 0, r.stderr)
                ET.parse(Path(d) / "banner.svg")

    def test_wrong_ramp_type_in_config_exits_2(self):
        with tempfile.TemporaryDirectory() as d:
            cfgp = Path(d) / "c.json"
            cfgp.write_text(json.dumps({"name": "X", "outdir": d, "ramp": 5}))
            r = run_cli("--config", str(cfgp))
            self.assertEqual(r.returncode, 2)
            self.assertNotIn("Traceback", r.stderr)

    def test_empty_ramp_in_config_exits_2(self):
        for ramp in ([], "", {}):
            with self.subTest(ramp=ramp), tempfile.TemporaryDirectory() as d:
                cfgp = Path(d) / "c.json"
                cfgp.write_text(json.dumps({"name": "X", "outdir": d, "ramp": ramp}))
                r = run_cli("--config", str(cfgp))
                self.assertEqual(r.returncode, 2)
                self.assertNotIn("Traceback", r.stderr)

    def test_null_ramp_falls_back_to_palette(self):
        with tempfile.TemporaryDirectory() as d:
            cfgp = Path(d) / "c.json"
            cfgp.write_text(json.dumps({"name": "X", "outdir": d, "ramp": None}))
            self.assertEqual(run_cli("--config", str(cfgp)).returncode, 0)

    def test_non_string_palette_exits_2_without_traceback(self):
        for pal in (["ocean"], 5):
            with self.subTest(palette=pal), tempfile.TemporaryDirectory() as d:
                cfgp = Path(d) / "c.json"
                cfgp.write_text(json.dumps({"name": "X", "outdir": d, "palette": pal}))
                r = run_cli("--config", str(cfgp))
                self.assertEqual(r.returncode, 2)
                self.assertNotIn("Traceback", r.stderr)

    def test_quoted_tagline_cli_parses(self):
        with tempfile.TemporaryDirectory() as d:
            r = run_cli("--name", "X", "--tagline", 'The "fast" thing', "--outdir", d)
            self.assertEqual(r.returncode, 0, r.stderr)
            for f in ("banner.svg", "banner-light.svg", "social-preview.svg"):
                ET.parse(Path(d) / f)


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
