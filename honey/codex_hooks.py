"""Read current Codex hook trust without executing hooks or changing approvals."""
from __future__ import annotations

import json
import os
import selectors
import shutil
import subprocess
import time

PLUGIN = 'honey@honey-stack'
MAX_RESPONSE_BYTES = 2 * 1024 * 1024
EXPECTED_EVENTS = {'preToolUse', 'postToolUse', 'postCompact', 'sessionStart', 'sessionEnd',
                   'userPromptSubmit', 'subagentStart', 'stop', 'interrupt'}


def _registry(cwd: str, timeout: float) -> dict:
    exe = shutil.which('codex')
    if not exe:
        raise RuntimeError('codex CLI not found')
    process = subprocess.Popen([exe, 'app-server'], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                               stderr=subprocess.DEVNULL, env=dict(os.environ, HONEY_DISABLE='1', RSI_CHILD='1'))
    selector = selectors.DefaultSelector()
    selector.register(process.stdout, selectors.EVENT_READ)
    buffer = b''
    deadline = time.monotonic() + timeout

    def request(ident, method, params):
        nonlocal buffer
        process.stdin.write((json.dumps({'id': ident, 'method': method, 'params': params}) + '\n').encode())
        process.stdin.flush()
        while time.monotonic() < deadline:
            while b'\n' in buffer:
                line, buffer = buffer.split(b'\n', 1)
                response = json.loads(line)
                if not isinstance(response, dict):
                    raise ValueError('invalid Codex registry response')
                if response.get('id') == ident:
                    if 'error' in response:
                        raise RuntimeError('Codex rejected hook registry request')
                    result = response.get('result')
                    if not isinstance(result, dict):
                        raise ValueError('invalid Codex registry result')
                    return result
            if not selector.select(max(0, deadline - time.monotonic())):
                break
            chunk = os.read(process.stdout.fileno(), 65536)
            if not chunk:
                raise RuntimeError('Codex registry closed unexpectedly')
            buffer += chunk
            if len(buffer) > MAX_RESPONSE_BYTES:
                raise ValueError('Codex registry response too large')
        raise TimeoutError('Codex hook registry timed out')

    try:
        request(1, 'initialize', {'clientInfo': {'name': 'honey_hook_inspector', 'version': '1.0'},
                                  'capabilities': {'experimentalApi': True}})
        process.stdin.write(b'{"method":"initialized"}\n')
        process.stdin.flush()
        return request(2, 'hooks/list', {'cwds': [cwd]})
    finally:
        selector.close()
        process.terminate()
        try:
            process.wait(timeout=1)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait()
        process.stdin.close()
        process.stdout.close()


def inspect(cwd=None, timeout=8.0) -> dict:
    """Return trusted/review_required/disabled/missing/unknown from the native registry."""
    try:
        result = _registry(os.path.abspath(cwd or os.getcwd()), timeout)
        entries = result.get('data')
        if not isinstance(entries, list) or len(entries) != 1 or not isinstance(entries[0], dict):
            raise ValueError('invalid Codex hook listing')
        entry = entries[0]
        if entry.get('errors'):
            raise RuntimeError('Codex reported hook configuration errors')
        hooks = entry.get('hooks')
        if not isinstance(hooks, list) or any(not isinstance(h, dict) for h in hooks):
            raise ValueError('invalid Codex hooks')
        mine = [h for h in hooks if h.get('pluginId') == PLUGIN or
                str(h.get('key', '')).startswith(PLUGIN + ':')]
        out = {'total': len(mine), 'trusted': 0, 'modified': 0, 'untrusted': 0, 'disabled': 0}
        for hook in mine:
            trust = hook.get('trustStatus')
            if trust not in ('trusted', 'managed', 'modified', 'untrusted'):
                raise ValueError('unknown Codex hook trust status')
            if type(hook.get('enabled')) is not bool:
                raise ValueError('unknown Codex hook enabled state')
            out['trusted' if trust == 'managed' else trust] += 1
            out['disabled'] += not hook['enabled']
        out['missing_events'] = sorted(EXPECTED_EVENTS - {h.get('eventName') for h in mine})
        out['status'] = ('missing' if not mine else 'incomplete' if out['missing_events']
                         else 'review_required' if out['modified'] or out['untrusted']
                         else 'disabled' if out['disabled'] else 'trusted')
        return out
    except (OSError, ValueError, RuntimeError, TimeoutError) as exc:
        return {'status': 'unknown', 'reason': str(exc)}
