"""Check the current master once; optionally publish the CI-selected components to TCR."""

import argparse
import json
import os
from pathlib import Path
import re
import stat
import subprocess
from urllib.error import URLError

from tencent_pilot_gate import WORKFLOW_ID, github_json, repository_json, verify_ci_job, verify_run

JOBS = {'Frontend image': 'frontend', 'Backend image': 'backend'}
TCR = 'ccr.ccs.tencentyun.com/cs-career-guide-pilot'


def candidate(read=repository_json, read_run=github_json):
    sha = read('git/ref/heads/master')['object']['sha']
    if not re.fullmatch(r'[0-9a-f]{40}', sha):
        raise ValueError('Invalid master SHA')
    runs = read(f'actions/workflows/{WORKFLOW_ID}/runs?branch=master&event=push'
                f'&head_sha={sha}&per_page=1')['workflow_runs']
    if not runs or runs[0]['status'] != 'completed':
        return None
    run_id = runs[0]['id']
    if type(run_id) is not int or run_id < 1:
        raise ValueError('Invalid Run ID')
    run = read_run(str(run_id))
    verify_run(run, run_id, sha)
    attempt = run['run_attempt']
    if type(attempt) is not int or attempt < 1:
        raise ValueError('Invalid Run attempt')
    jobs = read_run(f'{run_id}/attempts/{attempt}/jobs?per_page=100')
    current = read_run(str(run_id))
    verify_run(current, run_id, sha)
    verify_ci_job(current, jobs)
    selected = []
    for name, component in JOBS.items():
        matches = [job for job in jobs['jobs'] if job.get('name') == name]
        expected = {'status': 'completed', 'head_sha': sha, 'run_id': run_id,
                    'run_attempt': attempt}
        if (len(matches) != 1 or any(matches[0].get(k) != v for k, v in expected.items())
                or matches[0].get('conclusion') not in ('success', 'skipped')):
            raise ValueError(f'Missing or invalid image result: {component}')
        if matches[0]['conclusion'] == 'success':
            selected.append(component)
    if not selected:
        return None
    return sha, str(run_id), 'all' if len(selected) == 2 else selected[0]


def verified_images(path, components):
    expected = set(JOBS.values()) if components == 'all' else {components}
    images = {}
    for line in path.read_text(encoding='ascii').splitlines():
        component, sep, ref = line.partition(' ')
        if (not sep or component not in expected or component in images
                or not re.fullmatch(rf'{re.escape(TCR)}/{component}-pilot@sha256:[0-9a-f]{{64}}', ref)):
            raise ValueError('Invalid or duplicate TCR receipt entry')
        images[component] = ref
    if images.keys() != expected:
        raise ValueError('Missing verified TCR images')
    return images


def publish(selection, state, run=subprocess.run):
    state.mkdir(mode=0o700, exist_ok=True)
    info = state.lstat()
    if not stat.S_ISDIR(info.st_mode) or info.st_uid != os.geteuid() or info.st_mode & 0o077:
        raise ValueError('Publish state must be a private directory owned by the operator')
    sha, run_id, components = selection
    claim = state / sha
    try:
        claim.mkdir(mode=0o700)
    except FileExistsError:
        print(f'ALREADY_CLAIMED {sha}; check the receipt before any manual retry')
        return
    print(f'PUBLISH_CLAIMED {sha} {run_id} {components}', flush=True)
    script = Path(__file__).resolve().with_name('tencent_pilot.sh')
    # A failed/interrupted attempt leaves its claim for manual reconciliation.
    refs = claim / 'verified-images'
    run(['bash', str(script), *selection], check=True,
        env={**os.environ, 'CS_CAREER_TCR_RECEIPT_FILE': str(refs.resolve())})
    receipt = {'sha': sha, 'run_id': int(run_id), 'images': verified_images(refs, components)}
    pending = claim / 'published.next'
    with pending.open('x', encoding='ascii') as f:
        json.dump(receipt, f, sort_keys=True)
        f.write('\n')
        f.flush()
        os.fsync(f.fileno())
    pending.rename(claim / 'published')
    print(f'PUBLISH_VERIFIED {sha} {run_id} {components}', flush=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument('--source-check', action='store_true')
    mode.add_argument('--publish-state', type=Path)
    args = parser.parse_args()
    try:
        selection = candidate()
        if not selection:
            print('NO_ELIGIBLE_MASTER_BUILD')
            return
        print('TCR_CANDIDATE', *selection, flush=True)
        if args.source_check:
            script = Path(__file__).resolve().with_name('tencent_pilot.sh')
            subprocess.run(['bash', str(script), *selection[:2], 'source-only'], check=True)
        elif args.publish_state:
            publish(selection, args.publish_state)
    except (KeyError, TypeError, ValueError, URLError, OSError, subprocess.CalledProcessError) as exc:
        raise SystemExit(str(exc)) from None


if __name__ == '__main__':
    main()
