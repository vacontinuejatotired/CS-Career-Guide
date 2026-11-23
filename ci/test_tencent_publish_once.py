import json
import os
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import Mock

from tencent_pilot_gate import GATE_NAME
from tencent_publish_once import TCR, candidate, publish, verified_images
from test_tencent_pilot_gate import GOOD, RUN_ID, SHA

FRONT = f'{TCR}/frontend-pilot@sha256:' + 'a' * 64
BACK = f'{TCR}/backend-pilot@sha256:' + 'b' * 64


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
                def run(_command, *, check, env):
                    self.assertTrue(check)
                    Path(env['CS_CAREER_TCR_RECEIPT_FILE']).write_text(f'frontend {FRONT}\n', encoding='ascii')
                    if fails:
                        raise subprocess.CalledProcessError(1, 'bash')

                runner = Mock(side_effect=run)
                if fails:
                    with self.assertRaises(subprocess.CalledProcessError):
                        publish(selection, state, runner)
                else:
                    publish(selection, state, runner)
                publish(selection, state, runner)
                self.assertEqual(runner.call_count, 1)
                receipt = state / SHA / 'published'
                self.assertEqual(receipt.exists(), not fails)
                if not fails:
                    self.assertEqual(json.loads(receipt.read_text(encoding='ascii')),
                                     {'sha': SHA, 'run_id': RUN_ID, 'images': {'frontend': FRONT}})

    def test_receipt_requires_exact_component_set_and_digest(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'images'
            good = f'frontend {FRONT}\nbackend {BACK}\n'
            path.write_text(good, encoding='ascii')
            self.assertEqual(verified_images(path, 'all'), {'frontend': FRONT, 'backend': BACK})
            for invalid in (f'frontend {FRONT}\n', f'backend {FRONT}\nfrontend {FRONT}\n',
                            good + f'backend {BACK}\n', good.replace(TCR, 'other/repository')):
                with self.subTest(invalid=invalid), self.assertRaises(ValueError):
                    path.write_text(invalid, encoding='ascii')
                    verified_images(path, 'all')
