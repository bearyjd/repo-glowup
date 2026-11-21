"""Pin copies of gen_branding.py facts held by other consumers (shell scripts, SKILL.md)."""
import re
import sys
import unittest
from pathlib import Path

SCRIPTS_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(SCRIPTS_DIR))

import gen_branding as gb  # noqa: E402

SKILL = (SCRIPTS_DIR.parent / "SKILL.md").read_text(encoding="utf-8")
SELFCHECK = (SCRIPTS_DIR / "selfcheck.sh").read_text(encoding="utf-8")
RASTERIZE = (SCRIPTS_DIR / "rasterize.sh").read_text(encoding="utf-8")


def svg_size(kind, theme):
    svg = gb.build(kind, theme, {"name": "X"}, gb.PALETTES["ocean"])
    m = re.search(r'viewBox="0 0 (\d+) (\d+)"', svg)
    return int(m.group(1)), int(m.group(2))


class ConsumerContractTests(unittest.TestCase):
    def test_selfcheck_covers_every_palette(self):
        m = re.search(r"^PALETTES=\((.*?)\)", SELFCHECK, re.M)
        self.assertIsNotNone(m, "PALETTES array not found in selfcheck.sh")
        self.assertEqual(set(m.group(1).split()), set(gb.PALETTES))

    def test_skill_documents_every_config_key(self):
        m = re.search(r"Write `<CFG>/branding\.json` with keys(.*?)\(CLI flags", SKILL, re.S)
        self.assertIsNotNone(m, "step 3 keys sentence not found")
        for k in (*gb.TEXT_KEYS, "palette", "ramp", "outdir"):
            self.assertIn(f"`{k}`", m.group(1), k)

    def test_rasterize_sizes_match_generated_canvases(self):
        w, h = svg_size("social", "dark")
        self.assertIn(f'"$PNG" {w} {h}', RASTERIZE)
        for theme in ("dark", "light"):
            w, h = svg_size("banner", theme)
            self.assertIn(f'"$PREVIEW/$b.png" {w} {h}', RASTERIZE)


if __name__ == "__main__":
    unittest.main()
