"""题库检索回执在成员4/5边界的隔离集成回归。"""
from django.core.cache import cache
from django.utils import timezone

from career_platform.models import PracticeSession
from career_platform.rag.retrieval import DjangoQuestionRetriever
from career_platform.rag.service import InterviewRagService
from career_platform.records.service import PracticeService
from career_platform.tests.accept_support import AcceptanceCase
from career_platform.tests.helpers import question, request_id


class CatalogReceiptTests(AcceptanceCase):
    def setUp(self):
        super().setUp()
        cache.clear()
        records = PracticeService()
        self.wire(records=records, rag=InterviewRagService(retriever=DjangoQuestionRetriever(), records=records))
        self.questions = [question(), question()]
        for q in self.questions:
            q.collected_at = timezone.now()
            q.save(update_fields=['collected_at'])
        self.retrieved = self.post('questions/retrieve/', dict(
            role='Java后端', topic='', jd_text='集合', difficulty='easy', top_k=5, request_id=request_id()))
        self.body = dict(role='Java后端', topic='', difficulty='easy',
                         question_ids=[r['question_id'] for r in self.retrieved['results']],
                         retrieval_id=self.retrieved['retrieval_id'], request_id=request_id())

    def test_real_question_metadata_survives_retrieval_and_snapshot(self):
        item = self.retrieved['results'][0]
        self.assertEqual(item['role'], 'Java后端')
        self.assertEqual(item['topic'], '集合')
        self.assertTrue(item['collected_at'])
        session = self.post('practice-sessions/', self.body)
        self.assertEqual(session['presented_questions'][0]['collected_at'], item['collected_at'])

    def test_revoked_or_deleted_question_cannot_start_new_session(self):
        self.questions[0].permission_status = 'restricted'
        self.questions[0].save(update_fields=['permission_status'])
        self.post('practice-sessions/', self.body, expected=409)
        self.assertEqual(PracticeSession.objects.count(), 0)
        self.questions[0].delete()
        self.post('practice-sessions/', self.body, expected=409)
        self.assertEqual(PracticeSession.objects.count(), 0)

    def test_ranked_order_is_preserved_but_ordered_subset_is_allowed(self):
        reversed_body = self.body | {'question_ids': list(reversed(self.body['question_ids']))}
        self.post('practice-sessions/', reversed_body, expected=400)
        subset = self.body | {'question_ids': self.body['question_ids'][1:]}
        session = self.post('practice-sessions/', subset)
        self.assertEqual([q['question_id'] for q in session['presented_questions']], subset['question_ids'])

    def test_receipt_is_user_bound_and_expires_without_creating_session(self):
        self.client.force_authenticate(self.other)
        self.post('practice-sessions/', self.body, expected=409)
        self.client.force_authenticate(self.user)
        cache.clear()
        self.post('practice-sessions/', self.body, expected=409)
        self.assertEqual(PracticeSession.objects.count(), 0)
