import copy
import unittest

from tencent_pilot_gate import GATE_NAME, REPOSITORY, WORKFLOW_ID, verify_ci_job, verify_run

SHA = 'a' * 40
RUN_ID = 12345
GOOD = dict(id=RUN_ID, workflow_id=WORKFLOW_ID, head_branch='master', head_sha=SHA,
            event='push', status='completed', conclusion='success', run_attempt=2,
            repository={'full_name': REPOSITORY}, head_repository={'full_name': REPOSITORY})


class TencentPilotGateTest(unittest.TestCase):
    def test_success(self):
        verify_run(GOOD, RUN_ID, SHA)

    def test_rejects_each_wrong_field(self):
        for key, value in dict(id=9, workflow_id=8, head_branch='feature', head_sha='b' * 40,
                               event='pull_request', status='in_progress',
                               repository=None, head_repository={'full_name': 'other/fork'}).items():
            with self.subTest(key=key), self.assertRaisesRegex(ValueError, key):
                run = copy.deepcopy(GOOD)
                run[key] = value
                verify_run(run, RUN_ID, SHA)

    def test_publish_failure_does_not_mask_ci_success(self):
        run = dict(GOOD, conclusion='failure')
        verify_run(run, RUN_ID, SHA)
        gate = dict(name=GATE_NAME, run_id=RUN_ID, head_sha=SHA, run_attempt=2,
                    status='completed', conclusion='success')
        jobs = [gate, dict(name='Publish verified frontend image', conclusion='failure')]
        verify_ci_job(run, dict(total_count=2, jobs=jobs))

    def test_rejects_missing_duplicate_stale_or_failed_ci_and_cancelled_run(self):
        gate = dict(name=GATE_NAME, run_id=RUN_ID, head_sha=SHA, run_attempt=2,
                    status='completed', conclusion='success')
        for jobs in ([], [gate, gate], [dict(gate, run_attempt=1)],
                     [dict(gate, conclusion='failure')], [dict(gate, head_sha='b' * 40)]):
            with self.subTest(jobs=jobs), self.assertRaises(ValueError):
                verify_ci_job(GOOD, dict(total_count=len(jobs), jobs=jobs))
        with self.assertRaises(ValueError):
            verify_ci_job(dict(GOOD, conclusion='cancelled'), dict(total_count=1, jobs=[gate]))
        with self.assertRaises(ValueError):
            verify_ci_job(GOOD, dict(total_count=2, jobs=[gate]))
