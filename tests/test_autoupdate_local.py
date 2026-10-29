"""Exercise a cached install whose marketplace points at a local Git checkout."""
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from honey import autoupdate, dispatch, install, paths  # noqa: E402
from honey.rsi import store  # noqa: E402

GIT = ["git", "-c", "user.name=Test", "-c", "user.email=test@example.com",
       "-c", "commit.gpgsign=false", "-c", "tag.gpgsign=false"]


class LocalMarketplaceUpdate(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.home = self.root / "honey-home"
        self.home.mkdir()
        self.origin = self.root / "origin"
        self.origin.mkdir()
        self.git(self.origin, "init", "-q", "-b", "main")
        (self.origin / ".codex-plugin").mkdir()
        (self.origin / "honey").mkdir()
        (self.origin / ".codex-plugin" / "plugin.json").write_text('{"name":"honey","version":"1.0.0"}')
        (self.origin / "honey" / "__init__.py").write_text('__version__ = "1.0.0"\n')
        self.git(self.origin, "add", ".codex-plugin/plugin.json", "honey/__init__.py")
        self.git(self.origin, "commit", "-qm", "first release")
        self.git(self.origin, "tag", "v1.0.0")
        self.checkout = self.root / "source checkout"
        subprocess.run([*GIT, "clone", "-q", str(self.origin), str(self.checkout)], check=True)
        self.old_head = self.git(self.checkout, "rev-parse", "HEAD")
        self.cache = self.root / "codex" / "plugins" / "cache" / "honey-stack" / "honey" / "1.0.0"
        self.cache.mkdir(parents=True)
        (self.root / "codex" / "config.toml").write_text('[marketplaces.honey-stack]\nsource_type = "local"\n')
        self.codex = self.root / "codex-cli"
        self.codex.write_text('''#!/usr/bin/env python3
import json, os, pathlib, sys
root = pathlib.Path(os.environ["TEST_UPDATE_ROOT"])
args = sys.argv[1:]
if args == ["plugin", "marketplace", "list"]:
    print("MARKETPLACE ROOT\\nhoney-stack " + str(root / "source checkout"))
elif args == ["plugin", "add", "honey@honey-stack"]:
    if (root / "fail-refresh").exists():
        sys.exit(1)
    source = root / "source checkout"
    version = json.loads((source / ".codex-plugin" / "plugin.json").read_text())["version"]
    cache = root / "codex" / "plugins" / "cache" / "honey-stack" / "honey" / version
    cache.mkdir(parents=True, exist_ok=True)
    (cache / "installed-version").write_text(version)
else:
    sys.exit(2)
''')
        self.codex.chmod(0o755)
        self.env = patch.dict(os.environ, {"HONEY_HOME": str(self.home), "TEST_UPDATE_ROOT": str(self.root),
                                           "CODEX_HOME": str(self.root / "codex"),
                                           "CLAUDE_CONFIG_DIR": str(self.root / "claude")}, clear=False)
        self.env.start()
        self.addCleanup(self.env.stop)
        os.environ.pop("HONEY_NO_AUTOUPDATE", None)
        self.git_env = patch.object(autoupdate, "GIT_ENV", dict(os.environ, GIT_TERMINAL_PROMPT="0"))
        self.git_env.start()
        self.addCleanup(self.git_env.stop)
        self.repo = patch.object(paths, "REPO", str(self.cache))
        self.repo.start()
        self.addCleanup(self.repo.stop)
        self.cli = patch.object(install, "_cli", side_effect=lambda agent: str(self.codex) if agent == "codex" else None)
        self.cli.start()
        self.addCleanup(self.cli.stop)
        self.override = patch.object(autoupdate, "REPO_OVERRIDE", str(self.cache))
        self.override.start()
        self.addCleanup(self.override.stop)
        store.write_json(paths.path("synced.json"), {"source_repo": str(self.checkout), "head": self.old_head})

    def git(self, cwd, *args):
        return subprocess.run([*GIT, "-C", str(cwd), *args], check=True, capture_output=True, text=True).stdout.strip()

    def release(self):
        (self.origin / ".codex-plugin" / "plugin.json").write_text('{"name":"honey","version":"1.1.0"}')
        (self.origin / "honey" / "__init__.py").write_text('__version__ = "1.1.0"\n')
        self.git(self.origin, "add", ".codex-plugin/plugin.json", "honey/__init__.py")
        self.git(self.origin, "commit", "-qm", "second release")
        self.git(self.origin, "tag", "v1.1.0")
        return self.git(self.origin, "rev-parse", "HEAD")

    def test_release_updates_checkout_and_installed_cache(self):
        new_head = self.release()
        result = autoupdate.run()
        self.assertEqual(result.get("status"), "updated", result)
        self.assertEqual(self.git(self.checkout, "rev-parse", "HEAD"), new_head)
        self.assertEqual((self.cache.parent / "1.1.0" / "installed-version").read_text(), "1.1.0")
        self.assertEqual(store.read_json(paths.path("synced.json"))["head"], new_head)
        self.assertIn("1.0.0 → 1.1.0", autoupdate.notice())

    def test_feature_branch_is_not_reported_ready_when_release_is_current(self):
        self.git(self.checkout, 'switch', '-c', 'feature/local-work')
        result = autoupdate.run()
        self.assertEqual(result['status'], 'skipped')
        self.assertIn('not on main', result['reason'])

    def test_local_main_commits_are_not_reported_ready(self):
        (self.checkout / 'local.txt').write_text('local work')
        self.git(self.checkout, 'add', 'local.txt')
        self.git(self.checkout, 'commit', '-qm', 'local work')
        result = autoupdate.run()
        self.assertEqual(result['status'], 'skipped')
        self.assertIn('own commits', result['reason'])

    def test_failed_refresh_is_retried_without_a_false_success(self):
        new_head = self.release()
        (self.root / "fail-refresh").touch()
        result = autoupdate.run()
        self.assertEqual(result.get("status"), "skipped", result)
        self.assertEqual(self.git(self.checkout, "rev-parse", "HEAD"), new_head)
        self.assertEqual(autoupdate.notice(), "")
        self.assertEqual(store.read_json(paths.path("synced.json"))["head"], self.old_head)
        self.assertGreater(store.read_json(paths.path("state", "autoupdate.json"))["checked"], 0)
        (self.root / "fail-refresh").unlink()
        state = store.read_json(paths.path("state", "autoupdate.json"))
        state["checked"] = 0
        store.write_json(paths.path("state", "autoupdate.json"), state)
        result = autoupdate.run()
        self.assertEqual(result.get("status"), "updated", result)
        self.assertEqual((self.cache.parent / "1.1.0" / "installed-version").read_text(), "1.1.0")
        self.assertEqual(store.read_json(paths.path("synced.json"))["head"], new_head)

    def test_pending_refresh_does_not_install_later_local_edits(self):
        self.release()
        (self.root / "fail-refresh").touch()
        self.assertEqual(autoupdate.run().get("status"), "skipped")
        (self.root / "fail-refresh").unlink()
        (self.checkout / "honey" / "__init__.py").write_text("# local edit\n")
        state = store.read_json(paths.path("state", "autoupdate.json"))
        state["checked"] = 0
        store.write_json(paths.path("state", "autoupdate.json"), state)
        result = autoupdate.run()
        self.assertEqual(result.get("status"), "skipped", result)
        self.assertIn("local changes", result.get("reason", ""))
        self.assertFalse((self.cache.parent / "1.1.0").exists())
        self.assertIn("pending_refresh", store.read_json(paths.path("state", "autoupdate.json")))

    def test_local_marketplace_works_without_a_previous_sync(self):
        Path(paths.path("synced.json")).unlink()
        new_head = self.release()
        result = autoupdate.run()
        self.assertEqual(result.get("status"), "updated", result)
        self.assertEqual(self.git(self.checkout, "rev-parse", "HEAD"), new_head)
        self.assertEqual(store.read_json(paths.path("synced.json"))["head"], new_head)

    def test_session_start_triggers_update_and_next_session_sees_notice(self):
        self.release()
        jobs = []

        def spawn(args):
            jobs.append(args)
            if args == ["autoupdate"]:
                self.assertEqual(autoupdate.run().get("status"), "updated")

        with patch.object(dispatch.observe, "spawn", side_effect=spawn):
            first = dispatch.Ctx("codex", {"session_id": "first", "source": "startup", "cwd": str(self.root)})
            dispatch.session_start(first)
            self.assertIn(["autoupdate"], jobs)
            second = dispatch.Ctx("codex", {"session_id": "second", "source": "startup", "cwd": str(self.root)})
            message = dispatch.session_start(second)
        self.assertIn("auto-updated 1.0.0 → 1.1.0", json.dumps(message, ensure_ascii=False))
        self.assertEqual(jobs.count(["autoupdate"]), 1)

    def test_dirty_checkout_is_not_updated_or_refreshed(self):
        self.release()
        (self.checkout / "honey" / "__init__.py").write_text("# local edit\n")
        result = autoupdate.run()
        self.assertEqual(result.get("status"), "skipped", result)
        self.assertIn("local changes", result.get("reason", ""))
        self.assertEqual(self.git(self.checkout, "rev-parse", "HEAD"), self.old_head)
        self.assertFalse((self.cache.parent / "1.1.0").exists())

    def test_failed_remote_plugin_refresh_does_not_report_current(self):
        (self.root / "codex" / "config.toml").write_text('[marketplaces.honey-stack]\nsource_type = "git"\n')
        # A Claude executable alone must not cause an attempt to install its plugin.
        with patch.object(install, "_cli", return_value=str(self.codex)):
            result = autoupdate.run()
        self.assertEqual(result.get("status"), "skipped", result)
        self.assertIn("refresh failed", result.get("reason", ""))
        self.assertNotIn("claude", result.get("reason", ""))

    def test_disabled_codex_plugin_is_not_reenabled(self):
        config = self.root / "codex" / "config.toml"
        config.write_text('[marketplaces.honey-stack]\nsource_type = "local"\n'
                          '[plugins."honey@honey-stack"]\nenabled = false\n')
        self.release()
        result = autoupdate.run()
        self.assertEqual(result.get("status"), "skipped", result)
        self.assertEqual(self.git(self.checkout, "rev-parse", "HEAD"), self.old_head)
        self.assertFalse((self.cache.parent / "1.1.0").exists())

    def test_different_local_marketplaces_do_not_update_either_checkout(self):
        other = self.root / "other-checkout"
        subprocess.run([*GIT, "clone", "-q", str(self.origin), str(other)], check=True)
        claude = self.root / "claude"
        (claude / "plugins").mkdir(parents=True)
        (claude / "settings.json").write_text(json.dumps({"enabledPlugins": {"honey@honey-stack": True}}))
        (claude / "plugins" / "known_marketplaces.json").write_text(json.dumps(
            {"honey-stack": {"source": {"source": "directory", "path": str(other)}}}))
        self.release()
        with patch.object(install, "_cli", return_value=str(self.codex)):
            result = autoupdate.run()
        self.assertEqual(result.get("status"), "skipped", result)
        self.assertIn("different local checkouts", result.get("reason", ""))
        self.assertEqual(self.git(self.checkout, "rev-parse", "HEAD"), self.old_head)
        self.assertEqual(self.git(other, "rev-parse", "HEAD"), self.old_head)


if __name__ == "__main__":
    unittest.main()
