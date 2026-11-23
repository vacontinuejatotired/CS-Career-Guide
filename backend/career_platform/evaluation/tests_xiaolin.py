import json
from pathlib import Path
from tempfile import TemporaryDirectory

from django.test import SimpleTestCase

from .build_xiaolin import build
from .datasets import DATASET_DIR, FrozenDatasetLoader, fingerprint, load_corpus
from .service import EvaluationService
from .strategies import build_default_strategies
from ..models import EvaluationRun
from ..tests.accept_support import AcceptanceCase
from ..tests.helpers import request_id


class XiaolinFrozenTests(SimpleTestCase):
    def test_corpus_labels_and_disjoint_queries(self):
        corpus, summary = load_corpus(DATASET_DIR / 'xiaolin-corpus-v1.json')
        self.assertEqual(summary['size'], 943)
        ids = {q['id'] for q in corpus['questions']}
        self.assertEqual(len(ids), 943)
        loader = FrozenDatasetLoader()
        datasets = [loader.load(f'xiaolin-eval-{split}-v1') for split in ('dev', 'test')]
        for dataset in datasets:
            self.assertEqual(dataset['corpus_sha256'], summary['sha256'])
            self.assertEqual(set(dataset['corpus_ids']), ids)
            for sample in dataset['queries']:
                self.assertTrue(set(sample['relevant_ids']) <= ids)
        self.assertFalse({q['query'] for q in datasets[0]['queries']} & {q['query'] for q in datasets[1]['queries']})
        self.assertFalse({i for q in datasets[0]['queries'] for i in q['relevant_ids']} &
                         {i for q in datasets[1]['queries'] for i in q['relevant_ids']})

    def test_generated_snapshots_are_reproducible(self):
        source = Path(__file__).resolve().parents[3] / 'data/career-platform/xiaolincoding-questions.json'
        if not source.exists():
            self.skipTest('运行镜像不包含仓库根数据；生成一致性在源码检出验证')
        with TemporaryDirectory() as directory:
            for version, payload in build(source, directory).items():
                frozen = json.loads((DATASET_DIR / f'{version}.json').read_text(encoding='utf-8'))
                self.assertEqual(fingerprint(payload), fingerprint(frozen))

    def test_display_source_compatibility_does_not_accept_changed_question_content(self):
        source = Path(__file__).resolve().parents[3] / 'data/career-platform/xiaolincoding-questions.json'
        if not source.exists():
            self.skipTest('运行镜像不包含仓库根数据；指纹校验在源码检出验证')
        with TemporaryDirectory() as directory:
            tampered = Path(directory) / 'tampered.json'
            data = json.loads(source.read_text(encoding='utf-8'))
            data['questions'][0]['question'] += '（篡改测试）'
            tampered.write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
            with self.assertRaises(ValueError):
                build(tampered, Path(directory) / 'out')


class XiaolinEvaluationTests(AcceptanceCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.strategies, _ = build_default_strategies()

    def setUp(self):
        super().setUp()
        self.wire(evaluation=EvaluationService(strategies=self.strategies))

    def body(self, strategy='xiaolin-baseline'):
        return dict(task='question', strategy=strategy, dataset_version='xiaolin-eval-dev-v1',
                    parameters={'k': 5}, request_id=request_id())

    def test_mismatched_corpus_is_rejected_without_writes(self):
        self.post('evaluation-runs/', self.body('text-baseline'), staff=True, expected=400)
        self.assertEqual(EvaluationRun.objects.count(), 0)

    def test_actual_corpus_fingerprint_is_stored_and_export_is_identical(self):
        result = self.post('evaluation-runs/', self.body(), staff=True)
        summary = self.strategies['xiaolin-baseline'].corpus_summary
        self.assertEqual(result['parameters']['corpus_sha256'], summary['sha256'])
        self.assertEqual(result['parameters']['corpus_size'], 943)
        exported = self.get(f"evaluation-runs/{result['id']}/export/", staff=True)
        self.assertEqual(exported['results'], result['results'])
        self.assertTrue(all(not row['unknown_ids'] for row in result['results']))

    def test_tampered_corpus_fingerprint_is_rejected_without_writes(self):
        class TamperedLoader:
            def load(self, version):
                dataset = FrozenDatasetLoader().load(version)
                dataset['corpus_sha256'] = '0' * 64
                return dataset
        self.wire(evaluation=EvaluationService(strategies=self.strategies, dataset_loader=TamperedLoader()))
        self.post('evaluation-runs/', self.body(), staff=True, expected=400)
        self.assertEqual(EvaluationRun.objects.count(), 0)
