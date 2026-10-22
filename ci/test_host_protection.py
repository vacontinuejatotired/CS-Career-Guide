"""Reject host-dangerous runtime settings and regressions in the demo sandbox."""

from pathlib import Path
import unittest

import yaml

from host_protection import verify_sandbox


def sandbox_state(service='backend'):
    return {
        'user': '10001:10001',
        'host': {
            'ReadonlyRootfs': True, 'Privileged': False, 'Init': True,
            'NetworkMode': 'demo-net', 'CapDrop': ['ALL'], 'CapAdd': None,
            'SecurityOpt': ['no-new-privileges:true'],
            'Memory': 512 * 1024 * 1024, 'MemorySwap': 512 * 1024 * 1024,
            'NanoCpus': 500000000, 'PidsLimit': 128,
            'LogConfig': {'Type': 'local', 'Config': {'max-size': '5m', 'max-file': '3'}},
            'Devices': [], 'PortBindings': {} if service == 'backend' else {
                '8080/tcp': [{'HostIp': '127.0.0.1', 'HostPort': '18080'}]},
        },
        'mounts': [{'Type': 'volume', 'Destination': '/data', 'RW': True}]
        if service == 'backend' else [{'Type': 'volume', 'Destination': '/var/www/media', 'RW': False}],
    }


class RunningSandboxTests(unittest.TestCase):
    def test_expected_backend_and_frontend_sandboxes_are_accepted(self):
        for service in ('backend', 'frontend'):
            verify_sandbox(service, sandbox_state(service))

    def test_host_privileges_or_missing_resource_bounds_are_rejected(self):
        for field, value in (
            ('Privileged', True), ('ReadonlyRootfs', False), ('Init', False),
            ('NetworkMode', 'host'), ('CapDrop', []), ('CapAdd', ['SYS_ADMIN']),
            ('SecurityOpt', []), ('Memory', 0), ('MemorySwap', -1),
            ('NanoCpus', 0), ('PidsLimit', 0), ('Devices', [{'PathOnHost': '/dev/sda'}]),
            ('LogConfig', {'Type': 'json-file', 'Config': {}}),
        ):
            state = sandbox_state()
            state['host'][field] = value
            with self.subTest(field=field), self.assertRaises(RuntimeError):
                verify_sandbox('backend', state)

    def test_root_user_host_bind_mount_and_writable_frontend_data_are_rejected(self):
        cases = [('backend', sandbox_state()), ('backend', sandbox_state()), ('frontend', sandbox_state('frontend'))]
        cases[0][1]['user'] = '0:0'
        cases[1][1]['mounts'] = [{'Type': 'bind', 'Destination': '/data', 'RW': True}]
        cases[2][1]['mounts'][0]['RW'] = True
        for service, state in cases:
            with self.subTest(service=service, state=state), self.assertRaises(RuntimeError):
                verify_sandbox(service, state)

    def test_public_binding_or_published_backend_port_is_rejected(self):
        for service in ('backend', 'frontend'):
            state = sandbox_state(service)
            state['host']['PortBindings'] = {'8080/tcp': [{'HostIp': '0.0.0.0', 'HostPort': '18080'}]}
            with self.subTest(service=service), self.assertRaises(RuntimeError):
                verify_sandbox(service, state)


class ComposeSandboxTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.root = Path(__file__).resolve().parents[1]
        cls.services = yaml.safe_load((cls.root / 'deploy/docker-compose.yml').read_text(encoding='utf-8'))['services']

    def test_docker_socket_is_confined_to_an_explicit_updates_profile(self):
        self.assertEqual(self.services['watchtower']['profiles'], ['updates'])
        for name in ('backend', 'frontend', 'mysql'):
            service = self.services[name]
            self.assertNotIn('docker.sock', str(service))
            self.assertFalse(service.get('privileged', False))
            self.assertNotIn('host', [service.get('network_mode'), service.get('pid')])

    def test_applications_have_only_named_data_volumes_and_bounded_tmpfs(self):
        for name in ('backend', 'frontend'):
            service = self.services[name]
            self.assertEqual(service['user'], '10001:10001')
            self.assertIs(service['read_only'], True)
            self.assertEqual(service['cap_drop'], ['ALL'])
            self.assertIn('no-new-privileges:true', service['security_opt'])
            self.assertGreater(service['pids_limit'], 0)
            for mount in service['volumes']:
                self.assertFalse(mount.startswith(('/', '.', '~')))
            for mount in service['tmpfs']:
                self.assertIn('size=', mount)
                self.assertIn('noexec', mount)
            self.assertEqual(service['mem_limit'], service['memswap_limit'])
            self.assertEqual(service['logging']['options'], {'max-size': '5m', 'max-file': '3'})
        self.assertEqual(self.services['frontend']['ports'], ['${WEB_PORT:-127.0.0.1:48080}:8080'])
        self.assertNotIn('ports', self.services['backend'])

    def test_frontend_image_runs_non_root_on_the_unprivileged_port(self):
        dockerfile = (self.root / 'Dockerfile.frontend').read_text(encoding='utf-8')
        nginx = (self.root / 'nginx.conf').read_text(encoding='utf-8')
        self.assertIn('USER 10001:10001', dockerfile)
        self.assertIn('EXPOSE 8080', dockerfile)
        self.assertIn('listen 8080;', nginx)


if __name__ == '__main__':
    unittest.main()
