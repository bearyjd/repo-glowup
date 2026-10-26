"""rasterize.sh with a fake google-chrome that exits 0 but writes nothing."""
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[1] / "rasterize.sh"
BASH = shutil.which("bash")


@unittest.skipUnless(BASH, "bash not available")
class ChromeNoOutputTests(unittest.TestCase):
    def _run(self, with_preview, social_ok=False):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            bin_dir, assets, prev = root / "bin", root / "assets", root / "prev"
            bin_dir.mkdir()
            assets.mkdir()
            fake = bin_dir / "google-chrome"
            good = root / "good.png"
            subprocess.run(["python3", "-c",
                            "from PIL import Image;Image.new('RGB',(4,4)).save('%s')" % good],
                           check=False)
            # write a PNG only for the social render; banner renders produce nothing
            fake.write_text('#!/bin/sh\nfor a in "$@"; do case "$a" in --screenshot=*social*)'
                            + (' cp "%s" "${a#--screenshot=}";;' % good if social_ok else ';;')
                            + ' esac; done\nexit 0\n')
            fake.chmod(0o755)
            # symlink only the tools the script needs, so rsvg-convert is hidden
            for tool in ("wc", "mkdir", "readlink", "python3", "dirname", "rm", "cp"):
                src = shutil.which(tool)
                if src:
                    (bin_dir / tool).symlink_to(src)
            svg = '<svg xmlns="http://www.w3.org/2000/svg" width="10" height="10"/>'
            for n in ("social-preview", "banner", "banner-light"):
                (assets / f"{n}.svg").write_text(svg)
            args = [BASH, str(SCRIPT), str(assets)] + ([str(prev)] if with_preview else [])
            env = {"PATH": str(bin_dir), "HOME": d}
            return subprocess.run(args, capture_output=True, text=True, env=env, timeout=30)

    def test_social_render_failure_exits_2_without_traceback(self):
        r = self._run(False)
        self.assertEqual(r.returncode, 2, r.stderr)
        self.assertIn("WARN", r.stderr)
        self.assertIn("install", r.stderr)
        self.assertNotIn("Traceback", r.stderr)

    def test_preview_render_failure_warns_and_continues(self):
        try:
            import PIL  # noqa: F401
        except ImportError:
            self.skipTest("Pillow needed to build the fake social PNG")
        r = self._run(True, social_ok=True)
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("WARN", r.stderr)
        self.assertNotIn("Traceback", r.stderr)


if __name__ == "__main__":
    unittest.main()
