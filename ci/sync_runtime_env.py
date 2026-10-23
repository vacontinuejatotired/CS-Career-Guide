"""Send only AI settings over verified SSH; preserve host-owned dotenv entries."""

import base64
import json
import os
from pathlib import Path
import re
import shlex
import stat
import subprocess
import sys
import tempfile


AI_KEYS = (
    'LLM_API_KEY', 'LLM_BASE_URL', 'LLM_MODEL', 'CAREER_REPORT_MODEL',
    'ASR_API_KEY', 'ASR_WSS_URL', 'ASR_MODEL', 'ENABLE_TTS',
    'TTS_API_KEY', 'TTS_WSS_URL', 'TTS_MODEL', 'TTS_VOICE',
)
REQUIRED = ('LLM_API_KEY', 'LLM_BASE_URL', 'LLM_MODEL')


def validate_values(values):
    if not isinstance(values, dict) or set(values) - set(AI_KEYS):
        raise ValueError('Payload contains unsupported configuration keys')
    for name, value in values.items():
        # Reject control characters and dotenv quoting ambiguities. Provider keys,
        # model IDs and endpoint URLs do not need quotes or backslashes.
        if not isinstance(value, str) or any(ord(c) < 32 or ord(c) == 127 for c in value):
            raise ValueError('Configuration must contain single-line string values')
        if any(c in value for c in "'\\"):
            raise ValueError('Configuration contains unsupported quoting characters')
    if any(not values.get(name, '').strip() for name in REQUIRED):
        raise ValueError('Required LLM configuration is missing')


def merge_env(original, values):
    """Keep every non-managed line byte-for-byte; refuse ambiguous dotenv files."""
    validate_values(values)
    text = original.decode('utf-8')
    lines = text.splitlines(keepends=True)
    newline = '\r\n' if '\r\n' in text else '\n'
    result, seen = [], set()
    for line in lines:
        stripped = line.strip()
        if not stripped or stripped.startswith('#'):
            result.append(line)
            continue
        match = re.fullmatch(r"\s*(?:export\s+)?([A-Za-z_][A-Za-z0-9_]*)\s*=\s*(.*)", line.rstrip('\r\n'))
        if not match:
            raise ValueError('Unsupported dotenv syntax; original file was preserved')
        name, value = match.groups()
        # Multiline quoted values could contain apparent KEY=value lines. Refuse
        # rather than accidentally changing a line inside a host-owned value.
        if value.startswith(("'", '"')):
            quote = value[0]
            if not re.fullmatch(r"(?:\\.|[^" + quote + r"\\])*" + quote + r"\s*(?:#.*)?", value[1:]):
                raise ValueError('Multiline or ambiguous dotenv values are unsupported')
        if name not in values:
            result.append(line)
            continue
        if name in seen:
            raise ValueError('Duplicate managed dotenv key; original file was preserved')
        seen.add(name)
        result.append(f"{name}='{values[name]}'{newline}")
    if result and not result[-1].endswith(('\n', '\r')):
        result[-1] += newline
    for name in AI_KEYS:
        if name in values and name not in seen:
            result.append(f"{name}='{values[name]}'{newline}")
    return ''.join(result).encode('utf-8')


def compose_run(command, *, capture=False):
    # Compose diagnostics can contain expanded secrets. Never forward its output.
    result = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=600)
    if result.returncode:
        raise RuntimeError('Remote Compose operation failed; inspect it privately on the server')
    return json.loads(result.stdout) if capture else None


def apply_remote(env_path, values):
    import fcntl  # Remote target is Linux; local unit tests remain portable.

    validate_values(values)
    path = Path(env_path)
    if not path.is_absolute() or path.name != '.env' or path.resolve() != path:
        raise ValueError('Target must be an absolute existing .env path without symlinks')
    parent = path.parent.stat()
    if parent.st_uid != os.geteuid() or parent.st_mode & 0o022:
        raise ValueError('Deployment directory must be owned by SSH user and not writable by others')
    compose = path.parent / 'docker-compose.yml'
    if not compose.is_file():
        raise ValueError('Existing docker-compose.yml is required beside .env')
    lock_fd = os.open(str(path) + '.ai-sync.lock', os.O_CREAT | os.O_RDWR | os.O_NOFOLLOW, 0o600)
    candidate = None
    try:
        fcntl.flock(lock_fd, fcntl.LOCK_EX)
        with os.fdopen(os.open(path, os.O_RDONLY | os.O_NOFOLLOW), 'rb') as current:
            info = os.fstat(current.fileno())
            if not stat.S_ISREG(info.st_mode) or info.st_uid != os.geteuid() or info.st_nlink != 1:
                raise ValueError('Target must be a regular file owned by SSH user without hard links')
            if info.st_mode & 0o077:
                raise ValueError('Set server .env permissions to 600 before enabling sync')
            original = current.read()
        merged = merge_env(original, values)
        fd, candidate = tempfile.mkstemp(prefix='.ai-env-', dir=path.parent)
        with os.fdopen(fd, 'wb') as output:
            output.write(merged)
            output.flush()
            os.fsync(output.fileno())
        base = ['docker', 'compose', '--project-directory', str(path.parent), '-f', str(compose)]
        config = compose_run([*base, '--env-file', candidate, 'config', '--format', 'json'], capture=True)
        backend_env = config.get('services', {}).get('backend', {}).get('environment', {})
        if any(str(backend_env.get(k, '')) != v for k, v in values.items()):
            raise ValueError('Server Compose must pass all managed AI settings without conflicting shell overrides')
        # Pull first: network/authentication failures leave the original .env intact.
        compose_run([*base, '--env-file', candidate, 'pull', 'backend', 'frontend'])
        if path.read_bytes() != original:
            raise ValueError('Server .env changed concurrently; refusing overwrite')
        os.replace(candidate, path)
        candidate = None
        compose_run([*base, '--env-file', str(path), 'up', '-d', '--no-deps',
                     '--force-recreate', '--wait', '--wait-timeout', '180', 'backend', 'frontend'])
        print('AI configuration synchronized; application containers recreated and healthy')
    finally:
        if candidate is not None:
            Path(candidate).unlink(missing_ok=True)
        os.close(lock_fd)


def sync():
    required = ('DEPLOY_SSH_HOST', 'DEPLOY_SSH_USER', 'DEPLOY_ENV_PATH',
                'DEPLOY_SSH_KEY', 'DEPLOY_SSH_KNOWN_HOSTS')
    if any(not os.environ.get(name, '').strip() for name in required):
        raise ValueError('Deployment SSH secrets are incomplete')
    host, user = os.environ['DEPLOY_SSH_HOST'], os.environ['DEPLOY_SSH_USER']
    port = os.environ.get('DEPLOY_SSH_PORT') or '22'
    if not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9.-]*', host):
        raise ValueError('Invalid SSH host')
    if not re.fullmatch(r'[a-z_][a-z0-9_-]*', user):
        raise ValueError('Invalid SSH user')
    if not port.isdigit() or not 1 <= int(port) <= 65535:
        raise ValueError('Invalid SSH port')
    values = {name: os.environ[name] for name in AI_KEYS if os.environ.get(name, '')}
    validate_values(values)
    source = base64.b64encode(Path(__file__).read_bytes()).decode('ascii')
    code = f"import base64;exec(compile(base64.b64decode('{source}'),'ai-env-sync','exec'))"
    remote = shlex.join(['python3', '-c', code, '--remote', os.environ['DEPLOY_ENV_PATH']])
    with tempfile.TemporaryDirectory(prefix='ai-env-ssh-') as directory:
        os.chmod(directory, 0o700)
        key, known = Path(directory) / 'identity', Path(directory) / 'known_hosts'
        for target, content in ((key, os.environ['DEPLOY_SSH_KEY']),
                                (known, os.environ['DEPLOY_SSH_KNOWN_HOSTS'])):
            fd = os.open(target, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
            with os.fdopen(fd, 'w', encoding='utf-8', newline='\n') as output:
                output.write(content.rstrip('\r\n') + '\n')
        command = ['ssh', '-F', '/dev/null', '-T', '-i', str(key), '-p', port,
                   '-o', 'IdentitiesOnly=yes', '-o', 'BatchMode=yes',
                   '-o', 'StrictHostKeyChecking=yes', '-o', f'UserKnownHostsFile={known}',
                   '-o', 'GlobalKnownHostsFile=/dev/null', '-o', 'ConnectTimeout=15',
                   '-o', 'ServerAliveInterval=15', '-o', 'ServerAliveCountMax=3',
                   f'{user}@{host}', remote]
        # The API keys travel through SSH stdin, never argv, shell text or an artifact.
        result = subprocess.run(command, input=json.dumps(values).encode(),
                                stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=1800)
        if result.returncode:
            raise RuntimeError('SSH sync or container activation failed; inspect the server privately')
        print('AI environment sync and container health checks completed')


if __name__ == '__main__':
    try:
        if len(sys.argv) == 3 and sys.argv[1] == '--remote':
            apply_remote(sys.argv[2], json.load(sys.stdin))
        else:
            sync()
    except Exception:
        # Do not emit exception values: dotenv, SSH and Docker errors can hold secrets.
        print('AI environment synchronization failed; configuration or activation requires attention', file=sys.stderr)
        sys.exit(1)
