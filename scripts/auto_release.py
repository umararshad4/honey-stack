#!/usr/bin/env python3
"""Release a tested main revision; run only after the CI test matrix succeeds."""
import argparse
import json
import os
import re
import subprocess
import sys
import tempfile

import release


def command(*args):
    result = subprocess.run(args, cwd=release.ROOT, capture_output=True, text=True)
    if result.returncode:
        raise RuntimeError(result.stderr.strip() or f'{args[0]} failed')
    return result.stdout.strip()


def git(*args):
    return command('git', *args)


def repository():
    repo = os.environ.get('GITHUB_REPOSITORY', '')
    if not re.fullmatch(r'[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+', repo):
        raise ValueError('GITHUB_REPOSITORY must identify the release repository')
    return repo


def published_releases():
    repo = repository()
    pages = json.loads(command('gh', 'api', '--paginate', '--slurp', f'repos/{repo}/releases'))
    return [item for page in pages for item in page]


def publish(tag):
    if not tag.startswith('v') or not release.SEMVER.fullmatch(tag[1:]):
        raise ValueError('Release tag must be vMAJOR.MINOR.PATCH')
    repo = repository()
    existing = [r for r in published_releases() if r['tag_name'] == tag]
    if existing:
        if existing[0].get('draft'):
            raise ValueError('An existing draft release needs manual review')
        return existing[0]['html_url']
    log = git('show', f'{tag}:CHANGELOG.md')
    match = re.search(rf'^## \[{re.escape(tag[1:])}\][^\n]*\n(.*?)(?=^## \[|\Z)', log, re.M | re.S)
    if not match or not match.group(1).strip():
        raise ValueError('Release notes are missing from the tagged commit')
    with tempfile.TemporaryDirectory(prefix='honey-release-') as folder:
        notes = os.path.join(folder, 'notes.md')
        with open(notes, 'w', encoding='utf-8') as stream:
            stream.write(match.group(1).strip() + '\n')
        return command('gh', 'release', 'create', tag, '--repo', repo, '--title', f'honey-stack {tag}',
                       '--notes-file', notes, '--verify-tag')


def run(expected):
    if not re.fullmatch(r'[0-9a-f]{40,64}', expected):
        raise ValueError('Expected CI revision must be a full commit SHA')
    repository()
    if git('status', '--porcelain'):
        raise ValueError('Automatic releases require a clean checkout')
    if git('branch', '--show-current') != 'main':
        raise ValueError('Automatic releases require the main branch')
    git('fetch', '--tags', 'origin', 'main')
    remote = git('rev-parse', 'origin/main')
    if git('rev-parse', 'HEAD') != remote:
        return {'skipped': 'Checkout is behind current main; a newer CI run owns the release'}
    tags = [t for t in git('tag', '--merged', 'HEAD', '--list', 'v*').splitlines()
            if release.SEMVER.fullmatch(t[1:])]
    # A rerun after an atomic push must publish the same tag, never bump again.
    for tag in tags:
        body = git('log', '-1', '--format=%B', tag)
        if f'Release-Source: {expected}' in body.splitlines():
            if git('rev-parse', tag + '^') != expected:
                raise ValueError('Release source marker does not match the tag parent')
            return {'tag': tag, 'url': publish(tag), 'recovered': True}
    if remote != expected:
        return {'skipped': 'Tested revision is no longer current main'}
    if not tags:
        raise ValueError('Automatic releases require an existing version tag')
    latest = max(tags, key=lambda t: tuple(map(int, t[1:].split('.'))))
    versions = set(release.versions().values())
    if versions != {latest[1:]}:
        raise ValueError('Current metadata does not match the latest reachable version tag')
    current = latest[1:]
    messages = git('log', f'{latest}..HEAD', '--format=%B%x00').split('\0')
    messages = [m.strip() for m in messages if m.strip()]
    if not messages:
        return {'tag': latest, 'url': publish(latest), 'recovered': True}
    new = release.next_version(current, messages)
    published_releases()  # Fail authentication before committing or pushing metadata.
    fallback = '### Changed\n' + '\n'.join('- ' + m.splitlines()[0] for m in messages)
    release.prepare(new, fallback_notes=fallback)
    # Tests run against the bumped metadata, before any remote state changes.
    subprocess.run([sys.executable, os.path.join(release.ROOT, 'tests', 'run.py')],
                   cwd=release.ROOT, check=True)
    if git('rev-parse', 'HEAD') != expected:
        raise ValueError('HEAD changed during tests; refusing to publish unverified commits')
    files = ('CHANGELOG.md', release.INIT, *release.JSON_FILES)
    changed = set(git('diff', '--name-only', 'HEAD').splitlines())
    if changed - set(files) or git('ls-files', '--others', '--exclude-standard'):
        raise ValueError('Tests changed files outside release metadata')
    if set(release.versions().values()) != {new}:
        raise ValueError('Release metadata changed during tests')
    git('add', '--', *files)
    git('commit', '-m', f'release: v{new}', '-m', f'Release-Source: {expected}')
    tag = 'v' + new
    git('tag', '-a', tag, '-m', tag)
    git('push', '--atomic', 'origin', 'HEAD:refs/heads/main', f'refs/tags/{tag}')
    return {'tag': tag, 'url': publish(tag), 'recovered': False}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument('--expected-head')
    source.add_argument('--publish-tag')
    args = parser.parse_args()
    print(json.dumps(run(args.expected_head) if args.expected_head else {'url': publish(args.publish_tag)}, indent=2))
