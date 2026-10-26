"""Validate references/ecosystems.json against gen_branding.PALETTES and the fixtures."""
import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import gen_branding  # noqa: E402

ECO_PATH = ROOT / "skills" / "repo-glowup" / "references" / "ecosystems.json"
FIXTURES = ROOT / ".agent_native" / "fixtures"


class EcosystemsTest(unittest.TestCase):
    def setUp(self):
        self.data = json.loads(ECO_PATH.read_text(encoding="utf-8"))

    def test_shape(self):
        for name, spec in self.data.items():
            self.assertIsInstance(spec["markers"], list, name)
            self.assertIsInstance(spec["palette"], str, name)
            self.assertIsInstance(spec["alt_markers"], list, name)
            self.assertTrue(all(isinstance(m, str) for m in spec["alt_markers"]), name)

    def test_palettes_exist(self):
        for name, spec in self.data.items():
            self.assertIn(spec["palette"], gen_branding.PALETTES, name)

    def test_markers_exist_in_fixtures(self):
        for name, spec in self.data.items():
            for marker in spec["markers"]:
                self.assertTrue((FIXTURES / name / marker).exists(), f"{name}/{marker}")

    def test_all_fixtures_covered(self):
        fixtures = {p.name for p in FIXTURES.iterdir() if p.is_dir()}
        self.assertEqual(fixtures, set(self.data))

    def test_go_and_container_differ_from_python(self):
        py = self.data["python"]["palette"]
        self.assertNotEqual(self.data["go"]["palette"], py)
        self.assertNotEqual(self.data["container"]["palette"], py)


if __name__ == "__main__":
    unittest.main()
