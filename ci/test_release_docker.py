import json
from pathlib import Path
import tempfile
import unittest

from configure_release_docker import configure


class PublisherDockerTests(unittest.TestCase):
    def test_existing_runner_options_are_preserved_and_reruns_are_idempotent(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / 'daemon.json'
            path.write_text(json.dumps({'debug': False, 'features': {'buildkit': True},
                                        'max-concurrent-uploads': 5}), encoding='utf-8')
            configure(path)
            configure(path)
            self.assertEqual(json.loads(path.read_text(encoding='utf-8')),
                             {'debug': False, 'features': {'buildkit': True}, 'max-concurrent-uploads': 1})

    def test_absent_runner_configuration_is_created(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / 'docker' / 'daemon.json'
            configure(path)
            self.assertEqual(json.loads(path.read_text(encoding='utf-8')), {'max-concurrent-uploads': 1})

    def test_malformed_configuration_is_not_overwritten(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / 'daemon.json'
            for content in ('{broken', '[]', 'null'):
                path.write_text(content, encoding='utf-8')
                with self.subTest(content=content), self.assertRaises(ValueError):
                    configure(path)
                self.assertEqual(path.read_text(encoding='utf-8'), content)
