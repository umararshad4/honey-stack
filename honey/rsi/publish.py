"""Publish applied skill changes, never local instructions or session evidence."""
from __future__ import annotations

import json
import os
import re
import subprocess
import tempfile

from honey import paths
from honey.rsi import review, store, text


def command(args, *, env=None, input=None):
    result = subprocess.run(args, cwd=paths.source_repo(), env=env, input=input,
                            capture_output=True, text=True, timeout=120)
    if result.returncode:
        raise RuntimeError(text.redact(result.stderr.strip(), 300) or 'Publication command failed')
    return result.stdout.strip()


def gh(*args):
    return command(['gh', *args])


def git(*args, **kwargs):
    return command(['git', *args], **kwargs)


def repository():
    remote = git('config', '--get', 'remote.origin.url')
    match = re.fullmatch(r'(?:https://github\.com/|git@github\.com:)([\w.-]+/[\w.-]+?)(?:\.git)?/?', remote)
    if not match:
        raise ValueError('Publication requires a GitHub origin remote')
    push_urls = git('remote', 'get-url', '--push', '--all', 'origin').splitlines()
    if len(push_urls) != 1 or push_urls[0].removesuffix('.git') not in (
            'https://github.com/' + match.group(1), 'git@github.com:' + match.group(1)):
        raise ValueError('Publication push destination does not match origin')
    return match.group(1)


def config():
    return (store.read_json(paths.path('config.json'), {}) or {}).get('rsi', {}).get('publish', {})


def configure(action):
    cfg = store.read_json(paths.path('config.json'), {}) or {}
    settings = cfg.setdefault('rsi', {}).setdefault('publish', {})
    if action == 'on':
        repo = repository()
        details = json.loads(gh('repo', 'view', repo, '--json', 'nameWithOwner,defaultBranchRef'))
        if details['nameWithOwner'].lower() != repo.lower():
            raise ValueError('GitHub repository does not match origin')
        settings.update(enabled=True, repository=repo, base=details['defaultBranchRef']['name'])
    elif action == 'off':
        settings['enabled'] = False
    if action != 'status':
        store.write_json(paths.path('config.json'), cfg)
    return settings


def save(proposal):
    store.write_json(paths.path('proposals', paths.safe_id(proposal['id']) + '.json'), proposal)


def prepare(proposal, settings):
    """Build a public commit from the remote base and a single validated blob."""
    from honey.rsi import patch
    skill = proposal.get('skill', '')
    if not re.fullmatch(r'[a-z][a-z0-9-]*', skill):
        raise ValueError('Publication requires a named skill')
    if (proposal.get('application') or {}).get('state') != 'applied':
        raise ValueError('Publication requires successful local sync')
    patch._validate_eval(proposal)
    if not proposal.get('source_snapshot'):
        raise ValueError('Publication requires an evaluated runtime snapshot')
    patch._check_runtime_snapshot(proposal, set())
    if git('status', '--porcelain', '--', *patch.RUNTIME_SURFACE):
        raise ValueError('Publication requires a clean runtime; local changes stay private')
    sha = proposal.get('patch_sha', '')
    if not re.fullmatch(r'[0-9a-f]{40,64}', sha):
        raise ValueError('Publication requires an exact evaluated commit')
    parents = git('rev-list', '--parents', '-n', '1', sha).split()
    if len(parents) != 2:
        raise ValueError('Publication requires a single-parent evaluated patch')
    base = settings['base']
    git('check-ref-format', 'refs/heads/' + base)
    git('fetch', '--no-tags', 'origin', 'refs/heads/' + base)
    base_sha = git('rev-parse', 'FETCH_HEAD')
    if git('diff', '--name-only', base_sha, parents[1], '--', *patch.RUNTIME_SURFACE):
        raise ValueError('Remote runtime differs from evaluation baseline; re-evaluate first')
    target = f'skills/{skill}/SKILL.md'
    if git('diff', '--name-only', parents[1], sha, '--', *patch.RUNTIME_SURFACE) != target:
        raise ValueError('Evaluated patch changed unexpected runtime files')
    entry = git('ls-tree', sha, '--', target).split()
    if len(entry) != 4 or entry[:2] != ['100644', 'blob'] or entry[3] != target:
        raise ValueError('Published skill must be a regular file')
    # An isolated index cannot stage user files. No private commit becomes an ancestor.
    with tempfile.TemporaryDirectory(prefix='honey-publish-') as directory:
        env = dict(os.environ, GIT_INDEX_FILE=os.path.join(directory, 'index'))
        git('read-tree', base_sha, env=env)
        git('update-index', '--add', '--cacheinfo', '100644', entry[2], target, env=env)
        tree = git('write-tree', env=env)
        public_sha = git('commit-tree', tree, '-p', base_sha,
                         input=f'fix(skills): improve {skill} workflow\n')
    return {'state': 'prepared', 'sha': public_sha, 'source_sha': sha, 'base_sha': base_sha,
            'branch': 'rsi/publish-' + paths.safe_id(proposal['id']),
            'repository': settings['repository'], 'base': base, 'updated': text.now()}


def publish(proposal, settings):
    if repository().lower() != settings['repository'].lower():
        raise ValueError('Publication origin changed; enable publication again to confirm it')
    state = proposal.get('publication') or {}
    if not state.get('sha'):
        state = prepare(proposal, settings)
        proposal['publication'] = state
        save(proposal)  # Persist the exact commit before any network write.
    if (state['source_sha'] != proposal.get('patch_sha') or
            any(state[key] != settings[key] for key in ('repository', 'base'))):
        raise ValueError('Publication target or evaluated commit changed')
    branch, sha, repo = state['branch'], state['sha'], state['repository']
    args = ('pr', 'list', '--repo', repo, '--head', branch, '--base', state['base'],
            '--state', 'all', '--json', 'url,headRefOid,state')
    prs = json.loads(gh(*args))
    if prs and (len(prs) != 1 or prs[0]['headRefOid'] != sha or prs[0]['state'] not in ('OPEN', 'MERGED')):
        raise ValueError('Publication PR is closed, ambiguous or has a different head')
    if prs and prs[0]['state'] == 'MERGED':
        state.update(state='published', url=prs[0]['url'], updated=text.now())
        state.pop('error', None)
        save(proposal)
        return {'id': proposal['id'], 'url': state['url'], 'sha': sha}
    remote = git('ls-remote', '--heads', 'origin', 'refs/heads/' + branch).split()
    if remote and remote[0] != sha:
        raise ValueError('Publication branch changed remotely; refusing to overwrite it')
    git('push', 'origin', sha + ':refs/heads/' + branch)
    remote = git('ls-remote', '--heads', 'origin', 'refs/heads/' + branch).split()
    if not remote or remote[0] != sha:
        raise ValueError('Published head could not be verified')
    if not prs:
        # Only fixed metadata is sent; rationale, evidence and generated evals stay local.
        with tempfile.TemporaryDirectory(prefix='honey-pr-') as directory:
            body = os.path.join(directory, 'body.md')
            store.write_text(body, 'Updates one skill after local regression evaluation and successful plugin sync.\n\n'
                             'Only the skill file is published. Private session evidence and generated evaluation '
                             'prompts remain local. Local evaluation does not replace repository CI or review.\n')
            gh('pr', 'create', '--repo', repo, '--base', state['base'], '--head', branch,
               '--title', 'fix(skills): improve ' + proposal['skill'] + ' workflow', '--body-file', body)
        prs = json.loads(gh(*args))
    if len(prs) != 1 or prs[0]['headRefOid'] != sha or prs[0]['state'] not in ('OPEN', 'MERGED'):
        raise ValueError('Publication PR is closed, ambiguous or has a different head')
    state.update(state='published', url=prs[0]['url'], updated=text.now())
    state.pop('error', None)
    save(proposal)
    return {'id': proposal['id'], 'url': state['url'], 'sha': sha}


def run():
    """Caller owns the RSI lock; publication failure never undoes local application."""
    settings = config()
    if not settings.get('enabled'):
        return {'skipped': 'publication disabled'}
    result = {'published': [], 'blocked': []}
    pending = [p for p in review.all_proposals() if p.get('type') == 'skill_patch'
               and p.get('status') == 'applied' and (p.get('publication') or {}).get('state') != 'published']
    pending.sort(key=lambda p: (p.get('publication') or {}).get('updated', ''))
    for proposal in pending[:20]:
        try:
            result['published'].append(publish(proposal, settings))
        except Exception as exc:
            error = text.redact(str(exc), 300)
            proposal.setdefault('publication', {}).update(state='blocked', error=error, updated=text.now())
            save(proposal)
            result['blocked'].append({'id': proposal['id'], 'reason': error})
    store.write_json(paths.path('state', 'publication-last.json'), dict(result, ts=text.now()))
    return result
