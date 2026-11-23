"""Validate the GitHub Actions gate for the Tencent build pilot."""

import argparse
import json
import os
from pathlib import Path
import re
import sys
from urllib.error import URLError
from urllib.request import HTTPRedirectHandler, Request, build_opener

REPOSITORY = 'vacontinuejatotired/CS-Career-Guide'
WORKFLOW_ID = 391258355
GATE_NAME = 'CI validation (no publication)'


def verify_run(run, run_id, sha):
    expected = dict(id=run_id, workflow_id=WORKFLOW_ID, head_branch='master',
                    head_sha=sha, event='push', status='completed')
    for key, value in expected.items():
        if run.get(key) != value:
            raise ValueError(f'GitHub gate rejected this run: {key}')
    for key in ('repository', 'head_repository'):
        if (run.get(key) or {}).get('full_name') != REPOSITORY:
            raise ValueError(f'GitHub gate rejected this run: {key}')


def verify_ci_job(run, jobs_page):
    if run.get('conclusion') not in ('success', 'failure'):
        raise ValueError('GitHub gate rejected this run: conclusion')
    attempt = run.get('run_attempt')
    if type(attempt) is not int or attempt < 1:
        raise ValueError('GitHub gate rejected this run: run_attempt')
    jobs = jobs_page['jobs']
    if jobs_page.get('total_count') != len(jobs):
        raise ValueError('GitHub gate rejected an incomplete attempt job list')
    gates = [job for job in jobs if job.get('name') == GATE_NAME]
    if len(gates) != 1 or any(gates[0].get(key) != value for key, value in {
        'run_id': run['id'], 'run_attempt': attempt, 'head_sha': run['head_sha'],
        'status': 'completed', 'conclusion': 'success',
    }.items()):
        raise ValueError('GitHub gate requires one successful CI validation job in this attempt')


class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def github_token():
    path = os.environ.get('CS_CAREER_GITHUB_TOKEN_FILE')
    if not path and os.environ.get('CREDENTIALS_DIRECTORY'):
        path = Path(os.environ['CREDENTIALS_DIRECTORY']) / 'github-token'
    if not path:
        return None
    try:
        token = Path(path).read_text(encoding='ascii').strip()
    except (OSError, UnicodeError):
        raise ValueError('Cannot read configured GitHub API credential') from None
    if not re.fullmatch(r'[A-Za-z0-9_]{1,512}', token):
        raise ValueError('Invalid GitHub API credential file')
    return token


def repository_json(path):
    request = Request(f'https://api.github.com/repos/{REPOSITORY}/{path}',
                      headers={'Accept': 'application/vnd.github+json',
                               'User-Agent': 'cs-career-guide-tcr-pilot'})
    token = github_token()
    if token is not None:
        request.add_unredirected_header('Authorization', f'Bearer {token}')
    with build_opener(NoRedirect()).open(request, timeout=15) as response:
        return json.load(response)


def github_json(path):
    return repository_json(f'actions/runs/{path}')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('sha')
    parser.add_argument('run_id', type=int)
    args = parser.parse_args()
    if not re.fullmatch(r'[0-9a-f]{40}', args.sha) or args.run_id < 1:
        parser.error('Expected a full lowercase commit SHA and a positive Run ID')
    try:
        run = github_json(str(args.run_id))
        verify_run(run, args.run_id, args.sha)
        attempt = run.get('run_attempt')
        if type(attempt) is not int or attempt < 1:
            raise ValueError('GitHub gate rejected this run: run_attempt')
        jobs = github_json(f'{args.run_id}/attempts/{attempt}/jobs?per_page=100')
        verify_ci_job(run, jobs)
        current = github_json(str(args.run_id))
        verify_run(current, args.run_id, args.sha)
        verify_ci_job(current, jobs)
    except (KeyError, TypeError, ValueError, URLError, OSError) as exc:
        sys.exit(str(exc))
    print(f'GitHub gate passed: {args.run_id} {args.sha}')


if __name__ == '__main__':
    main()
