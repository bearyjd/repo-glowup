"""Lint SKILL.md frontmatter (hand-parsed, stdlib only) and its bundled-path references."""
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
SKILL = ROOT / "skills" / "repo-glowup" / "SKILL.md"
KNOWN_TOOLS = {"Bash", "Read", "Edit", "Write", "AskUserQuestion", "Skill",
               "Glob", "Grep", "WebFetch"}


def parse_frontmatter(text):
    m = re.match(r"---\n(.*?)\n---\n", text, re.S)
    assert m, "missing frontmatter"
    out, key = {}, None
    for line in m.group(1).splitlines():
        if re.match(r"^\s+- ", line):
            out[key].append(line.strip()[2:].strip())
        elif re.match(r"^\s+\S", line):
            out[key] = (out[key] + " " + line.strip()).strip()
        else:
            key, _, val = line.partition(":")
            val = val.strip()
            out[key] = [] if val == "" else ("" if val == ">" else val.strip('"'))
    return out


class SkillFrontmatterTest(unittest.TestCase):
    def setUp(self):
        self.text = SKILL.read_text(encoding="utf-8")
        self.fm = parse_frontmatter(self.text)

    def test_required_keys(self):
        for k in ("name", "description", "argument-hint", "allowed-tools"):
            self.assertTrue(self.fm.get(k), k)

    def test_description_starts_with_use_when(self):
        self.assertTrue(self.fm["description"].startswith("Use when"))

    def test_allowed_tools_known(self):
        self.assertLessEqual(set(self.fm["allowed-tools"]), KNOWN_TOOLS)

    def test_branding_json_keys_documented(self):
        # scoped to the step 3 sentence: a stray mention elsewhere must not satisfy it
        m = re.search(r"Write `<CFG>/branding\.json` with keys(.*?)\(CLI flags", self.text, re.S)
        if m is None:
            self.fail("step 3 keys sentence not found")
        for k in ("name", "palette", "eyebrow", "tagline", "subline", "footnote",
                  "ramp", "outdir"):
            self.assertIn(f"`{k}`", m.group(1), k)

    def test_asks_for_direction_the_repo_does_not_state(self):
        # the repo can't say where a project is heading; step 2 must ask the user
        self.assertRegex(self.text, r"(?s)## 2 ·.*?emphasi[sz]e.*?## 3 ·")

    def test_unchanged_readme_has_a_message(self):
        self.assertIn("already up to date", self.text)

    def test_plugin_root_paths_exist(self):
        paths = re.findall(r"\$\{CLAUDE_PLUGIN_ROOT\}/([^\s\"'`)]+)", self.text)
        self.assertTrue(paths)
        for p in paths:
            self.assertTrue((ROOT / p).exists(), p)


if __name__ == "__main__":
    unittest.main()
