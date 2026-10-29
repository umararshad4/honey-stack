"""Real Git publication with a disposable remote; GitHub is the only API fixture."""
import json
import os
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch as mock

from helpers import REPO
from honey import paths
from honey.rsi import autonomy, patch, publish, store


class Publication(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name, 'source'); self.root.mkdir()
        self.remote = Path(self.tmp.name, 'remote.git')
        self.addCleanup(mock.stopall)
        mock.dict(os.environ, HONEY_HOME=str(Path(self.tmp.name, 'state'))).start()
        mock.object(paths, 'source_repo', return_value=str(self.root)).start()
        self.git('init', '-q', '-b', 'main')
        self.git('config', 'user.name', 'Test')
        self.git('config', 'user.email', 'test@example.test')
        self.write('skills/debug/SKILL.md', 'Reproduce first.\n')
        self.write('honey/runtime.py', 'version = 1\n')
        self.git('add', '.'); self.git('commit', '-qm', 'baseline')
        subprocess.run(['git', 'init', '--bare', '-q', str(self.remote)], check=True)
        self.git('remote', 'add', 'origin', str(self.remote))
        self.git('push', '-qu', 'origin', 'main')
        self.base = self.git('rev-parse', 'HEAD')
        self.write('skills/debug/SKILL.md', 'Reproduce and verify.\n')
        self.write('evals/private/prompt.md', 'PRIVATE CUSTOMER REQUEST\n')
        self.git('add', '.'); self.git('commit', '-qm', 'PRIVATE SESSION MESSAGE')
        self.sha = self.git('rev-parse', 'HEAD')
        self.p = {'id': 'p-test', 'type': 'skill_patch', 'skill': 'debug', 'status': 'applied',
                  'patch_sha': self.sha, 'application': {'state': 'applied'}}
        self.p['source_snapshot'] = {'target': 'skills/debug/SKILL.md',
            'sha256': patch._runtime_digest(patch._runtime_files(str(self.root)), 'skills/debug/SKILL.md')}
        self.save()
        store.write_json(paths.path('config.json'), {'rsi': {'autonomous': True, 'publish': {
            'enabled': True, 'repository': 'example/honey', 'base': 'main'}}})
        # Keep real Git transport, replacing only the GitHub repository identity and API.
        self.real_repository = publish.repository
        mock.object(publish, 'repository', return_value='example/honey').start()
        self.prs = []
        self.creates = 0
        self.fail_create = False
        mock.object(publish, 'gh', side_effect=self.gh).start()

    def write(self, name, text):
        target = self.root / name; target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(text)

    def git(self, *args):
        return subprocess.run(['git', '-C', str(self.root), *args], check=True,
                              capture_output=True, text=True).stdout.strip()

    def save(self):
        store.write_json(paths.path('proposals', self.p['id'] + '.json'), self.p)

    def gh(self, *args):
        if args[:2] == ('pr', 'list'):
            return json.dumps(self.prs)
        if args[:2] == ('pr', 'create'):
            self.creates += 1
            if self.fail_create:
                raise RuntimeError('GitHub temporarily unavailable')
            branch = args[args.index('--head') + 1]
            sha = self.git('ls-remote', 'origin', 'refs/heads/' + branch).split()[0]
            self.prs = [{'url': 'https://github.com/example/honey/pull/1',
                         'headRefOid': sha, 'state': 'OPEN'}]
            return self.prs[0]['url']
        raise AssertionError(args)

    def test_automatic_pass_pushes_only_skill_without_private_history(self):
        self.write('notes.md', 'PRIVATE UNRELATED WORK\n')
        self.git('add', 'notes.md')
        # The integration seam represents evaluation, already required by local application.
        with mock('honey.rsi.patch._validate_eval'):
            result = autonomy.run()
        saved = store.read_json(paths.path('proposals', self.p['id'] + '.json'))
        self.assertEqual(saved['publication']['state'], 'published')
        sha = saved['publication']['sha']
        self.assertEqual(self.git('diff', '--name-only', self.base, sha), 'skills/debug/SKILL.md')
        self.assertEqual(self.git('rev-parse', sha + '^'), self.base)
        self.assertNotIn('PRIVATE', self.git('log', '--format=%B', sha))
        self.assertNotIn('evals/private', self.git('ls-tree', '-r', '--name-only', sha))
        self.assertEqual(self.git('show', sha + ':skills/debug/SKILL.md'), 'Reproduce and verify.')
        self.assertEqual(result['publication']['published'][0]['url'], self.prs[0]['url'])
        self.assertEqual(self.git('rev-parse', 'HEAD'), self.sha)
        self.assertEqual(saved['status'], 'applied')
        self.assertEqual(self.git('diff', '--cached', '--name-only'), 'notes.md')
        self.assertNotIn('notes.md', self.git('ls-tree', '-r', '--name-only', sha))

    def run_publish(self):
        with mock.object(patch, '_validate_eval'):
            return publish.run()

    def test_disabled_and_personal_changes_never_publish(self):
        publish.configure('off')
        self.assertEqual(self.run_publish(), {'skipped': 'publication disabled'})
        settings = store.read_json(paths.path('config.json'))
        settings['rsi']['publish']['enabled'] = True
        store.write_json(paths.path('config.json'), settings)
        for kind in ('instr_line', 'toolkit_fix', 'guard'):
            self.p['type'] = kind; self.save()
            self.assertEqual(self.run_publish(), {'published': [], 'blocked': []})
        publish.gh.assert_not_called()

    def test_failed_create_retries_exact_sha_without_duplicate(self):
        self.fail_create = True
        self.assertEqual(len(self.run_publish()['blocked']), 1)
        saved = store.read_json(paths.path('proposals', 'p-test.json'))
        self.assertEqual(saved['status'], 'applied')
        self.assertEqual(saved['publication']['state'], 'blocked')
        sha = saved['publication']['sha']
        self.fail_create = False
        self.assertEqual(len(self.run_publish()['published']), 1)
        self.assertEqual(store.read_json(paths.path('proposals', 'p-test.json'))['publication']['sha'], sha)
        self.run_publish()
        self.assertEqual(self.creates, 2)

    def test_create_succeeded_but_response_lost_finds_existing_pr(self):
        real = self.gh
        def lose_response(*args):
            result = real(*args)
            if args[:2] == ('pr', 'create'):
                raise RuntimeError('connection lost after create')
            return result
        with mock.object(publish, 'gh', side_effect=lose_response):
            self.assertEqual(len(self.run_publish()['blocked']), 1)
        self.assertEqual(len(self.run_publish()['published']), 1)
        self.assertEqual(self.creates, 1)

    def test_remote_branch_changes_are_preserved(self):
        self.fail_create = True
        self.run_publish()
        saved = store.read_json(paths.path('proposals', 'p-test.json'))
        branch = saved['publication']['branch']
        # Another writer advances the public branch after the first push.
        tree = self.git('rev-parse', saved['publication']['sha'] + '^{tree}')
        changed = self.git('commit-tree', tree, '-p', saved['publication']['sha'], '-m', 'Other writer')
        self.git('push', '-q', 'origin', changed + ':refs/heads/' + branch)
        self.fail_create = False
        result = self.run_publish()
        self.assertIn('refusing to overwrite', result['blocked'][0]['reason'])
        self.assertTrue(self.git('ls-remote', 'origin', 'refs/heads/' + branch).startswith(changed))
        self.assertEqual(self.creates, 1)

    def test_closed_pr_does_not_recreate_deleted_branch(self):
        self.fail_create = True
        self.run_publish()
        saved = store.read_json(paths.path('proposals', 'p-test.json'))['publication']
        self.prs = [{'url': 'https://github.com/example/honey/pull/1',
                     'headRefOid': saved['sha'], 'state': 'CLOSED'}]
        self.git('push', '-q', 'origin', ':refs/heads/' + saved['branch'])
        self.assertIn('closed', self.run_publish()['blocked'][0]['reason'])
        self.assertEqual(self.git('ls-remote', 'origin', 'refs/heads/' + saved['branch']), '')

    def test_rejected_push_preserves_applied_state_and_retries(self):
        hook = self.remote / 'hooks/pre-receive'
        hook.write_text('#!/bin/sh\nexit 1\n'); hook.chmod(0o755)
        self.assertEqual(len(self.run_publish()['blocked']), 1)
        saved = store.read_json(paths.path('proposals', 'p-test.json'))
        self.assertEqual(saved['status'], 'applied')
        self.assertEqual(self.creates, 0)
        hook.unlink()
        self.assertEqual(len(self.run_publish()['published']), 1)
        self.assertEqual(self.prs[0]['headRefOid'], saved['publication']['sha'])

    def test_dirty_runtime_or_changed_origin_blocks_before_push(self):
        self.write('honey/runtime.py', 'private_change = True\n')
        self.assertEqual(len(self.run_publish()['blocked']), 1)
        self.assertEqual(self.git('ls-remote', '--heads', 'origin', 'refs/heads/rsi/*'), '')
        self.git('restore', 'honey/runtime.py')
        with mock.object(publish, 'repository', return_value='other/repo'):
            self.assertIn('origin changed', self.run_publish()['blocked'][0]['reason'])

    def test_unpublished_runtime_ancestry_is_not_exported(self):
        self.git('checkout', '-qb', 'private-base', self.base)
        self.write('honey/runtime.py', 'private_runtime = True\n')
        self.git('commit', '-qam', 'PRIVATE HISTORY')
        self.write('skills/debug/SKILL.md', 'Reproduce and verify.\n')
        self.git('commit', '-qam', 'new evaluated patch')
        self.p['patch_sha'] = self.git('rev-parse', 'HEAD')
        self.p['source_snapshot']['sha256'] = patch._runtime_digest(
            patch._runtime_files(str(self.root)), 'skills/debug/SKILL.md')
        self.save()
        self.assertIn('baseline', self.run_publish()['blocked'][0]['reason'])
        self.assertEqual(self.git('ls-remote', '--heads', 'origin', 'refs/heads/rsi/*'), '')

    def test_missing_or_failed_evaluation_and_sync_are_not_published(self):
        self.p['application']['state'] = 'sync_pending'; self.save()
        self.assertIn('local sync', self.run_publish()['blocked'][0]['reason'])
        self.p['application']['state'] = 'applied'; self.save()
        # Real validation rejects this fixture, which intentionally has no evaluation.
        result = publish.run()
        self.assertIn('eval evidence', result['blocked'][0]['reason'])
        self.assertEqual(self.git('ls-remote', '--heads', 'origin', 'refs/heads/rsi/*'), '')

    def test_configuration_pins_origin_and_default_branch(self):
        with mock.object(publish, 'gh', return_value=json.dumps({
                'nameWithOwner': 'example/honey', 'defaultBranchRef': {'name': 'main'}})):
            self.assertEqual(publish.configure('on'), {
                'enabled': True, 'repository': 'example/honey', 'base': 'main'})
        self.assertEqual(publish.configure('status')['base'], 'main')
        self.assertFalse(publish.configure('off')['enabled'])

    def test_repository_accepts_only_github_origins(self):
        for url in ('https://github.com/example/honey.git', 'git@github.com:example/honey.git'):
            self.git('config', 'remote.origin.url', url)
            self.assertEqual(self.real_repository(), 'example/honey')
        self.git('config', 'remote.origin.url', 'https://example.com/example/honey.git')
        with self.assertRaises(ValueError):
            self.real_repository()
        self.git('config', 'remote.origin.url', 'https://github.com/example/honey.git')
        self.git('config', 'remote.origin.pushurl', 'https://github.com/other/repository.git')
        with self.assertRaisesRegex(ValueError, 'push destination'):
            self.real_repository()


if __name__ == '__main__':
    unittest.main()
