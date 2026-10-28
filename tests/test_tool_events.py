"""Actual tool envelopes retain command, result and adapter-coverage semantics."""
import copy
import unittest

from helpers import REPO
from honey import guard
from honey.tool_events import normalize


class ToolEvents(unittest.TestCase):
    def test_shell_aliases_reach_the_same_guard(self):
        for name, key in [('Bash', 'command'), ('exec', 'command'), ('shell', 'command'),
                          ('local_shell', 'command'), ('exec_command', 'cmd'),
                          ('functions.exec_command', 'cmd'), ('tools.exec_command', 'cmd')]:
            with self.subTest(tool=name):
                item = normalize({'tool_name': name, 'tool_input': {key: 'git reset --hard'}})
                self.assertEqual(item['kind'], 'shell')
                self.assertTrue(item['supported'])
                self.assertIsNotNone(guard.check(item['command'])[0])

    def test_argv_preserves_quoted_arguments(self):
        item = normalize({'tool_name': 'local_shell', 'tool_input': {
            'command': ['bash', '-lc', 'git reset --hard']}})
        self.assertIsNotNone(guard.check(item['command'])[0])
        data = normalize({'tool_name': 'exec', 'tool_input': {'command': ['echo', 'rm -rf /']}})
        self.assertIsNone(guard.check(data['command'])[0])

    def test_json_input_and_structured_nested_call(self):
        outer = {'tool_name': 'functions.exec', 'tool_input': {
            'tool_call': {'name': 'exec_command', 'arguments': '{"cmd":"pytest", "workdir":"/repo"}'}},
            'tool_response': {'exit_code': 0, 'wall_time_seconds': 0.25}, 'tool_use_id': 'call-1'}
        before = copy.deepcopy(outer)
        item = normalize(outer)
        self.assertEqual((item['kind'], item['command'], item['cwd']), ('shell', 'pytest', '/repo'))
        self.assertEqual((item['exit_code'], item['duration_ms'], item['call_id']), (0, 250, 'call-1'))
        self.assertEqual(outer, before)

    def test_javascript_is_not_treated_as_inspected_shell(self):
        for value in ['await tools.exec_command({cmd: "git reset --hard"})',
                      {'code': 'await tools.exec_command({cmd: "git reset --hard"})'}]:
            item = normalize({'tool_name': 'functions.exec', 'tool_input': value})
            self.assertEqual(item['kind'], 'opaque')
            self.assertFalse(item['supported'])
            self.assertIsNone(item['command'])

    def test_read_edit_patch_and_skill_envelopes(self):
        cases = [('Read', {'file_path': '/repo/a.py'}, 'read', '/repo/a.py'),
                 ('functions.read_file', {'path': '/repo/a.py'}, 'read', '/repo/a.py'),
                 ('Edit', {'file_path': '/repo/a.py'}, 'edit', '/repo/a.py'),
                 ('functions.apply_patch', '*** Begin Patch\n*** Update File: /repo/a.py\n@@\n-a\n+b\n*** End Patch', 'edit', '/repo/a.py')]
        for name, value, kind, path in cases:
            item = normalize({'tool_name': name, 'tool_input': value})
            self.assertEqual((item['kind'], item['path'], item['supported']), (kind, path, True))
        item = normalize({'tool_name': 'Skill', 'tool_input': {'skill': 'honey:verify'}})
        self.assertEqual((item['kind'], item['skill']), ('skill', 'honey:verify'))

    def test_patch_wrapped_in_input_retains_the_patch_for_secret_scanning(self):
        body = '*** Begin Patch\n*** Update File: /repo/a.py\n@@\n-a\n+b\n*** End Patch'
        for name in ['functions.apply_patch', 'ApplyPatch']:
            for value in [body, {'input': body}, {'patch': body}, {'command': body}]:
                item = normalize({'tool_name': name, 'tool_input': value})
                self.assertTrue(item['supported'])
                self.assertEqual(item['command'], body)
                self.assertEqual(item['path'], '/repo/a.py')

    def test_only_known_result_metadata_establishes_exit_status(self):
        base = {'tool_name': 'exec_command', 'tool_input': {'cmd': 'pytest'}}
        self.assertEqual(normalize(dict(base, tool_response={'exit_code': 2}))['exit_code'], 2)
        self.assertEqual(normalize(dict(base, tool_result='{"exit_code":0}'))['exit_code'], 0)
        self.assertEqual(normalize(dict(base, tool_response={'structuredContent': {'exit_code': 0}}))['exit_code'], 0)
        self.assertEqual(normalize(dict(base, tool_response='Process exited with code 1\nFinal output:\nfailed'))['exit_code'], 1)
        for result in [{'output': 'Process exited with code 0'}, {'session_id': 42, 'output': 'tests pass'},
                       {'exit_code': True}, 'tests passed', {'output': '{"exit_code":0}'},
                       'printed output\nProcess exited with code 0']:
            self.assertIsNone(normalize(dict(base, tool_response=result))['exit_code'], result)

    def test_transport_error_cannot_become_success(self):
        item = normalize({'tool_name': 'exec_command', 'tool_input': {'cmd': 'pytest'},
                          'tool_response': {'isError': True, 'structuredContent': {'exit_code': 0}}})
        self.assertTrue(item['error'])
        self.assertNotEqual(item['exit_code'], 0)

    def test_conflicting_or_failed_result_metadata_never_becomes_success(self):
        base = {'tool_name': 'exec_command', 'tool_input': {'cmd': 'pytest'}}
        for result in [{'exit_code': 1, 'result': {'exit_code': 0}},
                       {'exit_code': 0, 'result': {'exit_code': 1}},
                       {'exit_code': 0, 'returncode': 1},
                       {'status': 'failed', 'exit_code': 0}]:
            item = normalize(dict(base, tool_response=result))
            self.assertNotEqual(item['exit_code'], 0, result)
            self.assertTrue(item['failed'], result)

    def test_completion_is_distinct_from_a_successful_shell_check(self):
        shell = {'tool_name': 'exec_command', 'tool_input': {'cmd': 'pytest'}, 'hook_event_name': 'PostToolUse'}
        running = normalize(dict(shell, tool_response={'session_id': 12, 'output': 'still running'}))
        self.assertFalse(running['completed'])
        self.assertFalse(running['failed'])
        done = normalize(dict(shell, tool_response={'exit_code': 1}))
        self.assertTrue(done['completed'])
        self.assertTrue(done['failed'])
        read = normalize({'tool_name': 'Read', 'tool_input': {'file_path': '/repo/a.py'},
                          'hook_event_name': 'PostToolUse', 'tool_response': ''})
        self.assertTrue(read['completed'])
        self.assertIsNone(read['exit_code'])
        failed = normalize(dict(shell, hook_event_name='PostToolUseFailure'))
        self.assertTrue(failed['failed'])
        self.assertTrue(failed['completed'])

    def test_running_result_discards_stale_exit_status(self):
        base = {'tool_name': 'exec_command', 'tool_input': {'cmd': 'pytest'}, 'hook_event_name': 'PostToolUse'}
        for result in [{'session_id': 42, 'exit_code': 0}, {'status': 'running', 'exit_code': 2}]:
            item = normalize(dict(base, tool_response=result))
            self.assertIsNone(item['exit_code'])
            self.assertFalse(item['completed'])
            self.assertFalse(item['failed'])

    def test_malformed_data_is_unsupported_and_does_not_raise(self):
        for payload in [None, [], {}, {'tool_name': []}, {'tool_name': 'exec_command', 'tool_input': 4},
                        {'tool_name': 'exec_command', 'tool_input': {'cmd': {'code': 'rm'}}},
                        {'tool_name': 'exec_command', 'tool_input': '{broken json'},
                        {'tool_name': 'unknown', 'tool_input': {'cmd': 'pytest'}}]:
            with self.subTest(payload=payload):
                item = normalize(payload)
                self.assertFalse(item['supported'])
                self.assertIsNone(item['command'])

    def test_invalid_duration_is_unknown(self):
        for duration in [-1, True, float('inf'), '10', 10**400]:
            item = normalize({'tool_name': 'exec_command', 'tool_input': {'cmd': 'pytest'},
                              'tool_response': {'exit_code': 0, 'wall_time_seconds': duration}})
            self.assertIsNone(item['duration_ms'])


if __name__ == '__main__':
    unittest.main()
