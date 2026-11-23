from copy import deepcopy
from django.test import SimpleTestCase
from .service import InterviewRagService
from ..records.service import PracticeService
from ..models import AnswerRecord
from ..tests.accept_support import AcceptanceCase, Gateway
from ..tests.helpers import request_id


class RuntimeFeedbackTests(SimpleTestCase):
    def test_runtime_enforces_same_evidence_rules_as_pure_validator(self):
        evidence = {'source_id': 'fixture', 'field_path': 'key_points[0]', 'quote': '集合有序'}
        record = {'answer': '集合有序，我还不清楚其他细节', 'question_snapshot': {
            'question_id': 'fixture', 'key_points': ['集合有序'], 'evidence': [evidence]}}
        valid = {'answer_quote': '集合有序', 'key_points_covered': ['集合有序'],
                 'missing_points': [], 'evidence': [evidence], 'follow_up': '能举例吗？'}
        self.assertTrue(InterviewRagService._valid_feedback(valid, record))
        for changes in ({'answer_quote': ''}, {'evidence': []}, {'missing_points': ['虚构要点']},
                        {'key_points_covered': ['集合有序'] * 2}, {'score': 100}):
            with self.subTest(changes=changes):
                self.assertFalse(InterviewRagService._valid_feedback(deepcopy(valid) | changes, record))


class IndexedFeedbackIntegrationTests(AcceptanceCase):
    def setUp(self):
        super().setUp()
        self.session_row, self.question = self.session()
        self.gateway = Gateway({'answer_quote': '集合语义', 'covered_indices': [0], 'missing_indices': [], 'follow_up': None})
        records = PracticeService(model_gateway=self.gateway)
        self.wire(rag=InterviewRagService(model_gateway=self.gateway, records=records), records=records)

    def test_indices_are_stored_as_original_public_feedback_and_replayed_once(self):
        body = dict(question_id=str(self.question.id), answer='集合语义', request_id=request_id())
        path = f'practice-sessions/{self.session_row.id}/answers/'
        first = self.post(path, body)
        replay = self.post(path, body)
        self.assertEqual(first['id'], replay['id'])
        self.assertEqual(first['feedback']['key_points_covered'], ['语义'])
        self.assertEqual(first['feedback']['evidence'], self.session_row.presented_questions[0]['evidence'])
        self.assertNotIn('covered_indices', first['feedback'])
        self.assertEqual(len(self.gateway.calls), 1)

    def test_invalid_index_preserves_answer_and_reports_model_error(self):
        self.gateway.result['covered_indices'] = [999]
        self.post(f'practice-sessions/{self.session_row.id}/answers/',
                  dict(question_id=str(self.question.id), answer='集合语义', request_id=request_id()), expected=502)
        row = AnswerRecord.objects.get()
        self.assertEqual(row.answer, '集合语义')
        self.assertEqual(row.status, 'failed')
        self.assertEqual(row.failure_code, 'INVALID_MODEL_OUTPUT')
