"""Validate CI results separately from legacy ACR publication."""

import argparse
import json
import sys
from pathlib import Path

COMPONENTS = ('backend', 'frontend')


def failures_for(needs):
    failures = []

    def require(job, expected):
        result = needs.get(job, {}).get('result', 'missing')
        if result != expected:
            failures.append(f'{job}: expected {expected}, got {result}')

    require('changes', 'success')
    require('platform-gates', 'success')
    outputs = needs.get('changes', {}).get('outputs', {})
    keys = (*COMPONENTS, 'code')
    if any(outputs.get(key) not in {'true', 'false'} for key in keys):
        return failures + ['Missing or invalid component selection']
    selected = {item for item in COMPONENTS if outputs[item] == 'true'}
    if (outputs['code'] == 'true') != bool(selected):
        failures.append('Inconsistent component selection')
    require('delivery-checks', 'success' if selected else 'skipped')
    for component in COMPONENTS:
        for suffix in ('test', 'image'):
            require(f'{component}-{suffix}', 'success' if component in selected else 'skipped')
    require('integration', 'success' if len(selected) == 2 else 'skipped')
    return failures


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--summary', type=Path, required=True)
    args = parser.parse_args()
    failures = failures_for(json.load(sys.stdin))
    status = 'Failed' if failures else 'Passed'
    with args.summary.open('a', encoding='utf-8') as output:
        output.write('\n'.join(['## CI validation (ACR and deployment excluded)', '',
                                status, *[f'- {item}' for item in failures], '']))
    return bool(failures)


if __name__ == '__main__':
    raise SystemExit(main())
