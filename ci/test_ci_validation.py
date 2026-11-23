import unittest

from ci_validation import COMPONENTS, failures_for


def needs_for(selected):
    needs = {key: {'result': result} for key, result in {
        'changes': 'success', 'platform-gates': 'success',
        'delivery-checks': 'success' if selected else 'skipped',
        'integration': 'success' if len(selected) == 2 else 'skipped',
        **{f'{component}-{suffix}': 'success' if component in selected else 'skipped'
           for component in COMPONENTS for suffix in ('test', 'image')},
    }.items()}
    needs['changes']['outputs'] = {component: str(component in selected).lower()
                                   for component in COMPONENTS}
    needs['changes']['outputs']['code'] = str(bool(selected)).lower()
    return needs


class CIValidationTests(unittest.TestCase):
    def test_docs_single_and_both_ignore_release_failures(self):
        for selected in ((), ('frontend',), ('backend',), COMPONENTS):
            with self.subTest(selected=selected):
                needs = needs_for(selected)
                needs['publish-frontend'] = {'result': 'failure'}
                needs['deploy-backend'] = {'result': 'cancelled'}
                self.assertEqual(failures_for(needs), [])

    def test_each_required_check_is_fail_closed(self):
        for job in needs_for(COMPONENTS):
            for broken in ('failure', 'skipped', 'cancelled', 'missing'):
                with self.subTest(job=job, broken=broken):
                    needs = needs_for(COMPONENTS)
                    if broken == 'missing':
                        del needs[job]
                    else:
                        needs[job]['result'] = broken
                    self.assertIn(job, ' '.join(failures_for(needs)))

    def test_rejects_bad_selection(self):
        needs = needs_for(('frontend',))
        needs['changes']['outputs']['code'] = 'false'
        self.assertIn('Inconsistent component selection', failures_for(needs))
        del needs['changes']['outputs']['backend']
        self.assertIn('Missing or invalid component selection', failures_for(needs))
