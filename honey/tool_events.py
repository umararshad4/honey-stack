"""Normalize known host tool envelopes without evaluating commands or wrapper code.

``supported`` describes adapter coverage, not permission or command safety.
Unknown response metadata deliberately leaves ``exit_code`` unset.
"""
from __future__ import annotations

import json
import math
import re
import shlex

SHELL = {'bash', 'exec', 'shell', 'local_shell', 'exec_command'}
READ = {'read', 'read_file', 'readfile'}
EDIT = {'write', 'write_file', 'edit', 'multiedit', 'notebookedit', 'apply_patch'}
WRAPPERS = {'exec', 'parallel', 'multi_tool_use'}
_PROCESS_HEADER = re.compile(
    r'\A(?:Chunk ID:[^\n]*\n)?(?:Wall time:[^\n]*\n)?'
    r'Process exited with code (?P<code>-?\d+)(?:\Z|\n(?:Final output:|Output:)(?:\n|\Z))')


def _string(value):
    return value if isinstance(value, str) and value.strip() else None


def _object(value):
    if isinstance(value, dict):
        return value
    if isinstance(value, str) and value.lstrip().startswith('{'):
        try:
            parsed = json.loads(value)
            return parsed if isinstance(parsed, dict) else None
        except (ValueError, RecursionError):
            pass
    return None


def _name(value):
    name = _string(value) or ''
    # These are host namespaces, not arbitrary remote tool names ending in "exec".
    for prefix in ('functions.', 'tools.'):
        if name.startswith(prefix):
            name = name[len(prefix):]
    return 'apply_patch' if name.lower() == 'applypatch' else name


def _number(value):
    try:
        return value if type(value) in (int, float) and math.isfinite(value) and value >= 0 else None
    except OverflowError:
        return None


def _result(payload):
    value = next((payload[k] for k in ('tool_response', 'tool_result', 'result') if k in payload), None)
    obj = _object(value)
    error = (payload.get('is_error') is True or payload.get('isError') is True
             or payload.get('hook_event_name') == 'PostToolUseFailure')
    code, duration, running = None, _number(payload.get('duration_ms')), False
    if obj is None:
        match = _PROCESS_HEADER.match(value) if isinstance(value, str) else None
        return (int(match['code']) if match and not error else None), duration, error, running
    # Only unwrap documented result envelopes. In particular, stdout/output is data.
    for _ in range(4):
        running = running or obj.get('session_id') is not None or obj.get('status') in ('running', 'in_progress', 'queued')
        error = (error or obj.get('is_error') is True or obj.get('isError') is True or bool(obj.get('error'))
                 or obj.get('status') in ('failed', 'error', 'cancelled', 'canceled', 'timed_out'))
        for key in ('exit_code', 'exitCode', 'returncode'):
            if type(obj.get(key)) is int:
                # A nested or alternate success field cannot erase an outer failure.
                if code is None or code == 0:
                    code = obj[key]
        if duration is None:
            duration = _number(obj.get('duration_ms'))
            if duration is None:
                seconds = _number(obj.get('wall_time_seconds'))
                duration = seconds * 1000 if seconds is not None else None
        nested = next((_object(obj[k]) for k in ('structuredContent', 'result') if _object(obj.get(k)) is not None), None)
        if nested is None:
            break
        obj = nested
    return (None if error or running else code), duration, error, running


def normalize(payload):
    """Return a small stable event for guards, evidence, observation and health.

    A structured ``tool_call`` may wrap a single call. JavaScript, tool batches,
    and other opaque wrappers require host-provided inner events; they are never
    parsed as shell or executed here.
    """
    payload = payload if isinstance(payload, dict) else {}
    raw_name = _string(payload.get('tool_name')) or _string(payload.get('name')) or ''
    name = _name(raw_name)
    raw = payload.get('tool_input', payload.get('arguments'))
    ti = _object(raw)
    lower = name.lower()
    if lower in WRAPPERS and ti:
        nested = _object(ti.get('tool_call'))
        if nested and (_string(nested.get('tool_name')) or _string(nested.get('name'))):
            # Preserve outer result/call metadata, not arbitrary inner overrides.
            inner = dict(payload, tool_name=nested.get('tool_name') or nested.get('name'),
                         tool_input=nested.get('tool_input', nested.get('arguments')))
            if _name(inner['tool_name']).lower() not in WRAPPERS:
                return normalize(inner)
    code, duration, error, running = _result(payload)
    item = {'tool': name, 'kind': 'other', 'command': None, 'path': None, 'skill': None,
            'supported': False, 'exit_code': code, 'duration_ms': duration,
            'call_id': _string(payload.get('tool_use_id')) or _string(payload.get('call_id')) or _string(payload.get('tool_call_id')),
            'cwd': _string((ti or {}).get('workdir')) or _string((ti or {}).get('cwd')) or _string(payload.get('cwd')),
            'error': error, 'completed': (code is not None or error) and not running,
            'failed': error or (code is not None and code != 0)}
    if lower in SHELL:
        command = (ti.get('command', ti.get('cmd')) if ti is not None else raw)
        wrapper = lower == 'exec' and (raw_name == 'functions.exec' or (ti is not None and 'code' in ti))
        if wrapper and (ti is None or not any(k in ti for k in ('command', 'cmd'))):
            item['kind'] = 'opaque'
            return item
        if isinstance(command, list) and command and all(isinstance(p, str) for p in command):
            command = shlex.join(command)
        # A malformed JSON object is not a shell command.
        if isinstance(command, str) and command.lstrip().startswith('{') and ti is None:
            command = None
        if _string(command):
            item.update(kind='shell', command=command, supported=True)
        return item
    if lower in READ | EDIT:
        path = _string((ti or {}).get('file_path')) or _string((ti or {}).get('path'))
        patch = (_string((ti or {}).get('patch')) or _string((ti or {}).get('input'))
                 or _string((ti or {}).get('command')) or (_string(raw) if ti is None else None))
        if lower == 'apply_patch' and patch:
            found = re.findall(r'^\*\*\* (?:Add|Update|Delete) File: (.+)$', patch, re.M)
            path = found[0] if len(found) == 1 else None
            valid = patch.lstrip().startswith('*** Begin Patch') and bool(found)
            item['command'] = patch if valid else None
        else:
            valid = ti is not None and (path is not None or lower in {'multiedit', 'notebookedit'})
        item.update(kind='read' if lower in READ else 'edit', path=path, supported=valid)
    elif lower == 'skill':
        skill = _string((ti or {}).get('skill')) or _string((ti or {}).get('name'))
        item.update(kind='skill', skill=skill, supported=skill is not None)
    elif lower in WRAPPERS:
        item['kind'] = 'opaque'
    if (not running and item['supported'] and item['kind'] in {'read', 'edit', 'skill'}
            and payload.get('hook_event_name') == 'PostToolUse'
            and any(k in payload for k in ('tool_response', 'tool_result', 'result'))):
        item['completed'] = True
    return item
