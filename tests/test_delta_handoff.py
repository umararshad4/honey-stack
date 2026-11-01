"""Exercise handoff provenance through the CLI, replacing only external Delta calls."""
import io
import json
from contextlib import redirect_stdout
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch

from helpers import REPO
from honey import delta


class DeltaHandoff(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="honey-handoff-")
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.repo = self.root / "repo"
        self.repo.mkdir()
        subprocess.run(["git", "init", "-q", str(self.repo)], check=True)
        self.code = self.repo / "decision.txt"
        self.code.write_text("Cache lifetime is five minutes.\n")
        subprocess.run(["git", "-C", str(self.repo), "add", "."], check=True)
        subprocess.run(["git", "-C", str(self.repo), "-c", "user.name=QA", "-c", "user.email=qa@example.invalid",
                        "commit", "-qm", "Synthetic baseline"], check=True)
        self.handoff = self.root / "handoff.md"
        self.body = "# Handoff\n## Goal\nFix cache expiry.\n## Decisions\nFive minutes.\n## Next steps\nVerify eviction.\n"
        self.handoff.write_text(self.body)
        self.evidence = self.root / "test-result.txt"
        self.evidence.write_text("Observed test result for this synthetic checkout.\n")

    def external(self, *args):
        if "show" in args:
            value = [{"id": "thread_handoff123", "messages": [
                {"number": 1, "role": "assistant", "buffer": "Five minutes.", "tool_calls": []}]}]
        else:
            value = {"operation": "status", "thread_id": "thread_handoff123", "url": None,
                     "visibility": None, "upload": {"state": "queued"}, "access": {"state": "local_only"}}
        return subprocess.CompletedProcess(args, 0, json.dumps(value), "")

    def command(self, *args, missing=False):
        output = io.StringIO()
        effect = delta.DeltaError("not_installed", "Delta is unavailable.") if missing else self.external
        with patch("honey.delta._invoke", side_effect=effect), redirect_stdout(output):
            code = delta.main(list(args))
        self.assertEqual(code, 0, output.getvalue())
        return json.loads(output.getvalue())

    def attach(self):
        return self.command("attach", str(self.handoff), "thread_handoff123", "--project", str(self.repo),
                            "--source", "qa", "--external-id", "session-1", "--messages", "1-1",
                            "--evidence", str(self.evidence))

    def test_attach_preserves_summary_and_restore_checks_actual_git_and_evidence(self):
        self.attach()
        self.assertTrue(self.handoff.read_text().startswith(self.body))
        restored = self.command("restore", str(self.handoff), "--project", str(self.repo))
        self.assertIn("Verify eviction.", restored["local_handoff"])
        self.assertTrue(restored["git"]["head_matches"])
        self.assertTrue(restored["git"]["worktree_matches"])
        self.assertEqual(restored["evidence"][0]["status"], "unchanged")
        self.assertTrue(restored["history"]["available"])
        self.assertEqual(restored["history"]["cloud"]["state"], "queued")
        self.code.write_text("A later edit changed expiry.\n")
        self.evidence.write_text("A different run.\n")
        drift = self.command("restore", str(self.handoff), "--project", str(self.repo))
        self.assertFalse(drift["git"]["worktree_matches"])
        self.assertEqual(drift["evidence"][0]["status"], "changed")

    def test_restore_without_delta_preserves_actionable_local_handoff(self):
        self.attach()
        restored = self.command("restore", str(self.handoff), "--project", str(self.repo), missing=True)
        self.assertIn("Verify eviction.", restored["local_handoff"])
        self.assertFalse(restored["history"]["available"])
        self.assertEqual(restored["history"]["error"], "not_installed")

    def test_invalid_metadata_is_a_controlled_handoff_error(self):
        for old, new in [('"reference": "thread_handoff123"', '"reference": null'),
                         ('"messages": "1-1"', '"messages": "0-1"'),
                         ('"reference": "thread_handoff123"', '"reference": "https://evil.invalid/x"')]:
            self.handoff.write_text(self.body)
            self.attach()
            self.handoff.write_text(self.handoff.read_text().replace(old, new))
            output = io.StringIO()
            with redirect_stdout(output):
                result = delta.main(["restore", str(self.handoff), "--project", str(self.repo)])
            self.assertEqual(result, 1)
            self.assertEqual(json.loads(output.getvalue())["error"], "invalid_handoff")

    def test_staging_changed_content_is_detected_even_when_file_bytes_stay_the_same(self):
        self.code.write_text("Changed before saving the handoff.\n")
        self.attach()
        subprocess.run(["git", "-C", str(self.repo), "add", "decision.txt"], check=True)
        restored = self.command("restore", str(self.handoff), "--project", str(self.repo))
        self.assertFalse(restored["git"]["worktree_matches"])


if __name__ == "__main__":
    unittest.main()
