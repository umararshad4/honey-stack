"""Bounded task intent and observed checks. These records never grant tool permissions."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shlex
import time

from honey import paths
from honey.rsi import signals, store, text

CHECKS = {'code': ['verification'], 'generic': ['verification'],
          'uninstall': ['application', 'helpers', 'startup', 'preserved-data'],
          'startup': ['startup']}
INSPECT = re.compile(r"\b(read.only|only (?:tell|explain|inspect|review)|(?:first|just) tell|"
                     r"(?:do not|don't) (?:implement\b|(?:change|edit|modify) (?:any |the )?(?:files?|code|anything)\b|"
                     r"(?:change|edit|modify)\s*[.!?]?$))", re.I)
ACTION = re.compile(r'\b(implement|fix|build|create|add|write|refactor|update|rename|run|restart|install|change|edit|remove|uninstall|delete|disable|enable|configure|commit|push|merge|deploy)\b|\bmake\s+(?:it|that|this)\b', re.I)
DIRECT_ACTION = re.compile(r'^\s*(?:please\s+|yes[, ]+)?(?:do it|go ahead)[.!\s]*$', re.I)
FOLLOWUP = re.compile(r'^\s*(?:also\b|but\b|no[, ]|that\b|it\b|same\b)', re.I)
QUESTION = re.compile(r'^\s*(?:what|why|how|which|tell me|explain|inspect)\b', re.I)
STATUS = re.compile(r'^\s*(?:what(?:\s+is|\'s)\s+(?:the\s+)?(?:status|progress)|any\s+(?:updates?|progress)|status\??$|how\s+is\s+it\s+going)', re.I)
NAME = re.compile(r'^[a-z][a-z0-9-]{0,39}$')


def _absolute(path, cwd):
    return os.path.abspath(os.path.join(cwd, os.path.expanduser(path)))


def create(state, request, mode, operation, cwd, targets=(), checks=None, approved=()):
    task = {'id': 't' + str(state.get('turn', 0)) + '-' + str(time.time_ns()),
            'mode': mode, 'operation': operation, 'request': text.redact(request, 300),
            'cwd': os.path.abspath(cwd), 'targets': list(targets)[:20],
            'approved_actions': list(approved)[:10],
            'checks': list(checks if checks is not None else CHECKS[operation])[:12] if mode == 'execute' else [],
            'mutation': 0, 'evidence': {}, 'calls': [], 'seen_calls': [], 'check_outcomes': {}}
    state['task'] = task
    return task


def advance(ctx, prompt):
    """Keep explicit continuations; a fresh request starts with no prior proof or authority."""
    old = ctx.state.get('task')
    if old and STATUS.search(prompt) and not INSPECT.search(prompt):
        return
    inspect = bool(INSPECT.search(prompt) or QUESTION.search(prompt))
    has_action = bool(ACTION.search(prompt) or DIRECT_ACTION.fullmatch(prompt))
    continuation = bool(set(signals.classify(prompt)) & {'continue', 'accept'}) or bool(FOLLOWUP.match(prompt))
    if old and continuation and not inspect and not (old['mode'] == 'inspect' and has_action):
        for action in list(old['approved_actions']):
            if re.search(r"\b(?:no|not|never|don't|without)\s+(?:\w+\s+){0,2}" + action + r'\b', prompt, re.I):
                old['approved_actions'].remove(action)
                ctx.dirty = True
        return
    mode = 'inspect' if inspect or not has_action else 'execute'
    operation = ('uninstall' if re.search(r'\b(uninstall|remove).{0,60}(app|software|completely)', prompt, re.I)
                 else 'startup' if re.search(r'\b(startup|login items?)\b', prompt, re.I)
                 else 'code' if re.search(r'\b(fix|implement|code|parser|function|bug|refactor|build)\b', prompt, re.I)
                 else 'generic')
    # Descriptive only. Neither native permissions nor the safety guard consults this as approval.
    approved = [a for a in ('commit', 'push', 'merge', 'deploy', 'remove', 'disable')
                if mode == 'execute' and re.search(r'\b' + a + r'\b', prompt, re.I)
                and not re.search(r"\b(?:no|not|never|don't|without)\s+(?:\w+\s+){0,2}" + a + r'\b', prompt, re.I)]
    create(ctx.state, prompt, mode, operation, ctx.payload.get('cwd') or os.getcwd(), approved=approved)
    ctx.dirty = True


def command_kind(command):
    """Recognize direct check/mutation commands; prose and arbitrary interpreter code are unknown."""
    if not isinstance(command, str) or any(c in command for c in ('\n', '\r', '$', '`')):
        return None
    try:
        lexer = shlex.shlex(command, posix=True, punctuation_chars=True)
        lexer.whitespace_split = True
        words = list(lexer)
    except ValueError:
        return None
    # Composite commands need an explicit mapped check; their final exit code can mask a failure.
    if not words or any(re.fullmatch(r'[;&|<>()]+', w) for w in words):
        return None
    exe, args = os.path.basename(words[0]), words[1:]
    if re.fullmatch(r'python(?:3(?:\.\d+)?)?', exe.lower()):
        exe = 'python3'
    if exe in ('python', 'python3') and args and os.path.abspath(args[0]) == os.path.join(paths.REPO, 'bin', 'honey'):
        exe, args = 'honey', args[1:]
    if exe == 'honey' and (args[:1] == ['doctor'] or len(args) > 1 and args[0] == 'task' and args[1] in ('status', 'set', 'verify', 'run')):
        return 'read'  # bookkeeping changes evidence, not the task's target state
    # A redirected project/test path needs an explicitly mapped check, not automatic credit.
    external = any(a.split('=', 1)[-1].startswith(('/', '../', '~/'))
                   or a.split('=', 1)[0] in ('-C', '--cwd', '--prefix', '--directory', '--rootdir', '--git-dir', '--work-tree')
                   for a in args)
    check = None if external else 'check'
    if exe in ('pytest', 'py.test', 'unittest', 'tsc', 'eslint'):
        return check
    if exe in ('python', 'python3') and (args[:2] in (['-m', 'pytest'], ['-m', 'unittest'])
                                       or args and re.match(r'^(?:\./)?tests/[^ ]+\.py$', args[0])):
        return check
    if exe in ('npm', 'pnpm', 'yarn', 'bun') and args and (args[0] in ('test', 'lint', 'typecheck')
             or len(args) > 1 and args[0] == 'run' and args[1] in ('test', 'lint', 'typecheck')):
        return check
    if exe in ('cargo', 'go') and args[:1] == ['test'] or exe == 'ruff' and args[:1] == ['check']:
        return check
    if exe == 'git':
        while args and args[0].startswith('-'):
            n = 2 if args[0] in ('-C', '-c', '--git-dir', '--work-tree') else 1
            args = args[n:]
        if args[:1] == ['diff'] and '--check' in args:
            return check
        if args and args[0] in ('apply', 'checkout', 'restore', 'reset', 'clean', 'merge', 'rebase', 'cherry-pick'):
            return 'mutation'
        if args and args[0] in ('status', 'diff', 'log', 'show', 'ls-files', 'rev-parse') and not any(a.startswith('--output') for a in args):
            return 'read'
    if exe in ('rm', 'mv', 'cp', 'mkdir', 'rmdir', 'touch', 'install'):
        return 'mutation'
    if exe in ('sed', 'perl') and any(a == '-i' or a.startswith('-i') for a in args):
        return 'mutation'
    if exe in ('cat', 'head', 'tail', 'ls', 'stat', 'wc', 'du', 'df', 'pwd', 'readlink', 'pgrep', 'test', 'true', 'false'):
        return 'read'
    if exe in ('rg', 'grep') and not any(a.startswith(('--pre', '--hostname-bin')) for a in args):
        return 'read'
    if exe == 'launchctl' and args[:1] in (['print'], ['list'], ['print-disabled']):
        return 'read'
    return None


def mutation(event):
    return event.get('kind') == 'edit' or command_kind(event.get('command')) == 'mutation'


def protect(state, event):
    task = state.get('task') or {}
    if task.get('mode') == 'inspect' and mutation(event):
        return 'This task is inspection-only. A user request to make changes is needed before editing.'
    return None


def _outcome(task, fingerprint, status):
    outcomes = task.setdefault('check_outcomes', {})
    outcomes[fingerprint] = status
    if len(outcomes) > 40:
        task['check_overflow'] = True
        del outcomes[next(iter(outcomes))]
    task['evidence'].pop('verification', None)
    for name, proof in list(task['evidence'].items()):
        if proof.get('fingerprint') == fingerprint:
            del task['evidence'][name]


def _tracked(task, command):
    return (command_kind(command) == 'check'
            or hashlib.sha256((command or '').encode()).hexdigest() in task.get('check_outcomes', {}))


def _invalidate(ctx, task, preserve_runner=False):
    task['mutation'] += 1
    task['evidence'] = {name: proof for name, proof in task['evidence'].items()
                        if preserve_runner and proof.get('source') == 'runner'}
    ctx.dirty = True


def start_tool(ctx, event):
    """Remember task/generation before a tool runs, including across a later task change."""
    task = ctx.state.get('task')
    if not task or event.get('kind') != 'shell':
        return
    call_id = event.get('call_id')
    if call_id:
        starts = ctx.state.setdefault('tool_starts', {})
        starts[call_id] = {'task': task['id'], 'mutation': task['mutation']}
        if len(starts) > 80:
            ctx.state['tool_start_overflow'] = True
            del starts[next(iter(starts))]
    if (_tracked(task, event.get('command'))
            and _absolute(event.get('cwd') or ctx.payload.get('cwd') or task['cwd'], task['cwd']) == task['cwd']):
        _outcome(task, hashlib.sha256(event['command'].encode()).hexdigest(), 'unknown')
    ctx.dirty = True


def record_tool(ctx, event):
    task = ctx.state.get('task')
    if not task:
        return
    call_id = event.get('call_id')
    start = ctx.state.get('tool_starts', {}).get(call_id)
    if start and start['task'] != task['id']:
        if event.get('completed'):
            ctx.state['tool_starts'].pop(call_id, None)
            ctx.dirty = True
        return
    if call_id and call_id in task['seen_calls']:
        return
    # Starting an unverified rerun cannot preserve an earlier claim that this check passed.
    if event.get('kind') == 'shell' and event.get('exit_code') is None and not event.get('error'):
        if (_tracked(task, event.get('command'))
                and _absolute(event.get('cwd') or ctx.payload.get('cwd') or task['cwd'], task['cwd']) == task['cwd']):
            fingerprint = hashlib.sha256(event['command'].encode()).hexdigest()
            _outcome(task, fingerprint, 'unknown')
            ctx.dirty = True
        elif command_kind(event.get('command')) != 'read':
            _invalidate(ctx, task)
        return
    if call_id:
        task['seen_calls'] = (task['seen_calls'] + [call_id])[-80:]
    before_mutation = task['mutation']
    if (mutation(event) or event.get('kind') == 'opaque'
            or event.get('kind') == 'shell' and command_kind(event.get('command')) not in ('read', 'check')
            and not _tracked(task, event.get('command'))):
        _invalidate(ctx, task, preserve_runner=event.get('kind') == 'opaque' and not event.get('failed'))
        if event.get('path'):
            target = _absolute(event['path'], task['cwd'])
            task['targets'] = list(dict.fromkeys(task['targets'] + [target]))[-20:]
    cmd = event.get('command') or ''
    cwd = _absolute(event.get('cwd') or ctx.payload.get('cwd') or task['cwd'], task['cwd'])
    start = ctx.state.get('tool_starts', {}).pop(call_id, None)
    fresh = (start == {'task': task['id'], 'mutation': before_mutation} if start is not None
             else not ctx.state.get('tool_start_overflow'))
    good = (event.get('exit_code') == 0 and not event.get('error') and event.get('supported')
            and cwd == task['cwd'] and fresh)
    item = {'id': call_id, 'mutation': task['mutation'], 'success': bool(good),
            'command': text.redact(cmd, 160), 'fingerprint': hashlib.sha256(cmd.encode()).hexdigest(), 'cwd': cwd}
    if call_id:
        task['calls'] = (task['calls'] + [item])[-40:]
    if _tracked(task, cmd) and cwd == task['cwd']:
        _outcome(task, item['fingerprint'], 'passed' if good else 'failed')
        if good and 'verification' in task['checks']:
            task['evidence']['verification'] = item
    ctx.dirty = True


def missing(state):
    task = state.get('task') or {}
    if task.get('mode') != 'execute':
        return []
    from honey import verification
    pending = []
    for name in task.get('checks', []):
        proof = task.get('evidence', {}).get(name, {})
        good = verification.valid(task, proof) if proof.get('source') == 'runner' else (
            proof.get('mutation') == task.get('mutation') and proof.get('success'))
        if not good:
            pending.append(name)
    for name, proof in task.get('evidence', {}).items():
        target = proof.get('path')
        if target and ((proof.get('observation') == 'absent' and os.path.lexists(target))
                       or (proof.get('observation') == 'present' and not os.path.exists(target))):
            if name not in pending:
                pending.append(name)
    if any(status != 'passed' for status in task.get('check_outcomes', {}).values()):
        pending.append('failed-or-incomplete-check')
    if task.get('check_overflow'):
        pending.append('check-history-overflow (start an explicit bounded task)')
    return pending


def main(argv):
    p = argparse.ArgumentParser(prog='honey task')
    p.add_argument('action', choices=['status', 'set', 'verify', 'run'])
    p.add_argument('--agent', choices=['claude', 'codex'], default='codex')
    p.add_argument('--session', default=os.environ.get('CODEX_THREAD_ID'))
    p.add_argument('--json', action='store_true')
    p.add_argument('--mode', choices=['inspect', 'execute'])
    p.add_argument('--cwd', help='bind a task contract to its actual workspace')
    p.add_argument('--operation', choices=list(CHECKS), default='generic')
    p.add_argument('--target', action='append', default=[])
    p.add_argument('--check', action='append', default=[])
    p.add_argument('--tool-call')
    p.add_argument('--absent')
    p.add_argument('--present')
    separator = argv.index('--') if '--' in argv else len(argv)
    command = argv[separator + 1:] if separator < len(argv) else []
    a = p.parse_args(argv[:separator])
    if not a.session:
        p.error('--session is required outside a Codex session')
    file = paths.path('state', 'sessions', paths.session_key(a.agent, a.session) + '.json')
    if a.action == 'run':
        return _operate(a, file, command)
    with store.session_lock(file):
        return _operate(a, file, command)


def _operate(a, file, command):
    state = store.read_json(file, {}) or {}
    task = state.get('task')
    try:
        if a.action == 'run':
            from honey import verification
            if len(a.check) != 1:
                raise ValueError('Choose exactly one required check')
            return verification.run(file, a.check[0], command)
        if command:
            raise ValueError('Commands are accepted only by task run')
        if a.action == 'set':
            if not a.mode:
                raise ValueError('--mode is required')
            if any(not NAME.fullmatch(c) for c in a.check):
                raise ValueError('check names must be short lowercase identifiers')
            # Recording an agent-authored contract cannot relax an explicit user read-only request.
            if task and task.get('mode') == 'inspect' and a.mode == 'execute':
                raise ValueError('the user must request execution before changing an inspection task')
            cwd = os.path.abspath(os.path.expanduser(a.cwd)) if a.cwd else (task or {}).get('cwd') or os.getcwd()
            if not os.path.isdir(cwd):
                raise ValueError('task workspace must be an existing directory')
            task = create(state, (task or {}).get('request', ''), a.mode, a.operation, cwd,
                          [_absolute(t, cwd) for t in a.target], a.check or None,
                          (task or {}).get('approved_actions', []))
        elif a.action == 'verify':
            if not task or task.get('mode') != 'execute' or len(a.check) != 1 or a.check[0] not in task['checks']:
                raise ValueError('choose one required check from an execution task')
            if sum(bool(v) for v in (a.tool_call, a.absent, a.present)) != 1:
                raise ValueError('supply exactly one of --tool-call, --absent, or --present')
            if a.tool_call:
                proof = next((c for c in reversed(task['calls']) if c['id'] == a.tool_call), None)
                from honey import verification
                current = verification.valid(task, proof) if proof and proof.get('source') == 'runner' else (
                    proof and proof.get('mutation') == task['mutation'])
                if not proof or not proof['success'] or not current:
                    raise ValueError('tool call lacks fresh successful evidence in this task workspace')
                latest = next(c for c in reversed(task['calls']) if c['fingerprint'] == proof['fingerprint'])
                if latest['id'] != proof['id'] or task['check_outcomes'].get(proof['fingerprint'], 'passed') != 'passed':
                    raise ValueError('tool call was superseded by a later or incomplete check')
                if proof['fingerprint'] not in task['check_outcomes']:
                    _outcome(task, proof['fingerprint'], 'passed')
            else:
                if task['operation'] == 'uninstall' and a.check[0] == 'application' and not a.absent:
                    raise ValueError('uninstall application verification requires absence')
                target = _absolute(a.absent or a.present, task['cwd'])
                if target not in task['targets']:
                    raise ValueError('file check must refer to a declared target')
                good = not os.path.lexists(target) if a.absent else os.path.exists(target)
                if not good:
                    task['evidence'].pop(a.check[0], None)
                    store.write_json(file, state)
                    raise ValueError('the filesystem check failed')
                proof = {'mutation': task['mutation'], 'success': True, 'path': target,
                         'observation': 'absent' if a.absent else 'present'}
            task['evidence'][a.check[0]] = proof
        if a.action != 'status':
            store.write_json(file, state)
        from honey import metrics
        result = {'task': task, 'missing_checks': missing(state), 'metrics': metrics.report(state),
                  'note': 'Recorded scope is not permission. Tool evidence proves exit status and freshness, not arbitrary semantics.'}
        print(json.dumps(result, indent=2))
        return 0
    except ValueError as exc:
        print(str(exc), file=__import__('sys').stderr)
        return 2
