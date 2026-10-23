"""Offline regression checks: no SSH, Docker daemon or real credentials."""

import io
import json
import os
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch

import yaml

from sync_runtime_env import AI_KEYS, apply_remote, merge_env, sync


ROOT = Path(__file__).resolve().parents[1]
VALUES = {'LLM_API_KEY': 'fake-$KEY#only', 'LLM_BASE_URL': 'https://example.invalid/v1',
          'LLM_MODEL': 'test-model', 'ENABLE_TTS': 'True'}


class MergeTests(unittest.TestCase):
    def test_only_ai_keys_change_and_merge_is_idempotent(self):
        host = b'# host settings\r\nSECRET_KEY="host-secret"\r\nDATABASE_PASSWORD=host-only\r\nWEB_PORT=127.0.0.1:48080\r\nCUSTOM_FLAG=keep\r\n'
        original = host + b'LLM_API_KEY=old\r\n'
        merged = merge_env(original, VALUES)
        self.assertTrue(merged.startswith(host))
        self.assertIn(b"LLM_API_KEY='fake-$KEY#only'\r\n", merged)
        self.assertNotIn(b'LLM_API_KEY=old', merged)
        self.assertEqual(merge_env(merged, VALUES), merged)

    def test_missing_optional_values_preserve_existing_server_settings(self):
        original = b'ASR_API_KEY=server-asr\nENABLE_TTS=False\n'
        values = {k: v for k, v in VALUES.items() if k != 'ENABLE_TTS'}
        self.assertTrue(merge_env(original, values).startswith(original))

    def test_rejects_protected_keys_injection_duplicates_and_multiline(self):
        cases = [
            (b'SECRET_KEY=keep\n', {**VALUES, 'SECRET_KEY': 'overwrite'}),
            (b'', {**VALUES, 'LLM_API_KEY': 'bad\nSECRET_KEY=overwrite'}),
            (b'', {**VALUES, 'LLM_API_KEY': "bad'quote"}),
            (b'', {**VALUES, 'LLM_API_KEY': 'bad\\escape'}),
            (b'', {**VALUES, 'LLM_API_KEY': ''}),
            (b'LLM_MODEL=a\nexport LLM_MODEL=b\n', VALUES),
            (b'PRIVATE="first\nLLM_MODEL=inside\nlast"\n', VALUES),
        ]
        for original, values in cases:
            with self.subTest(original=original), self.assertRaises(ValueError):
                merge_env(original, values)

    def test_export_and_comments_and_quoted_host_values(self):
        original = b"# comment\nOTHER='host # value' # trailing\nexport LLM_MODEL=old\n"
        self.assertIn(b"OTHER='host # value' # trailing\n", merge_env(original, VALUES))
        self.assertIn(b"LLM_MODEL='test-model'\n", merge_env(original, VALUES))


class TransportTests(unittest.TestCase):
    def test_verified_ssh_and_secrets_only_in_stdin_with_private_temporary_files(self):
        environment = {**VALUES, 'DEPLOY_SSH_HOST': 'server.invalid', 'DEPLOY_SSH_PORT': '2222',
                       'DEPLOY_SSH_USER': 'deployer', 'DEPLOY_ENV_PATH': '/srv/career/.env',
                       'DEPLOY_SSH_KEY': 'fake-private-key', 'DEPLOY_SSH_KNOWN_HOSTS': 'fake-known-host'}
        def run(command, **kwargs):
            self.assertIn('StrictHostKeyChecking=yes', command)
            self.assertIn('IdentitiesOnly=yes', command)
            self.assertIn('/dev/null', command)
            self.assertNotIn(VALUES['LLM_API_KEY'], ' '.join(command))
            self.assertEqual(json.loads(kwargs['input']), VALUES)
            key = Path(command[command.index('-i') + 1])
            self.assertEqual(key.read_text().strip(), 'fake-private-key')
            if os.name != 'nt':
                self.assertEqual(key.stat().st_mode & 0o777, 0o600)
            return subprocess.CompletedProcess(command, 0)
        with patch.dict(os.environ, environment, clear=True), patch('sync_runtime_env.subprocess.run', side_effect=run), patch('sys.stdout', new_callable=io.StringIO):
            sync()

    def test_missing_secrets_fail_before_network(self):
        with patch.dict(os.environ, {}, clear=True), patch('sync_runtime_env.subprocess.run') as run:
            with self.assertRaises(ValueError):
                sync()
            run.assert_not_called()


@unittest.skipIf(os.name == 'nt', 'Remote atomic update requires Linux fcntl and POSIX permissions')
class RemoteTests(unittest.TestCase):
    def test_symlink_and_public_permissions_are_rejected_without_compose(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / '.env'
            original = b'SECRET_KEY=host-only\n'
            path.write_bytes(original)
            path.chmod(0o644)
            (path.parent / 'docker-compose.yml').write_text('services: {}')
            with patch('sync_runtime_env.compose_run') as compose:
                with self.assertRaises(ValueError):
                    apply_remote(str(path), VALUES)
                path.rename(path.parent / 'actual-env')
                path.symlink_to(path.parent / 'actual-env')
                with self.assertRaises(ValueError):
                    apply_remote(str(path), VALUES)
                compose.assert_not_called()
            self.assertEqual(path.read_bytes(), original)

    def test_activation_failure_keeps_new_env_and_reports_failure(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / '.env'
            path.write_bytes(b'SECRET_KEY=host-only\n')
            path.chmod(0o600)
            (path.parent / 'docker-compose.yml').write_text('services: {}')
            def compose(command, **kwargs):
                if 'config' in command:
                    return {'services': {'backend': {'environment': VALUES}}}
                if 'up' in command:
                    raise RuntimeError('fake unhealthy service')
            with patch('sync_runtime_env.compose_run', side_effect=compose), self.assertRaises(RuntimeError):
                apply_remote(str(path), VALUES)
            self.assertIn(b'SECRET_KEY=host-only\n', path.read_bytes())
            self.assertIn(b"LLM_MODEL='test-model'", path.read_bytes())
            self.assertFalse(list(path.parent.glob('.ai-env-*')))

    def test_validate_pull_replace_recreate_and_preserve_host_values(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / '.env'
            path.write_bytes(b'SECRET_KEY=host-only\nDATABASE_PASSWORD=keep\n')
            path.chmod(0o600)
            (path.parent / 'docker-compose.yml').write_text('services: {}')
            calls = []
            def compose(command, **kwargs):
                calls.append(command)
                if 'config' in command:
                    return {'services': {'backend': {'environment': VALUES}}}
                if 'pull' in command:
                    self.assertEqual(path.read_bytes(), b'SECRET_KEY=host-only\nDATABASE_PASSWORD=keep\n')
                if 'up' in command:
                    self.assertIn(b"LLM_MODEL='test-model'", path.read_bytes())
            with patch('sync_runtime_env.compose_run', side_effect=compose):
                apply_remote(str(path), VALUES)
            self.assertEqual(len(calls), 3)
            self.assertIn('--wait', calls[-1])
            self.assertEqual(path.stat().st_mode & 0o777, 0o600)
            self.assertFalse(list(path.parent.glob('.ai-env-*')))

    def test_invalid_compose_or_pull_failure_preserves_original_and_removes_candidate(self):
        for failure in ('mapping', 'pull'):
            with self.subTest(failure=failure), tempfile.TemporaryDirectory() as directory:
                path = Path(directory) / '.env'
                original = b'SECRET_KEY=keep\n'
                path.write_bytes(original)
                path.chmod(0o600)
                (path.parent / 'docker-compose.yml').write_text('services: {}')
                def compose(command, **kwargs):
                    if 'config' in command:
                        return {'services': {'backend': {'environment': {} if failure == 'mapping' else VALUES}}}
                    raise RuntimeError('fake pull failure')
                with patch('sync_runtime_env.compose_run', side_effect=compose), self.assertRaises((ValueError, RuntimeError)):
                    apply_remote(str(path), VALUES)
                self.assertEqual(path.read_bytes(), original)
                self.assertFalse(list(path.parent.glob('.ai-env-*')))


class WorkflowTests(unittest.TestCase):
    def test_sync_is_gated_after_publication_and_uses_secret_connection_fields(self):
        workflow = yaml.safe_load((ROOT / '.github/workflows/ci-cd.yml').read_text())
        job = workflow['jobs']['sync-runtime-env']
        self.assertEqual(job['needs'], ['publish'])
        self.assertIn("needs.publish.result == 'success'", job['if'])
        self.assertIn("refs/heads/master", job['if'])
        self.assertIn("vars.DEPLOY_ENV_SYNC_ENABLED == 'true'", job['if'])
        step = job['steps'][-1]
        for name in ('DEPLOY_SSH_HOST', 'DEPLOY_SSH_USER', 'DEPLOY_SSH_PORT', 'DEPLOY_ENV_PATH', 'DEPLOY_SSH_KEY', 'DEPLOY_SSH_KNOWN_HOSTS'):
            self.assertEqual(step['env'][name], '${{ secrets.' + name + ' }}')
        self.assertEqual(set(AI_KEYS) - set(step['env']), set())
        compose = yaml.safe_load((ROOT / 'deploy/docker-compose.yml').read_text())
        self.assertTrue(set(AI_KEYS).issubset(compose['services']['backend']['environment']))


if __name__ == '__main__':
    unittest.main()
