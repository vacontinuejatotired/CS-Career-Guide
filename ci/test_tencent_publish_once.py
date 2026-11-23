import os
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import Mock

from tencent_pilot_gate import GATE_NAME
from tencent_publish_once import candidate, publish
from test_tencent_pilot_gate import GOOD, RUN_ID, SHA


class TencentPublishOnceTest(unittest.TestCase):
    def select(self, front='success', back='success', **overrides):
        run = dict(GOOD, **overrides)
        gate = dict(name=GATE_NAME, run_id=RUN_ID, run_attempt=2, head_sha=SHA,
                    status='completed', conclusion='success')
        rows = [gate, dict(gate, name='Frontend image', conclusion=front),
                dict(gate, name='Backend image', conclusion=back)]
        read = Mock(side_effect=[{'object': {'sha': SHA}}, {'workflow_runs': [run]}])
        detail = Mock(side_effect=[run, {'jobs': rows, 'total_count': len(rows)}, run])
        return candidate(read, detail)

    def test_only_selects_components_that_built(self):
        self.assertEqual(self.select(), (SHA, str(RUN_ID), 'all'))
        self.assertEqual(self.select(back='skipped'), (SHA, str(RUN_ID), 'frontend'))
        self.assertEqual(self.select(front='skipped'), (SHA, str(RUN_ID), 'backend'))
        self.assertIsNone(self.select('skipped', 'skipped'))
        self.assertIsNone(self.select(status='in_progress'))

    def test_rejects_failure_wrong_event_or_different_sha(self):
        for kwargs in ({'front': 'failure'}, {'event': 'pull_request'}, {'head_sha': 'b' * 40}):
            with self.subTest(kwargs=kwargs), self.assertRaises(ValueError):
                self.select(**kwargs)

    @unittest.skipUnless(os.name == 'posix', 'POSIX receipt permissions')
    def test_successful_or_ambiguous_attempt_does_not_publish_twice(self):
        selection = (SHA, str(RUN_ID), 'frontend')
        for fails in (False, True):
            with self.subTest(fails=fails), tempfile.TemporaryDirectory() as directory:
                state = Path(directory) / 'state'
                runner = Mock(side_effect=subprocess.CalledProcessError(1, 'bash') if fails else None)
                if fails:
                    with self.assertRaises(subprocess.CalledProcessError):
                        publish(selection, state, runner)
                else:
                    publish(selection, state, runner)
                publish(selection, state, runner)
                self.assertEqual(runner.call_count, 1)
                self.assertEqual((state / SHA / 'published').exists(), not fails)
