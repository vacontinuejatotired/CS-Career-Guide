"""可复现的离线实验：只用 dev 选择候选，再报告固定 test 结果。"""
import argparse
import json
from pathlib import Path

from .datasets import FrozenDatasetLoader
from .metrics import aggregate_metrics, ranking_metrics
from .strategies import build_default_strategies


def measure(strategy, dataset, k):
    results = []
    for sample in dataset['queries']:
        predicted = strategy.rank(query=sample['query'], top_k=k)
        results.append({'query_id': sample['id'], 'group': sample['group'],
                        'relevant_ids': sample['relevant_ids'], 'predicted_ids': predicted,
                        'metrics': ranking_metrics(relevant_ids=sample['relevant_ids'], predicted_ids=predicted, k=k)})
    return {'metrics': aggregate_metrics([r['metrics'] for r in results if r['group'] == 'relevant']),
            'unrelated_predictions': sum(len(r['predicted_ids']) for r in results if r['group'] == 'unrelated'),
            'results': results}


def experiment():
    strategies, _ = build_default_strategies()
    loader = FrozenDatasetLoader()
    dev, test = (loader.load(f'xiaolin-eval-{split}-v1') for split in ('dev', 'test'))
    runs = []
    for name in ('xiaolin-baseline', 'xiaolin-balanced'):
        for k in (3, 5, 10):
            runs.append({'strategy': name, 'k': k, **measure(strategies[name], dev, k)})
    # F1 is chosen before inspecting test. Stable tie order retains the baseline.
    selected = max(runs, key=lambda run: run['metrics']['f1_at_k'])
    return {'created': '2026-11-16', 'corpus': strategies['xiaolin-baseline'].corpus_summary,
            'dataset_sha256': {'dev': dev['sha256'], 'test': test['sha256']},
            'limitations': '16条相关查询和2条无关查询，初步非穷尽标注；未经成员2独立复核；无模型、Embedding、线上或浏览器验收',
            'selection_rule': '只按dev宏平均F1选择策略与K，同分保留先出现的基线；不据test反向调参',
            'dev_runs': runs,
            'selected': {'strategy': selected['strategy'], 'k': selected['k']},
            'test_runs': [{'strategy': name, 'k': k, **measure(strategies[name], test, k)}
                          for name, k in dict.fromkeys([('xiaolin-baseline', 5),
                                                      (selected['strategy'], selected['k'])])]}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', required=True)
    args = parser.parse_args()
    Path(args.output).write_text(json.dumps(experiment(), ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
