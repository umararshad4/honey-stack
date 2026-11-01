"""A retried QA run must finish cleanup without archiving attached user work."""
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from helpers import REPO
import qa_delta_compare as qa


class FixtureCleanup(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="honey-qa-cleanup-")
        self.addCleanup(self.temp.cleanup)
        self.output = Path(self.temp.name)
        self.fixture = {"live": True, "native_status": {}, "archived": False,
                        "thread": "thread_qa", "source": "honey-qa", "external_id": "qa-session"}
        (self.output / "fixture.json").write_text(json.dumps(self.fixture))

    def test_reusing_a_fixture_retries_its_failed_archive(self):
        status = {"worktrees": {"status": "available", "items": []}, "visibility": "private"}
        with patch.object(qa, "native", side_effect=[json.dumps(status), "{}"]) as native:
            result = qa.prepare_fixture(self.output, True)
        self.assertTrue(result["archived"])
        self.assertEqual(native.call_args_list[-1].args, ("thread", "archive", "thread_qa"))
        self.assertTrue(json.loads((self.output / "fixture.json").read_text())["archived"])

    def test_cleanup_refuses_a_fixture_that_now_has_attached_work(self):
        status = {"worktrees": {"status": "available", "items": [{"reference": "user-work"}]}, "visibility": "private"}
        with patch.object(qa, "native", return_value=json.dumps(status)) as native:
            with self.assertRaises(ValueError):
                qa.prepare_fixture(self.output, True)
        self.assertEqual(native.call_count, 1)


if __name__ == "__main__":
    unittest.main()
