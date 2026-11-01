"""Delta stays optional and explicit; exercise its public Honey CLI boundary."""
import io
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import textwrap
import unittest
from contextlib import redirect_stdout
from unittest.mock import patch

from helpers import REPO
from honey import delta


class DeltaCommands(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="honey-delta-test-")
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.calls = self.root / "calls.jsonl"
        self.responses = self.root / "responses.json"
        binary = self.root / "delta"
        binary.write_text(f"#!{sys.executable}\n" + textwrap.dedent("""\
            import json, os, pathlib, sys
            calls = pathlib.Path(os.environ['DELTA_TEST_CALLS'])
            count = len(calls.read_text().splitlines()) if calls.exists() else 0
            with calls.open('a') as stream:
                stream.write(json.dumps(sys.argv[1:]) + '\\n')
            responses = json.loads(pathlib.Path(os.environ['DELTA_TEST_RESPONSES']).read_text())
            if count >= len(responses):
                print('Unexpected Delta invocation', file=sys.stderr)
                sys.exit(90)
            response = responses[count]
            print(response.get('stdout', ''), end='')
            print(response.get('stderr', ''), end='', file=sys.stderr)
            sys.exit(response.get('code', 0))
            """))
        binary.chmod(0o700)

    def run_honey(self, *args, responses=(), missing=False):
        self.responses.write_text(json.dumps(responses))
        self.calls.unlink(missing_ok=True)
        empty = self.root / "empty"
        empty.mkdir(exist_ok=True)
        env = dict(os.environ, PATH=str(empty) if missing else str(self.root) + os.pathsep + os.environ.get("PATH", ""),
                   DELTA_TEST_CALLS=str(self.calls), DELTA_TEST_RESPONSES=str(self.responses))
        result = subprocess.run([sys.executable, str(Path(REPO) / "bin/honey"), "delta", *args],
                                capture_output=True, text=True, env=env, timeout=10)
        calls = [json.loads(line) for line in self.calls.read_text().splitlines()] if self.calls.exists() else []
        return result, calls

    def test_status_reports_authenticated_delta(self):
        result, calls = self.run_honey("status", responses=[
            {"stdout": "delta 0.23.0\n"},
            {"stdout": json.dumps({"status": "signed_in", "account": {"login": "qa-user", "account_id": "private-id"}})},
        ])
        self.assertEqual(result.returncode, 0, result.stderr)
        payload = json.loads(result.stdout)
        self.assertTrue(payload["ready"])
        self.assertEqual(payload["version"], "0.23.0")
        self.assertEqual(payload["login"], "qa-user")
        self.assertEqual(calls, [["--version"], ["--json", "auth", "status"]])

    def test_status_keeps_delta_optional(self):
        result, calls = self.run_honey("status", missing=True)
        self.assertEqual(result.returncode, 0)
        self.assertEqual(json.loads(result.stdout)["reason"], "not_installed")
        self.assertFalse(json.loads(result.stdout)["ready"])
        self.assertEqual(calls, [])

    def test_readiness_separates_local_history_capture_and_cloud_upload(self):
        status = {"operation": "status", "thread_id": "opaque_history_123", "url": None,
                  "visibility": None, "upload": {"state": "queued", "error": None},
                  "access": {"state": "local_only"}, "worktrees": {"status": "available", "items": []}}
        native = [{"id": "opaque_history_123", "messages": [
            {"number": 1, "role": "user", "buffer": "Historical decision", "tool_calls": []}]}]
        result, _ = self.run_honey("status", "--project", str(self.root), "--thread", "opaque_history_123",
            "--source", "test", "--external-id", "session-1", responses=[
                {"stdout": "delta 0.23.0\n"},
                {"stdout": '{"status":"signed_in","account":{"login":"qa"}}'},
                {"stdout": json.dumps(status)}, {"stdout": json.dumps(native)}])
        self.assertEqual(result.returncode, 0, result.stderr)
        payload = json.loads(result.stdout)
        self.assertTrue(payload["ready"])
        self.assertTrue(payload["readiness"]["history_readable"])
        self.assertFalse(payload["readiness"]["cloud_uploaded"])
        self.assertFalse(payload["readiness"]["capture_configured"])
        self.assertEqual(payload["cloud"]["state"], "queued")
        self.assertEqual(payload["capture"]["mode"], "manual")

    def test_failed_cloud_status_does_not_invent_failed_local_history(self):
        native = [{"id": "thread_history123", "messages": [
            {"number": 1, "role": "user", "buffer": "Local history", "tool_calls": []}]}]
        result, _ = self.run_honey("status", "--thread", "thread_history123", "--source", "qa",
            "--external-id", "session1", responses=[{"stdout": "delta 0.23.0\n"},
            {"stdout": '{"status":"signed_in","account":{"login":"qa"}}'},
            {"stdout": '{"error":{"code":"not_shared","retryable":false}}', "code": 1},
            {"stdout": json.dumps(native)}])
        self.assertEqual(result.returncode, 0, result.stderr)
        payload = json.loads(result.stdout)
        self.assertTrue(payload["readiness"]["history_readable"])
        self.assertIsNone(payload["readiness"]["cloud_uploaded"])
        self.assertEqual(payload["cloud_error"]["error"], "not_shared")

    def test_signed_out_is_not_ready_even_when_delta_exits_one(self):
        result, _ = self.run_honey("status", responses=[
            {"stdout": "delta 0.23.0\n"},
            {"stdout": '{"status":"signed_out"}', "code": 1},
        ])
        self.assertEqual(result.returncode, 0)
        self.assertEqual(json.loads(result.stdout)["reason"], "signed_out")
        self.assertFalse(json.loads(result.stdout)["ready"])

    def test_old_cli_is_rejected_before_authentication(self):
        result, calls = self.run_honey("status", responses=[{"stdout": "delta 0.21.0\n"}])
        self.assertEqual(result.returncode, 0)
        self.assertEqual(json.loads(result.stdout)["reason"], "unsupported_version")
        self.assertEqual(calls, [["--version"]])

    def test_search_is_bounded_and_keeps_edited_path_literal(self):
        threads = [{"id": "thread_test123", "title": "Sign-in retry decision"}]
        result, calls = self.run_honey("search", "sign-in", "--limit", "3", "--edited-path", "src/**",
                                      responses=[{"stdout": json.dumps(threads)}])
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(json.loads(result.stdout), {"source": "delta", "threads": threads})
        self.assertEqual(calls, [["--json", "thread", "search", "--scope", "messages", "--limit", "3",
                                  "--edited-path=src/**", "--", "sign-in"]])

    def test_read_normalizes_a_link_and_preserves_the_requested_window(self):
        transcript = [{"number": 2, "role": "user", "buffer": "Synthetic request", "tool_calls": []},
                      {"number": 3, "role": "assistant", "buffer": "Synthetic response", "tool_calls": []}]
        native = [{"id": "opaque_delta_thread_0123456789", "messages": transcript}]
        result, calls = self.run_honey("read", "https://delta.dev/join/thread_test123", "--messages", "2-3",
                                      responses=[{"stdout": json.dumps(native)}])
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(json.loads(result.stdout), {"source": "delta", "url": "https://delta.dev/join/thread_test123",
            "thread": "opaque_delta_thread_0123456789", "messages": "2-3", "transcript": transcript})
        self.assertEqual(calls, [["--json", "thread", "show", "--format", "messages", "--messages", "2-3",
                                  "--", "https://delta.dev/join/thread_test123"]])

    def test_read_defaults_to_one_message_so_short_threads_are_readable(self):
        native = [{"id": "thread_test123", "messages": [
            {"number": 1, "role": "user", "buffer": "Synthetic request", "tool_calls": []}]}]
        result, calls = self.run_honey("read", "thread_test123", responses=[{"stdout": json.dumps(native)}])
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(json.loads(result.stdout)["messages"], "1-1")
        self.assertIn("1-1", calls[0])

    def test_opaque_local_id_is_readable_but_does_not_invent_a_share_url(self):
        thread = "opaque_delta_thread_0123456789"
        native = [{"id": thread, "messages": [{"number": 1, "role": "user", "buffer": "Local only", "tool_calls": []}]}]
        result, calls = self.run_honey("read", thread, responses=[{"stdout": json.dumps(native)}])
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(json.loads(result.stdout)["thread"], thread)
        self.assertIsNone(json.loads(result.stdout)["url"])
        self.assertEqual(calls[0][-1], thread)

    def test_read_rejects_malformed_or_out_of_window_transcripts(self):
        message = {"number": 1, "role": "user", "buffer": "Synthetic request", "tool_calls": []}
        bad_rows = [[], {}, {"message": "missing history"}, [None], [message],
                    [{"id": "thread_test123", "messages": [None]}],
                    [{"id": "thread_test123", "messages": [message, message]}],
                    [{"id": "thread_test123", "messages": [{**message, "number": 2}]}],
                    [{"id": "thread_test123", "messages": [{**message, "buffer": None}]}]]
        for response in bad_rows:
            with self.subTest(response=response):
                result, _ = self.run_honey("read", "thread_test123", responses=[{"stdout": json.dumps(response)}])
                self.assertEqual(result.returncode, 1)
                self.assertEqual(json.loads(result.stdout)["error"], "invalid_response")

    def test_unsafe_references_are_rejected_without_invoking_delta(self):
        for reference in ("--help", "thread_a/../b", "https://evil.test/join/thread_a",
                          "https://delta.dev.evil.test/join/thread_a", "http://delta.dev/join/thread_a",
                          "https://user@delta.dev/join/thread_a", "https://delta.dev:8443/join/thread_a",
                          "https://delta.dev/join/thread_a?token=secret", "thread_a\nthread_b"):
            with self.subTest(reference=reference):
                result, calls = self.run_honey("read", "--", reference)
                self.assertEqual(result.returncode, 2)
                self.assertEqual(calls, [])

    def test_bad_windows_are_rejected_before_invoking_delta(self):
        for window in ("0-1", "3-2", "1-21", "1", "1-2;touch x", "1-999999999999999999999999999999999"):
            with self.subTest(window=window):
                result, calls = self.run_honey("read", "thread_test123", "--messages", window)
                self.assertEqual(result.returncode, 2)
                self.assertEqual(calls, [])

    def test_search_passes_shell_and_option_like_text_as_literal_keywords(self):
        marker = self.root / "should-not-exist"
        keyword = f"$(touch {marker}); echo literal"
        result, calls = self.run_honey("search", "--", "--delete", keyword, responses=[{"stdout": "[]"}])
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(calls[0][-3:], ["--", "--delete", keyword])
        self.assertFalse(marker.exists())

    def test_empty_search_is_success_but_command_failure_is_not(self):
        result, _ = self.run_honey("search", "missing", responses=[{"stdout": "[]"}])
        self.assertEqual(result.returncode, 0)
        self.assertEqual(json.loads(result.stdout)["threads"], [])
        diagnostic = "synthetic-upstream-diagnostic"
        result, _ = self.run_honey("search", "missing", responses=[{"stderr": diagnostic, "code": 1}])
        self.assertEqual(result.returncode, 1)
        self.assertEqual(json.loads(result.stdout)["error"], "command_failed")
        self.assertNotIn(diagnostic, result.stdout + result.stderr)

    def test_temporary_read_failure_retries_but_access_denial_keeps_safe_diagnostics(self):
        transient = {"error": {"code": "app_unavailable", "retryable": True, "retry_after_ms": 0,
                               "message": "secret-from-provider"}}
        result, calls = self.run_honey("search", "decision", responses=[
            {"code": 1, "stdout": json.dumps(transient)}, {"stdout": "[]"}])
        self.assertEqual(result.returncode, 0, result.stdout)
        self.assertEqual(len(calls), 2)
        denied = {"error": {"code": "not_visible", "retryable": False,
                            "message": "secret-from-provider"}}
        result, calls = self.run_honey("search", "decision", responses=[
            {"code": 1, "stdout": json.dumps(denied)}])
        self.assertEqual(result.returncode, 1)
        self.assertEqual(json.loads(result.stdout)["error"], "not_visible")
        self.assertFalse(json.loads(result.stdout)["retryable"])
        self.assertEqual(len(calls), 1)
        self.assertNotIn("secret-from-provider", result.stdout + result.stderr)

    def test_invalid_json_is_an_error_without_repeating_its_contents(self):
        result, _ = self.run_honey("read", "thread_test123", responses=[{"stdout": "not-json synthetic-diagnostic"}])
        self.assertEqual(result.returncode, 1)
        self.assertEqual(json.loads(result.stdout)["error"], "invalid_response")
        self.assertNotIn("synthetic-diagnostic", result.stdout + result.stderr)

    def test_missing_delta_does_not_pretend_search_succeeded(self):
        result, calls = self.run_honey("search", "decision", missing=True)
        self.assertEqual(result.returncode, 1)
        self.assertEqual(json.loads(result.stdout)["error"], "not_installed")
        self.assertEqual(calls, [])

    def test_invalid_search_bounds_are_rejected_before_invoking_delta(self):
        for args in (("",), ("   ",), ("decision", "--limit", "0"),
                     ("decision", "--limit", "21"), ("decision", "--limit", "many")):
            with self.subTest(args=args):
                result, calls = self.run_honey("search", *args)
                self.assertEqual(result.returncode, 2)
                self.assertEqual(calls, [])

    def test_unexpected_or_oversized_search_responses_are_errors(self):
        for response in ({}, [None], [{}, {}, {}], {"error": "not found"}):
            with self.subTest(response=response):
                result, _ = self.run_honey("search", "decision", "--limit", "2",
                                           responses=[{"stdout": json.dumps(response)}])
                self.assertEqual(result.returncode, 1)
                self.assertIn("error", json.loads(result.stdout))

    def test_unknown_auth_state_and_empty_account_do_not_appear_ready(self):
        for auth in ({"status": "unknown"}, [], {"status": "signed_in", "account": {"login": ""}}):
            with self.subTest(auth=auth):
                result, _ = self.run_honey("status", responses=[
                    {"stdout": "delta 0.23.0\n"}, {"stdout": json.dumps(auth)},
                ])
                self.assertEqual(result.returncode, 1)
                self.assertEqual(json.loads(result.stdout)["error"], "invalid_response")

    def test_timeout_is_bounded_and_does_not_expose_subprocess_output(self):
        output = io.StringIO()
        with patch("honey.delta.shutil.which", return_value="/installed/delta"), \
             patch("honey.delta.subprocess.run", side_effect=subprocess.TimeoutExpired("delta", 20, output="synthetic-diagnostic")), \
             redirect_stdout(output):
            code = delta.main(["search", "decision"])
        self.assertEqual(code, 1)
        self.assertEqual(json.loads(output.getvalue())["error"], "timeout")
        self.assertNotIn("synthetic-diagnostic", output.getvalue())

    def test_mutating_delta_commands_are_not_exposed(self):
        for command in ("share", "create", "append", "delete", "query", "mount"):
            with self.subTest(command=command):
                result, calls = self.run_honey(command)
                self.assertEqual(result.returncode, 2)
                self.assertEqual(calls, [])

    def test_recall_finds_the_late_decision_and_returns_its_exact_window(self):
        texts = ["Cache lifetime: initially try 30 minutes.\n\n", "Exploring tradeoffs.\n\n",
                 "Cache lifetime final decision?\n\n", "Cache lifetime final decision is 5 minutes, approved.\n\n"]
        rows, offset = [], 0
        for number, content in enumerate(texts, 1):
            end = offset + len(content.encode())
            rows.append({"number": number, "role": "user" if number % 2 else "assistant",
                         "start_byte": offset, "end_byte": end, "created_at_utc": None})
            offset = end
        full = [{"id": "thread_history123", "name": "Cache decision", "buffer": "".join(texts),
                 "messages": rows, "summary": "stale: 30 minutes"}]
        selected = [{"id": "thread_history123", "messages": [
            {"number": 3, "role": "user", "buffer": texts[2], "tool_calls": []},
            {"number": 4, "role": "assistant", "buffer": texts[3], "tool_calls": []}]}]
        result, _ = self.run_honey("recall", "cache", "lifetime", responses=[
            {"stdout": '[{"id":"thread_history123","name":"Cache decision"}]'},
            {"stdout": json.dumps(full)}, {"stdout": json.dumps(selected)}])
        self.assertEqual(result.returncode, 0, result.stderr)
        data = json.loads(result.stdout)
        self.assertEqual(data["status"], "found")
        self.assertEqual(data["messages"], "3-4")
        self.assertEqual(data["match"]["message"], 4)
        self.assertIn("5 minutes", json.dumps(data["transcript"]))
        self.assertNotIn("30 minutes", result.stdout)

    def test_large_read_is_explicitly_truncated_to_the_output_budget(self):
        native = [{"id": "thread_history123", "messages": [
            {"number": 1, "role": "assistant", "buffer": "important " * 4000,
             "tool_calls": [{"output": "large log " * 4000}]}]}]
        result, _ = self.run_honey("read", "thread_history123", "--max-chars", "2000",
                                   responses=[{"stdout": json.dumps(native)}])
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertLessEqual(len(result.stdout.strip()), 2000)
        data = json.loads(result.stdout)
        self.assertTrue(data["truncated"])
        self.assertEqual(data["transcript"][0]["number"], 1)

    def test_stale_summary_is_withheld_and_full_transcript_is_not_forwarded(self):
        native = [{"id": "thread_history123", "name": "Cache decision", "transcript": "huge raw history" * 500,
                   "messages": [{"number": 1, "role": "user"}, {"number": 2, "role": "assistant"}],
                   "summary": "outdated decision", "summary_is_fresh": False}]
        result, _ = self.run_honey("summary", "thread_history123", responses=[{"stdout": json.dumps(native)}])
        self.assertEqual(result.returncode, 0, result.stderr)
        data = json.loads(result.stdout)
        self.assertEqual(data["summary_state"], "stale")
        self.assertIsNone(data["summary"])
        self.assertEqual(data["message_count"], 2)
        self.assertNotIn("huge raw history", result.stdout)

    def test_capture_preview_is_read_only_and_apply_preserves_other_settings(self):
        subprocess.run(["git", "init", "-q", str(self.root)], check=True)
        config = self.root / ".delta/settings.json"
        config.parent.mkdir()
        config.write_text('{"editor":{"theme":"keep-me"},"threads":{"mode":"manual"}}')
        before = config.read_bytes()
        args = ("setup", "--project", str(self.root), "--mode", "private", "--organization", "org_test123")
        preview, calls = self.run_honey(*args)
        self.assertEqual(preview.returncode, 0, preview.stderr)
        self.assertFalse(json.loads(preview.stdout)["applied"])
        self.assertEqual(config.read_bytes(), before)
        applied, calls = self.run_honey(*args, "--apply")
        self.assertEqual(applied.returncode, 0, applied.stderr)
        self.assertTrue(json.loads(applied.stdout)["applied"])
        self.assertEqual(json.loads(config.read_text())["editor"], {"theme": "keep-me"})
        self.assertEqual(json.loads(config.read_text())["threads"]["mode"], "private")
        self.assertEqual(subprocess.run(["git", "-C", str(self.root), "check-ignore", "-q", ".delta/settings.json"]).returncode, 0)
        self.assertEqual(calls, [])

    def test_capture_rejects_a_symlinked_settings_directory(self):
        subprocess.run(["git", "init", "-q", str(self.root)], check=True)
        outside = self.root / "outside"
        outside.mkdir()
        config = outside / "settings.json"
        config.write_text('{"keep":true}')
        (self.root / ".delta").symlink_to(outside, target_is_directory=True)
        result, _ = self.run_honey("setup", "--project", str(self.root), "--mode", "private",
                                  "--organization", "org_test123", "--apply")
        self.assertEqual(result.returncode, 1)
        self.assertEqual(json.loads(result.stdout)["error"], "unsafe_config")
        self.assertEqual(config.read_text(), '{"keep":true}')

    def test_malformed_native_error_code_cannot_crash_the_cli(self):
        result, _ = self.run_honey("search", "decision", responses=[
            {"stdout": '{"error":{"code":[],"retryable":false}}', "code": 1}])
        self.assertEqual(result.returncode, 1)
        self.assertEqual(json.loads(result.stdout)["error"], "command_failed")
        self.assertNotIn("Traceback", result.stderr)

    def test_recall_keeps_matching_evidence_after_a_large_diagnostic_prefix(self):
        body = "diagnostic output " * 3000 + "Final needle decision: five minutes."
        full = [{"id": "thread_history123", "buffer": body,
                 "messages": [{"number": 1, "role": "assistant", "start_byte": 0, "end_byte": len(body.encode())}]}]
        native = [{"id": "thread_history123", "messages": [
            {"number": 1, "role": "assistant", "buffer": body, "tool_calls": []}]}]
        result, _ = self.run_honey("recall", "needle", "decision", "--thread", "thread_history123",
            "--max-chars", "2000", responses=[{"stdout": json.dumps(full)}, {"stdout": json.dumps(native)}])
        self.assertEqual(result.returncode, 0, result.stderr)
        data = json.loads(result.stdout)
        self.assertEqual(data["status"], "found")
        self.assertIn("needle decision: five minutes", data["transcript"][0]["buffer"])
        self.assertLessEqual(len(result.stdout.strip()), 2000)

    def test_final_output_budget_preserves_the_reported_match_with_escaped_text(self):
        thread = "x" * 127
        texts = ["\\" * 219, "\\" * 219 + " needle", "\\" * 219]
        metadata, messages, offset = [], [], 0
        for number, body in enumerate(texts, 1):
            end = offset + len(body.encode())
            metadata.append({"number": number, "role": "assistant", "start_byte": offset, "end_byte": end})
            messages.append({"number": number, "role": "assistant", "buffer": body, "tool_calls": []})
            offset = end
        result, _ = self.run_honey("recall", "needle", "--thread", "https://delta.dev/join/" + thread,
            "--max-chars", "2000", responses=[
                {"stdout": json.dumps([{"id": thread, "buffer": "".join(texts), "messages": metadata}])},
                {"stdout": json.dumps([{"id": thread, "messages": messages}])}])
        self.assertEqual(result.returncode, 0, result.stderr)
        data = json.loads(result.stdout)
        anchor = next(row for row in data["transcript"] if row["number"] == data["match"]["message"])
        self.assertIn("needle", anchor["buffer"])
        self.assertTrue(data["match"]["complete"])
        self.assertLessEqual(len(result.stdout.strip()), 2000)


if __name__ == "__main__":
    unittest.main()
