"""Verify publication gates and failure handling without Docker or registry access."""

import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import yaml

from release_images import coordinates, export_image, load_verified_images, publish_images, push_digest, source_image

COMMIT = '1' * 40
IDS = {'backend': 'sha256:' + 'a' * 64, 'frontend': 'sha256:' + 'b' * 64}
MANIFESTS = {'backend': 'sha256:' + 'c' * 64, 'frontend': 'sha256:' + 'd' * 64}


class ReleaseImageTests(unittest.TestCase):
    def artifacts(self, root):
        for component, image_id in IDS.items():
            (root / f'{component}-image.tar').write_bytes(b'synthetic-unit-test-archive')
            metadata = {'component': component, 'commit': COMMIT,
                        'source_image': source_image(component, COMMIT),
                        'image_id': image_id, 'platform': 'linux/amd64'}
            (root / f'{component}-image.json').write_text(json.dumps(metadata), encoding='utf-8')

    def fake_docker(self, calls, *, fail_frontend=False, wrong_image=False, wrong_latest=False):
        def run(*arguments):
            calls.append(arguments)
            if arguments[:2] == ('image', 'inspect'):
                component = 'backend' if 'backend' in arguments[-1] else 'frontend'
                image_id = IDS['frontend'] if wrong_image and component == 'backend' else IDS[component]
                return json.dumps([{'Id': image_id, 'Os': 'linux', 'Architecture': 'amd64'}])
            if arguments[0] == 'push':
                component = 'backend' if 'backend:' in arguments[1] else 'frontend'
                if fail_frontend and component == 'frontend':
                    raise RuntimeError('Synthetic registry rejection.')
                digest = MANIFESTS[component]
                if wrong_latest and arguments[1].endswith(':latest'):
                    digest = 'sha256:' + 'e' * 64
                return f'{arguments[1].rsplit(":", 1)[1]}: digest: {digest} size: 1234\n'
            return ''
        return run

    def test_configuration_rejects_malformed_coordinates_and_tags(self):
        expected = coordinates('registry.example', 'demo', COMMIT, 'release-1')
        self.assertEqual(expected['backend'], 'registry.example/demo/cs-career-guide-backend')
        for registry, namespace, tag in [
            ('https://registry.example', 'demo', ''), ('registry.example/path', 'demo', ''),
            ('registry.example', 'UpperCase', ''), ('registry.example', 'demo', '.bad'),
            ('registry.example', 'demo', '$(command)'), ('', 'demo', ''),
        ]:
            with self.subTest(registry=registry, namespace=namespace, tag=tag), self.assertRaises(ValueError):
                coordinates(registry, namespace, COMMIT, tag)

    def test_export_records_inspected_image_identity(self):
        calls = []
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            with patch('release_images.docker', side_effect=self.fake_docker(calls)), patch('builtins.print'):
                export_image(root, 'backend', COMMIT)
            metadata = json.loads((root / 'backend-image.json').read_text(encoding='utf-8'))
            self.assertEqual(metadata['image_id'], IDS['backend'])
            self.assertEqual(metadata['commit'], COMMIT)
            self.assertEqual(calls[-1], ('save', '--output', str(root / 'backend-image.tar'), source_image('backend', COMMIT)))

    def test_wrong_commit_is_rejected_before_any_docker_operation(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.artifacts(root)
            metadata = json.loads((root / 'frontend-image.json').read_text(encoding='utf-8'))
            metadata['commit'] = '2' * 40
            (root / 'frontend-image.json').write_text(json.dumps(metadata), encoding='utf-8')
            with patch('release_images.docker') as runner, self.assertRaisesRegex(RuntimeError, 'identity'):
                load_verified_images(root, COMMIT)
            runner.assert_not_called()

    def test_loaded_image_mismatch_prevents_all_pushes(self):
        calls = []
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.artifacts(root)
            with patch('release_images.docker', side_effect=self.fake_docker(calls, wrong_image=True)):
                with self.assertRaisesRegex(RuntimeError, 'Loaded image ID'):
                    publish_images(root, 'registry.example', 'demo', COMMIT, '', root / 'release.json', root / 'summary.md')
        self.assertFalse(any(command[0] in ('push', 'tag') for command in calls))

    def test_success_publishes_both_versions_before_latest_and_records_digests(self):
        calls = []
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.artifacts(root)
            with patch('release_images.docker', side_effect=self.fake_docker(calls)), patch('builtins.print'):
                publish_images(root, 'registry.example', 'demo', COMMIT, 'release-1', root / 'release.json', root / 'summary.md')
            record = json.loads((root / 'release.json').read_text(encoding='utf-8'))
            self.assertTrue(record['complete'])
            for component in IDS:
                self.assertEqual(record['images'][component]['image_id'], IDS[component])
                self.assertEqual(record['images'][component]['reference'],
                                 f'registry.example/demo/cs-career-guide-{component}@{MANIFESTS[component]}')
        pushes = [command[1] for command in calls if command[0] == 'push']
        self.assertEqual([reference.rsplit(':', 1)[1] for reference in pushes],
                         ['sha-1111111', 'sha-1111111', 'release-1', 'release-1', 'latest', 'latest'])
        self.assertTrue(all(command[1] in IDS.values() for command in calls if command[0] == 'tag'))
        self.assertFalse(any(command[0] == 'build' for command in calls))

    def test_failed_version_push_does_not_advance_latest_and_records_partial_state(self):
        calls = []
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.artifacts(root)
            with patch('release_images.docker', side_effect=self.fake_docker(calls, fail_frontend=True)), patch('builtins.print'):
                with self.assertRaisesRegex(RuntimeError, 'Synthetic registry rejection'):
                    publish_images(root, 'registry.example', 'demo', COMMIT, '', root / 'release.json', root / 'summary.md')
            record = json.loads((root / 'release.json').read_text(encoding='utf-8'))
            self.assertFalse(record['complete'])
            self.assertEqual(record['images']['backend']['digest'], MANIFESTS['backend'])
            self.assertNotIn('digest', record['images']['frontend'])
            self.assertIn('Partial or failed', (root / 'summary.md').read_text(encoding='utf-8'))
        self.assertFalse(any(command[0] == 'push' and command[1].endswith(':latest') for command in calls))

    def test_digest_change_cannot_be_reported_as_a_complete_release(self):
        calls = []
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.artifacts(root)
            with patch('release_images.docker', side_effect=self.fake_docker(calls, wrong_latest=True)), patch('builtins.print'):
                with self.assertRaisesRegex(RuntimeError, 'different manifest digests'):
                    publish_images(root, 'registry.example', 'demo', COMMIT, '', root / 'release.json', root / 'summary.md')
            self.assertFalse(json.loads((root / 'release.json').read_text(encoding='utf-8'))['complete'])

    def test_ambiguous_or_missing_push_digest_is_rejected(self):
        self.assertEqual(push_digest('latest: digest: ' + MANIFESTS['backend'] + ' size: 123'), MANIFESTS['backend'])
        for output in ('no digest reported', f"digest: {MANIFESTS['backend']} digest: {MANIFESTS['frontend']}"):
            with self.subTest(output=output), self.assertRaises(RuntimeError):
                push_digest(output)


class WorkflowGateTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        path = Path(__file__).resolve().parents[1] / '.github' / 'workflows' / 'ci-cd.yml'
        cls.workflow = yaml.safe_load(path.read_text(encoding='utf-8'))

    def test_publisher_requires_both_quality_and_image_jobs(self):
        publisher = self.workflow['jobs']['publish']
        self.assertTrue({'backend-test', 'frontend-test', 'backend-image', 'frontend-image'}.issubset(publisher['needs']))

    def test_publication_guard_rejects_feature_branches_prs_other_repositories_and_false_intent(self):
        expression = self.workflow['jobs']['publish']['if']
        cases = [
            ('true', 'refs/heads/master', 'vacontinuejatotired/CS-Career-Guide', 'push', True),
            ('true', 'refs/heads/master', 'vacontinuejatotired/CS-Career-Guide', 'workflow_dispatch', True),
            ('true', 'refs/heads/feature', 'vacontinuejatotired/CS-Career-Guide', 'push', False),
            ('true', 'refs/heads/master', 'vacontinuejatotired/CS-Career-Guide', 'pull_request', False),
            ('true', 'refs/heads/master', 'other/CS-Career-Guide', 'push', False),
            ('false', 'refs/heads/master', 'vacontinuejatotired/CS-Career-Guide', 'push', False),
        ]
        for intent, ref, repository, event, expected in cases:
            translated = expression
            for key, value in {'needs.changes.outputs.publish': intent, 'github.ref': ref,
                               'github.repository': repository, 'github.event_name': event}.items():
                translated = translated.replace(key, repr(value))
            translated = translated.replace('&&', 'and').replace('||', 'or')
            with self.subTest(ref=ref, repository=repository, event=event, intent=intent):
                self.assertEqual(eval(translated, {'__builtins__': {}}, {}), expected)

    def test_image_jobs_always_load_and_test_without_registry_credentials(self):
        for name in ('backend-image', 'frontend-image'):
            job = self.workflow['jobs'][name]
            builds = [step for step in job['steps'] if step.get('uses', '').startswith('docker/build-push-action@')]
            self.assertEqual(len(builds), 1)
            self.assertIs(builds[0]['with']['push'], False)
            self.assertIs(builds[0]['with']['load'], True)
            self.assertNotIn('secrets.', json.dumps(job))
            for step in job['steps']:
                if step.get('name') in ('Smoke test validated image', 'Test real demo integration and SQLite persistence'):
                    self.assertNotIn('if', step)
            self.assertTrue(any('Smoke test validated image' == step.get('name') for step in job['steps']))
        backend = self.workflow['jobs']['backend-image']
        self.assertTrue(any(step.get('name') == 'Test real demo integration and SQLite persistence' for step in backend['steps']))

    def test_secrets_fallback_is_confined_to_publisher_and_artifacts_are_consumed(self):
        publisher = self.workflow['jobs']['publish']
        for name in ('ACR_REGISTRY', 'ACR_NAMESPACE'):
            self.assertEqual(publisher['env'][name], '${{ vars.' + name + ' || secrets.' + name + ' }}')
        downloads = [step for step in publisher['steps'] if step.get('uses', '').startswith('actions/download-artifact@')]
        self.assertEqual(len(downloads), 2)
        self.assertFalse(any(step.get('uses', '').startswith('docker/build-push-action@') for step in publisher['steps']))


if __name__ == '__main__':
    unittest.main()
