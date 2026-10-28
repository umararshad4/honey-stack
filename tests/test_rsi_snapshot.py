"""Evaluated runtime parity with real worktrees; only the evaluator/sync boundaries are fixtures."""
import os
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch as mock
from helpers import REPO
from honey import paths
from honey.rsi import patch, store


class RuntimeSnapshot(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(); self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name, 'repo'); self.root.mkdir()
        self.addCleanup(mock.stopall)
        mock.dict(os.environ, HONEY_HOME=str(Path(self.tmp.name, 'state'))).start()
        mock.object(paths, 'source_repo', return_value=str(self.root)).start()
        for args in [('init', '-q'), ('config', 'user.name', 'Test'), ('config', 'user.email', 'test@example.test')]:
            self.git(*args)
        self.write('skills/debug/SKILL.md', 'Reproduce first.\n')
        self.write('honey/runtime.py', 'old = True\n')
        self.write('hooks/remove.py', 'old = True\n')
        self.git('add', '.'); self.git('commit', '-qm', 'initial')
        self.before = self.git('rev-parse', 'HEAD')

    def write(self, name, content):
        store.write_text(str(self.root / name), content)

    def git(self, *args):
        return subprocess.run(['git', '-C', str(self.root), *args], check=True, capture_output=True, text=True).stdout.strip()

    def evaluate(self, root, pattern, out):
        changed = Path(root, 'skills/debug/SKILL.md').read_text() == 'Reproduce and verify.\n'
        return {p.name: int(changed) for p in Path(root, 'evals').glob('rsi-debug-*')}

    def draft(self, evaluator=None):
        with mock.object(patch, 'run_eval', side_effect=evaluator or self.evaluate):
            result = patch._evaluate('debug', 'diagnosis', 'Reproduce and verify.\n', 'Fix observed failure',
                                     [{'prompt': 'Debug the failure', 'should_fire': True, 'reply_regex': ''}],
                                     ['Please reproduce this failure.'])
        return store.read_json(paths.path('proposals', result['proposed'] + '.json'))

    def test_worktree_evaluates_dirty_untracked_and_deleted_runtime_without_committing_it(self):
        self.write('honey/runtime.py', 'current = True\n')
        self.write('honey/new.py', 'new = True\n')
        (self.root / 'hooks/remove.py').unlink()
        self.write('honey/__pycache__/ignored.pyc', 'cached')
        def evaluate(root, pattern, out):
            self.assertEqual(Path(root, 'honey/runtime.py').read_text(), 'current = True\n')
            self.assertEqual(Path(root, 'honey/new.py').read_text(), 'new = True\n')
            self.assertFalse(Path(root, 'hooks/remove.py').exists())
            self.assertFalse(Path(root, 'honey/__pycache__/ignored.pyc').exists())
            return self.evaluate(root, pattern, out)
        p = self.draft(evaluate)
        self.assertTrue(p.get('source_snapshot'))
        self.assertEqual(self.git('show', p['branch'] + ':honey/runtime.py'), 'old = True')
        with mock('honey.install.sync', return_value=0):
            patch.accept(p)
        self.assertEqual((self.root / 'honey/runtime.py').read_text(), 'current = True\n')
        self.assertEqual((self.root / 'honey/new.py').read_text(), 'new = True\n')
        self.assertFalse((self.root / 'hooks/remove.py').exists())

    def test_runtime_drift_after_evaluation_blocks_application(self):
        p = self.draft()
        self.write('honey/runtime.py', 'changed_after_evaluation = True\n')
        with mock('honey.install.sync', return_value=0) as sync:
            with self.assertRaisesRegex(ValueError, 'runtime.*changed|snapshot'):
                patch.accept(p)
        sync.assert_not_called()
        self.assertEqual(self.git('rev-parse', 'HEAD'), self.before)

    def test_runtime_drift_blocks_sync_retry(self):
        p = self.draft()
        with mock('honey.install.sync', return_value=1):
            with self.assertRaises(RuntimeError):
                patch.accept(p)
        self.write('honey/runtime.py', 'changed_after_merge = True\n')
        with mock('honey.install.sync', return_value=0) as sync:
            with self.assertRaisesRegex(ValueError, 'runtime.*changed|snapshot'):
                patch.accept(p)
        sync.assert_not_called()

    def test_legacy_proposal_blocks_dirty_runtime(self):
        p = self.draft()
        p.pop('source_snapshot', None)
        self.write('honey/runtime.py', 'dirty = True\n')
        with mock('honey.install.sync', return_value=0) as sync:
            with self.assertRaisesRegex(ValueError, 'runtime|snapshot'):
                patch.accept(p)
        sync.assert_not_called()

    def test_legacy_proposal_allows_unrelated_docs(self):
        p = self.draft()
        p.pop('source_snapshot', None)
        self.write('docs/notes.md', 'Keep my notes\n')
        with mock('honey.install.sync', return_value=0):
            patch.accept(p)
        self.assertEqual((self.root / 'docs/notes.md').read_text(), 'Keep my notes\n')


    def test_evaluator_runtime_mutation_is_not_accepted_as_snapshot_proof(self):
        def evaluate(root, pattern, out):
            Path(root, 'honey/runtime.py').write_text('modified_during_eval = True\n')
            return self.evaluate(root, pattern, out)
        with self.assertRaisesRegex(ValueError, 'runtime.*changed|snapshot'):
            self.draft(evaluate)
        self.assertEqual(self.git('rev-parse', 'HEAD'), self.before)
        self.assertFalse(list((self.root / '.worktrees').glob('*')))


if __name__ == '__main__': unittest.main()
