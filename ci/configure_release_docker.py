"""Configure the ephemeral publisher runner before loading verified images."""
import argparse
import json
from pathlib import Path


def configure(path):
    path = Path(path)
    config = json.loads(path.read_text(encoding='utf-8')) if path.exists() else {}
    if not isinstance(config, dict):
        raise ValueError('Docker daemon configuration must be a JSON object')
    config['max-concurrent-uploads'] = 1
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(config, indent=2) + '\n', encoding='utf-8')


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--config', required=True)
    args = parser.parse_args()
    configure(args.config)
    print('Publisher Docker upload concurrency configured: 1 layer at a time.')


if __name__ == '__main__':
    main()
