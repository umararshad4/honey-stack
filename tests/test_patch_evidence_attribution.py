"""Patch drafting cannot launder uncertain or unrelated feedback into evidence."""
import os
import tempfile
import unittest
from unittest.mock import patch as mock

from helpers import REPO
from honey import paths
from honey.rsi import patch, review, store


class PatchAttribution(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        context = mock.dict(os.environ, HONEY_HOME=self.temp.name)
        context.start(); self.addCleanup(context.stop)

    def event(self, **kwargs):
        return dict(event='prompt', origin='user', quarantined=False,
                    q='The debug skill failed to reproduce the problem', **kwargs)

    def test_feedback_record_requires_confident_matching_behavior(self):
        for annotation in ({'attribution': 'uncertain', 'feedback_kind': 'behavior', 'attributed_skill': 'debug'},
                           {'attribution': 'explicit', 'feedback_kind': 'behavior', 'attributed_skill': 'verify'},
                           {'attribution': 'explicit', 'feedback_kind': 'requirement', 'attributed_skill': 'debug'}):
            store.write_jsonl(paths.path('skill-feedback.jsonl'), [{'skill': 'debug', 'outcome': 'failed',
                                                                  'evidence': [self.event(**annotation)]}])
            self.assertEqual(patch.evidence_for('debug'), [])
        store.write_jsonl(paths.path('skill-feedback.jsonl'), [{'skill': 'debug', 'outcome': 'failed', 'evidence': [
            self.event(attribution='single-task', feedback_kind='behavior', attributed_skill='debug')]}])
        self.assertEqual(len(patch.evidence_for('debug')), 1)

    def test_nearby_prompt_is_not_evidence_for_a_different_task(self):
        store.write_jsonl(paths.path('events', '2026-10', 'session.jsonl'), [
            {'e': 'skill_outcome', 'name': 'debug', 'outcome': 'neg', 't': 1},
            {'e': 'prompt', 'origin': 'user', 'q': 'Add an export button', 't': 2,
             'feedback_kind': 'requirement', 'attribution': 'uncertain'}])
        self.assertEqual(patch.evidence_for('debug'), [])

    def test_pending_toolkit_diagnosis_retains_attribution(self):
        review.add(1, 'toolkit_fix', 'debug skill: failure', 'failure', 'investigate', [
            self.event(attribution='uncertain', feedback_kind='behavior', attributed_skill='debug')], 'uncertain')
        self.assertEqual(patch.evidence_for('debug'), [])


if __name__ == '__main__': unittest.main()
