"""Opting out of dollar caps preserves cadence, accounting, and evaluation."""
import contextlib
import io
import json
import os
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch as mock

from helpers import REPO
from honey import paths
from honey.rsi import cli, patch, reflect, store, text


class BudgetControl(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.env = mock.dict(os.environ, HONEY_HOME=self.tmp.name)
        self.env.start()
        self.addCleanup(self.env.stop)

    def disable_caps(self):
        store.write_json(paths.path('config.json'), {'budgets': {'enabled': False}})

    def test_explicit_opt_out_ignores_dollars_but_preserves_rate_limit(self):
        self.disable_caps()
        store.append_jsonl(paths.path('costs.jsonl'), {'ts': text.now(), 'usd': 100, 'job': 'eval'})
        self.assertIsNone(reflect.budget_block('claude'))
        self.assertIsNone(patch._budget_block())
        for _ in range(8):
            store.append_jsonl(paths.path('costs.jsonl'), {'ts': text.now(), 'usd': 0, 'job': 'reflect'})
        self.assertEqual(reflect.budget_block('claude'), 'daily reflection cap')

    def test_dollar_caps_remain_enabled_by_default(self):
        store.append_jsonl(paths.path('costs.jsonl'), {'ts': text.now(), 'usd': 100})
        self.assertEqual(reflect.budget_block('claude'), 'weekly budget')
        self.assertIn('weekly_usd', patch._budget_block())

    def test_uncapped_draft_omits_provider_limit(self):
        self.disable_caps()
        with mock.dict(os.environ), mock.object(reflect, 'engine', return_value=('claude', '/test/claude')), \
                mock.object(reflect.subprocess, 'run', return_value=subprocess.CompletedProcess(
                    [], 0, json.dumps({'structured_output': {}, 'total_cost_usd': 0.42}), '')) as run:
            os.environ.pop('HONEY_FAKE_LLM', None)
            self.assertEqual(reflect.call_llm('system', 'user', {}, 0.15)[1], 0.42)
        self.assertNotIn('--max-budget-usd', run.call_args.args[0])

    def test_uncapped_evaluation_records_actual_usage(self):
        self.disable_caps()
        output = str(Path(self.tmp.name, 'evaluation.json'))
        def execute(command, **kwargs):
            self.assertNotIn('--max-cost-usd', command)
            store.write_json(output, {'costUsd': 0.67, 'cases': [
                {'name': 'case', 'arms': {'with': [{'score': 1}]}}]})
            return subprocess.CompletedProcess(command, 0, '', '')
        with mock.object(patch.subprocess, 'run', side_effect=execute):
            self.assertEqual(patch.run_eval(self.tmp.name, '*', output), {'case': 1})
        cost = store.read_jsonl(paths.path('costs.jsonl'))[-1]
        self.assertEqual(cost['usd'], 0.67)
        self.assertFalse(cost['estimated'])

    def test_uncapped_failed_call_records_unknown_cost_not_a_false_cap(self):
        self.disable_caps()
        with mock.object(patch.subprocess, 'run', side_effect=subprocess.TimeoutExpired('claude', 900)):
            with self.assertRaises(subprocess.TimeoutExpired):
                patch.run_eval(self.tmp.name, '*', str(Path(self.tmp.name, 'out.json')))
        cost = store.read_jsonl(paths.path('costs.jsonl'))[-1]
        self.assertIsNone(cost['usd'])
        self.assertFalse(cost['ok'])

    def test_status_reports_explicit_uncapped_mode(self):
        self.disable_caps()
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            cli.status(True)
        self.assertFalse(json.loads(out.getvalue())['budget_caps_enabled'])

    def test_unknown_usage_is_not_presented_as_zero_total(self):
        self.disable_caps()
        store.append_jsonl(paths.path('costs.jsonl'), {'ts': text.now(), 'job': 'eval', 'usd': None})
        store.append_jsonl(paths.path('costs.jsonl'), {'ts': text.now(), 'job': 'eval', 'usd': 0.25})
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            cli.status(True)
        status = json.loads(out.getvalue())
        self.assertEqual(status['usd_this_month'], 0.25)
        self.assertEqual(status['unknown_cost_calls_this_month'], 1)
        self.assertFalse(status['monthly_cost_complete'])
        for args in (['status'], ['costs']):
            out = io.StringIO()
            with contextlib.redirect_stdout(out):
                cli.main(args)
            self.assertIn('unknown', out.getvalue())


if __name__ == '__main__':
    unittest.main()
