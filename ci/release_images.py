"""Export verified images and publish those exact archives in the gated CI job."""

import argparse
import json
import os
import re
import subprocess
import tempfile
import time
from pathlib import Path

COMPONENTS = ('backend', 'frontend')
DIGEST = r'sha256:[0-9a-f]{64}'


def source_image(component, commit):
    if component not in COMPONENTS or not re.fullmatch(r'[0-9a-f]{40}', commit):
        raise ValueError('A supported component and full commit SHA are required.')
    return f'cs-career-guide-{component}:sha-{commit[:7]}'


def coordinates(registry, namespace, commit, extra_tag=''):
    source_image('backend', commit)
    if not registry or not re.fullmatch(r'[a-z0-9](?:[a-z0-9.-]*[a-z0-9])?(?::[0-9]+)?', registry):
        raise ValueError('ACR_REGISTRY must be a registry hostname without a URL scheme or path.')
    if not namespace or not re.fullmatch(r'[a-z0-9][a-z0-9-]*', namespace):
        raise ValueError('ACR_NAMESPACE must contain lowercase letters, digits or hyphens.')
    if extra_tag and not re.fullmatch(r'[A-Za-z0-9_][A-Za-z0-9._-]{0,127}', extra_tag):
        raise ValueError('extra_tag must be a valid Docker tag.')
    return {name: f'{registry}/{namespace}/cs-career-guide-{name}' for name in COMPONENTS}


DOCKER_TIMEOUTS = {'push': 900, 'load': 300, 'save': 300}
HEARTBEAT_SECONDS = 15
PUSH_IDLE_TIMEOUT = 180


class DockerTimeoutError(RuntimeError):
    """A Docker command exhausted its bounded execution budget."""


class PushDiagnostics:
    """Emit only a fixed vocabulary, never registry output, URLs or credentials."""
    def __init__(self):
        self.layers = {}
        self.errors = set()
        self.log_chars = 0
        self.pending = ''

    def consume(self, chunk):
        self.log_chars += len(chunk)
        text = self.pending + chunk
        lines = re.split(r'[\r\n]', text)
        self.pending = lines.pop()[-4096:]
        for line in lines:
            match = re.fullmatch(r'([a-f0-9]{12,64}): (Preparing|Waiting|Pushing|Pushed|Layer already exists|Retrying in \d+ seconds)(?:\s+.*)?', line)
            if match:
                state = match[2]
                self.layers[match[1]] = 'Retrying' if state.startswith('Retrying') else state
            lower = line.lower()
            for category, pattern in (
                ('network-timeout', r'timeout|timed out|deadline exceeded'),
                ('connection', r'connection reset|connection refused|unexpected eof|no such host'),
                ('authorization', r'unauthorized|authentication required|denied:'),
                ('rate-limit', r'too many requests|\b429\b'),
                ('registry-server', r'\b50[0-4]\b|internal server error|bad gateway'),
                ('tls', r'tls handshake|x509:'),
            ):
                if re.search(pattern, lower):
                    self.errors.add(category)

    def summary(self):
        counts = {state: list(self.layers.values()).count(state) for state in sorted(set(self.layers.values()))}
        return json.dumps(dict(layers=counts, log_chars=self.log_chars, errors=sorted(self.errors)), sort_keys=True)


def docker(*arguments):
    operation = arguments[0]
    timeout = DOCKER_TIMEOUTS.get(operation, 120)
    started = time.monotonic()
    last_activity = started
    last_quiet_notice = started
    # A second file handle observes progress without moving the child's output
    # offset. Raw logs stay in a private temporary directory and are deleted.
    print(f'Docker {operation}: started (timeout {timeout}s).', flush=True)
    with tempfile.TemporaryDirectory() as folder, \
            open(Path(folder) / 'docker.log', 'w+t', encoding='utf-8') as output, \
            open(Path(folder) / 'docker.log', 'rt', encoding='utf-8', errors='replace') as progress:
        diagnostics = PushDiagnostics()
        def report_progress():
            if operation == 'push':
                output.flush()
                chunk = progress.read()
                diagnostics.consume(chunk)
                print('Docker push diagnostics: ' + diagnostics.summary(), flush=True)
                return bool(chunk)
            return False
        try:
            process = subprocess.Popen(['docker', *arguments], stdout=output, stderr=subprocess.STDOUT)
        except OSError:
            raise RuntimeError(f'Docker {operation} could not be started.') from None
        try:
            while True:
                now = time.monotonic()
                remaining = timeout - (now - started)
                if remaining <= 0:
                    raise TimeoutError()
                try:
                    code = process.wait(timeout=min(HEARTBEAT_SECONDS, remaining))
                    break
                except subprocess.TimeoutExpired:
                    now = time.monotonic()
                    print(f'Docker {operation}: running, elapsed {now - started:.0f}s.', flush=True)
                    if report_progress():
                        last_activity = now
                    elif (operation == 'push' and now - last_activity >= PUSH_IDLE_TIMEOUT
                          and now - last_quiet_notice >= PUSH_IDLE_TIMEOUT):
                        # Non-TTY Docker output may stay quiet while a large
                        # layer is uploading. Silence is diagnostic evidence,
                        # not proof that the daemon stopped transferring data.
                        print(f'Docker push: no new CLI output for at least {PUSH_IDLE_TIMEOUT}s; '
                              f'continuing within the {timeout}s total budget.', flush=True)
                        last_quiet_notice = now
        except (TimeoutError, KeyboardInterrupt) as error:
            process.kill()
            process.wait()
            print(f'Docker {operation}: stopped after {time.monotonic() - started:.1f}s.', flush=True)
            report_progress()
            if isinstance(error, KeyboardInterrupt):
                raise
            raise DockerTimeoutError(f'Docker {operation} exceeded its time budget.') from None
        elapsed = time.monotonic() - started
        report_progress()
        if code:
            print(f'Docker {operation}: failed after {elapsed:.1f}s.', flush=True)
            raise RuntimeError(f'Docker {operation} failed with exit code {code}.')
        print(f'Docker {operation}: completed in {elapsed:.1f}s.', flush=True)
        output.seek(0)
        return output.read()


def inspect_image(image):
    images = json.loads(docker('image', 'inspect', image))
    if len(images) != 1:
        raise RuntimeError('Expected exactly one inspected image.')
    image = images[0]
    if image.get('Os') != 'linux' or image.get('Architecture') != 'amd64':
        raise RuntimeError('Only the validated linux/amd64 image may be released.')
    if not re.fullmatch(DIGEST, image.get('Id', '')):
        raise RuntimeError('The validated image ID is missing or malformed.')
    return image['Id']


def export_image(directory, component, commit):
    source = source_image(component, commit)
    image_id = inspect_image(source)
    directory.mkdir(parents=True, exist_ok=True)
    docker('save', '--output', str(directory / f'{component}-image.tar'), source)
    metadata = {'component': component, 'commit': commit, 'source_image': source,
                'image_id': image_id, 'platform': 'linux/amd64'}
    (directory / f'{component}-image.json').write_text(json.dumps(metadata, indent=2) + '\n', encoding='utf-8')
    print(f'Exported verified {component} image and identity metadata.', flush=True)


def load_verified_images(directory, commit, components=COMPONENTS):
    verified = {}
    # Reject either archive's metadata before loading or tagging anything.
    if not components or len(set(components)) != len(components) or set(components) - set(COMPONENTS):
        raise ValueError('Select supported release components.')
    for component in components:
        metadata = json.loads((directory / f'{component}-image.json').read_text(encoding='utf-8'))
        if (metadata.get('component') != component or metadata.get('commit') != commit
                or metadata.get('source_image') != source_image(component, commit)
                or metadata.get('platform') != 'linux/amd64'
                or not re.fullmatch(DIGEST, metadata.get('image_id', ''))):
            raise RuntimeError('Image artifact identity does not match the validated commit and platform.')
        if not (directory / f'{component}-image.tar').is_file():
            raise RuntimeError('The verified image archive is missing.')
        verified[component] = metadata
    for component, metadata in verified.items():
        archive = directory / f'{component}-image.tar'
        print(f'Loading verified {component} archive ({archive.stat().st_size / 1048576:.1f} MiB).', flush=True)
        docker('load', '--input', str(archive))
        if inspect_image(metadata['source_image']) != metadata['image_id']:
            raise RuntimeError('Loaded image ID differs from the validated artifact.')
    return verified


def push_digest(output):
    digests = set(re.findall(r'\bdigest:\s*(' + DIGEST + r')\b', output))
    if len(digests) != 1:
        raise RuntimeError('Docker push did not report one unambiguous manifest digest.')
    return digests.pop()


def push_verified_tag(reference):
    # Re-send the exact same image/tag once after a stalled CLI was reaped.
    # Never retry an interruption, registry rejection or invalid digest.
    for attempt in range(2):
        try:
            output = docker('push', reference)
        except DockerTimeoutError:
            if attempt == 1:
                raise
            print('Docker push: timed out; retrying the same verified tag once.', flush=True)
        else:
            return push_digest(output)


def write_release(output, summary, release):
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(release, indent=2) + '\n', encoding='utf-8')
    title = 'Published verified images' if release['complete'] else 'Partial or failed image publication'
    lines = [f'## {title}', '', f"Commit: `{release['commit']}`",
             f"Compatibility evidence: `{release['compatibility']}`", '']
    for component, image in release['images'].items():
        if image.get('reference'):
            lines.append(f"- {component}: `{image['reference']}`")
    lines += ['', 'Roll back only the selected component using its recorded digest. Tags can be overwritten.',
              'A partial publication must not be treated as a completed release.', '']
    with summary.open('a', encoding='utf-8') as stream:
        stream.write('\n'.join(lines))


def publish_images(directory, registry, namespace, commit, extra_tag, output, summary, components=COMPONENTS,
                   compatibility='not-recorded'):
    if compatibility not in ('not-recorded', 'component-contracts', 'candidate-integration'):
        raise ValueError('Unsupported compatibility evidence scope.')
    repositories = coordinates(registry, namespace, commit, extra_tag)
    # Save a failure receipt even if archive loading/identity verification fails.
    release = {'commit': commit, 'components': list(components), 'compatibility': compatibility,
               'complete': False, 'images': {
        component: {'repository': repositories[component], 'tags': []}
        for component in components
    }}
    version_tags = list(dict.fromkeys([f'sha-{commit[:7]}'] + ([extra_tag] if extra_tag and extra_tag != 'latest' else [])))
    try:
        verified = load_verified_images(directory, commit, components)
        for component, metadata in verified.items():
            release['images'][component]['image_id'] = metadata['image_id']
        # Advance rolling tags only for the explicitly selected components.
        for tag in [*version_tags, 'latest']:
            for component, metadata in verified.items():
                reference = f'{repositories[component]}:{tag}'
                print(f'Publishing {component} tag {tag}: tagging verified image.', flush=True)
                docker('tag', metadata['image_id'], reference)
                print(f'Publishing {component} tag {tag}: pushing and resolving digest.', flush=True)
                digest = push_verified_tag(reference)
                image = release['images'][component]
                if image.get('digest', digest) != digest:
                    raise RuntimeError('Published tags resolved to different manifest digests.')
                image.update(digest=digest, reference=f'{repositories[component]}@{digest}')
                image['tags'].append(tag)
                print(f'Published verified {component} tag {tag}.', flush=True)
        release['complete'] = True
    finally:
        write_release(output, summary, release)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest='command', required=True)
    export = commands.add_parser('export')
    export.add_argument('--component', choices=COMPONENTS, required=True)
    export.add_argument('--commit', required=True)
    export.add_argument('--directory', type=Path, required=True)
    verify = commands.add_parser('verify')
    verify.add_argument('--commit', required=True)
    verify.add_argument('--directory', type=Path, required=True)
    verify.add_argument('--component', choices=COMPONENTS, action='append')
    for name in ('check-config', 'publish'):
        command = commands.add_parser(name)
        command.add_argument('--commit', required=True)
        command.add_argument('--extra-tag', default='')
        if name == 'publish':
            command.add_argument('--compatibility', choices=('not-recorded', 'component-contracts', 'candidate-integration'),
                                 default='not-recorded')
            command.add_argument('--component', choices=COMPONENTS, action='append')
            command.add_argument('--directory', type=Path, required=True)
            command.add_argument('--output', type=Path, required=True)
            command.add_argument('--summary', type=Path, required=True)
    args = parser.parse_args()
    if args.command == 'export':
        export_image(args.directory, args.component, args.commit)
        return
    if args.command == 'verify':
        load_verified_images(args.directory, args.commit, args.component or COMPONENTS)
        print('Selected archives match the validated commit, image IDs and linux/amd64 platform.')
        return
    registry = os.getenv('ACR_REGISTRY', '')
    namespace = os.getenv('ACR_NAMESPACE', '')
    if args.command == 'check-config':
        coordinates(registry, namespace, args.commit, args.extra_tag)
        print('Registry coordinate configuration is valid.')
    else:
        publish_images(args.directory, registry, namespace, args.commit, args.extra_tag,
                       args.output, args.summary, args.component or COMPONENTS, args.compatibility)


if __name__ == '__main__':
    main()
