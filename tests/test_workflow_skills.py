"""New workflow entry points must be discoverable without increasing implicit scope."""
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ENTRY_POINTS = ("project-verify", "triage", "research", "statechart")


class WorkflowSkills(unittest.TestCase):
    def test_explicit_entry_points_are_registered_on_both_hosts(self):
        router = (ROOT / "skills/honey/SKILL.md").read_text()
        readme = (ROOT / "README.md").read_text()
        for name in ENTRY_POINTS:
            with self.subTest(skill=name):
                directory = ROOT / "skills" / name
                skill = (directory / "SKILL.md").read_text()
                frontmatter = skill.split("---", 2)[1]
                self.assertRegex(frontmatter, rf"(?m)^name: {name}$")
                self.assertIn("disable-model-invocation: true", frontmatter)
                self.assertIn("license: MIT", frontmatter)
                self.assertIn("sources:", frontmatter)
                metadata = (directory / "agents/openai.yaml").read_text()
                self.assertIn("allow_implicit_invocation: false", metadata)
                description = re.search(r'short_description: "([^"]+)"', metadata)
                self.assertIsNotNone(description)
                self.assertTrue(25 <= len(description[1]) <= 64)
                self.assertIn(f"`{name}`", router)
                self.assertIn(f"`{name}`", readme)

    def test_workflow_reference_links_are_shipped(self):
        directories = ENTRY_POINTS + ("frontend", "qa", "perf", "rsi", "write-skill")
        for name in directories:
            for path in (ROOT / "skills" / name).rglob("*.md"):
                # Links in fenced examples are instructions for generated files,
                # not dependencies of the distributed skill itself.
                prose = re.sub(r"```.*?```", "", path.read_text(), flags=re.S)
                for target in re.findall(r"\]\(([^)]+)\)", prose):
                    if "://" in target or target.startswith(("#", "/")):
                        continue
                    with self.subTest(source=str(path), target=target):
                        self.assertTrue((path.parent / target.split("#")[0]).exists())


if __name__ == "__main__":
    unittest.main()
