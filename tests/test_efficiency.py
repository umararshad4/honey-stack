"""Bounded observations measure repetition without pretending it is wasted work."""
import os
import tempfile
import types
import unittest
from unittest.mock import patch

from helpers import REPO
from honey.rsi import coach, curate, observe
from honey import metrics


class Efficiency(unittest.TestCase):
    def event(self, call_id="a", **kwargs):
        return dict(tool="exec_command", kind="shell", command="cat README.md", path=None,
                    call_id=call_id, cwd="/project", completed=True, exit_code=0, duration_ms=200, **kwargs)

    def test_tool_results_record_completed_calls_once(self):
        with tempfile.TemporaryDirectory() as home, patch.dict(os.environ, HONEY_HOME=home):
            ctx = types.SimpleNamespace(state={"task": {"id": "t1", "mutation": 0}},
                                        agent="codex", sid="metrics", key="codex-metrics")
            payload = {"tool_name": "Bash", "tool_use_id": "call-1", "tool_input": {"command": "cat README.md"},
                       "tool_response": {"exit_code": 0, "wall_time_seconds": 0.2}}
            observe.tool_used(ctx, payload)
            observe.tool_used(ctx, payload)
            self.assertEqual(ctx.state.get("metrics", {}).get("session", {}).get("completed_calls"), 1)

    def test_repetition_is_invalidated_after_mutation_and_task_change(self):
        state = {"task": {"id": "t1", "mutation": 0}}
        for call in ("a", "b"):
            metrics.record(state, self.event(call))
        self.assertEqual(metrics.report(state)["task"]["repeated_reads"], 1)
        state["task"]["mutation"] += 1
        metrics.record(state, self.event("c"))
        self.assertEqual(metrics.report(state)["task"]["repeated_reads"], 1)
        state["task"] = {"id": "t2", "mutation": 0}
        metrics.record(state, self.event("d"))
        self.assertEqual(metrics.report(state)["task"]["repeated_reads"], 0)
        self.assertEqual(metrics.report(state)["session"]["tool_calls"], 4)

    def test_unknown_and_yielded_results_are_not_successes(self):
        state = {}
        event = self.event()
        event.update(completed=False, exit_code=None)
        metrics.record(state, event)
        metrics.record(state, event)
        self.assertEqual(metrics.report(state)["session"]["completed_calls"], 0)
        metrics.record(state, self.event())
        result = metrics.report(state)["session"]
        self.assertEqual((result["tool_calls"], result["completed_calls"], result["duration_samples"]), (1, 1, 1))

    def test_late_completion_does_not_count_in_the_next_task(self):
        state = {"task": {"id": "t1"}}
        pending = self.event()
        pending.update(completed=False, exit_code=None)
        metrics.record(state, pending)
        state["task"] = {"id": "t2"}
        metrics.record(state, self.event())
        self.assertEqual(metrics.report(state)["task"]["completed_calls"], 0)
        self.assertEqual(metrics.report(state)["session"]["completed_calls"], 1)

    def test_pretool_origin_prevents_terminal_only_result_entering_new_task(self):
        state = {'task': {'id': 'new'}}
        event = self.event(task_id='old')
        metrics.record(state, event)
        self.assertEqual(metrics.report(state)['task']['tool_calls'], 0)
        self.assertEqual(metrics.report(state)['session']['completed_calls'], 1)

    def test_package_run_tests_are_counted(self):
        state = {}
        for call in ('first', 'second'):
            event = self.event(call)
            event['command'] = 'npm run test'
            metrics.record(state, event)
        self.assertEqual(metrics.report(state)['session']['check_calls'], 2)
        self.assertEqual(metrics.report(state)['session']['repeated_checks'], 1)

    def test_new_task_report_is_empty_before_its_first_tool(self):
        state = {"task": {"id": "t1"}}
        metrics.record(state, self.event())
        state["task"] = {"id": "t2"}
        self.assertEqual(metrics.report(state)["task_id"], "t2")
        self.assertEqual(metrics.report(state)["task"]["completed_calls"], 0)

    def test_bounds_and_no_raw_commands_in_state(self):
        state = {"task": {"id": "t1"}}
        for number in range(200):
            event = self.event(str(number))
            event["command"] = "cat secret-file-" + str(number)
            metrics.record(state, event)
        self.assertLessEqual(len(state["metrics"]["seen"]), metrics.MAX_SEEN)
        self.assertLessEqual(len(state["metrics"]["fingerprints"]["read"]), metrics.MAX_FINGERPRINTS)
        self.assertNotIn("secret-file", str(state))

    def test_failure_and_check_denominators_are_explicit(self):
        state = {}
        event = self.event()
        event.update(command="python3 tests/run.py", exit_code=1)
        metrics.record(state, event)
        event["call_id"] = "b"
        event.update(exit_code=0, duration_ms=None)
        metrics.record(state, event)
        result = metrics.report(state)["session"]
        self.assertEqual((result["failed_calls"], result["check_calls"], result["repeated_checks"]), (1, 2, 1))
        self.assertEqual((result["duration_ms"], result["duration_samples"]), (200, 1))

    def test_weekly_report_has_denominators_and_no_causal_speed_claim(self):
        with tempfile.TemporaryDirectory() as home, patch.dict(os.environ, HONEY_HOME=home):
            state = {}
            rows = []
            for call in ("a", "b"):
                rows.append({"e": "tool", "metrics": metrics.record(state, self.event(call))})
            pending = self.event("c")
            pending.update(completed=False, exit_code=None)
            rows.append({"e": "tool", "metrics": metrics.record(state, pending)})
            curate.observe_only("codex-efficiency", rows)
            report = coach.report()
            self.assertIn("completed tool calls: 2/3", report)
            self.assertIn("unknown results: 1/3", report)
            self.assertIn("repeated reads: 1/2", report)
            self.assertIn("reported duration: 400 ms across 2", report)
            self.assertIn("not a speedup measurement", report)


if __name__ == "__main__":
    unittest.main()
