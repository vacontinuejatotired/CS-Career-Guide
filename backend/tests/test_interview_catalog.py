"""题库适配的离线回归，不加载Django配置，不调用模型。"""
from pathlib import Path
import sys
import unittest
from unittest.mock import Mock

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from ai_integration.interview.catalog import CatalogInterviewContext
from ai_integration.interview.legacy import LegacyPromptInterview
from career_platform.contracts import Evidence, RankedQuestion
from career_platform.rag.retrieval import TextRetrievalStrategy


class CatalogInterviewTests(unittest.TestCase):
    def setUp(self):
        self.retriever = Mock()
        self.context = CatalogInterviewContext(self.retriever)
        self.legacy = LegacyPromptInterview(lambda name: name, self.context)
        self.history = [{'user': '自我介绍', 'ai': '介绍项目'}, {'user': '项目', 'ai': '项目职责'}]

    def test_intro_project_and_review_do_not_retrieve(self):
        for history in ([], self.history[:1]):
            self.assertEqual(self.legacy.prepare_turn('开始', history, 'gentle').source_footer, '')
        self.assertEqual(self.legacy.prepare_turn('复盘', self.history, 'gentle', review=True).source_footer, '')
        self.retriever.retrieve.assert_not_called()

    def test_only_real_answer_is_retrieved_and_evidence_is_bounded(self):
        self.retriever.retrieve.return_value = [RankedQuestion(
            'q1', 'ArrayList如何扩容', ('扩大容量',),
            (Evidence('q1', 'source', '自编题'), Evidence('q1', 'source_url', 'https://example.invalid/q1')), .8)]
        message = '【面试模式】用户的回答是："我使用ArrayList"\n\n作为面试官'
        turn = self.legacy.prepare_turn(message, self.history, 'technical')
        self.retriever.retrieve.assert_called_once_with(
            query='我使用ArrayList', role='', topic='', difficulty='', top_k=3)
        self.assertIn('q1', turn.system)
        self.assertIn('https://example.invalid/q1', turn.system)
        self.assertIn('不提前输出要点', turn.system)
        self.assertIn('本轮题库检索参考', turn.source_footer)
        self.assertIn('https://example.invalid/q1', turn.source_footer)
        self.assertTrue(turn.user.endswith(message))

    def test_no_hit_and_failure_keep_interview_available_without_fabricated_source(self):
        self.retriever.retrieve.return_value = []
        turn = self.legacy.prepare_turn('没有技术内容', self.history, 'gentle')
        self.assertIn('没有相关命中', turn.system)
        self.assertIn('本轮未命中题库', turn.source_footer)
        self.retriever.retrieve.side_effect = RuntimeError('PRIVATE diagnostic')
        turn = self.legacy.prepare_turn('项目回答', self.history, 'gentle')
        self.assertIn('题库检索暂不可用', turn.system)
        self.assertIn('题库检索暂不可用', turn.source_footer)
        self.assertNotIn('PRIVATE', turn.system)

    def test_revoked_material_is_excluded_by_real_text_retriever(self):
        rows = [{'id': 'allowed', 'question': 'Redis缓存', 'source': '自编', 'permission_status': 'allowed'},
                {'id': 'revoked', 'question': 'Redis缓存', 'source': '自编', 'permission_status': 'pending'}]
        context = CatalogInterviewContext(TextRetrievalStrategy(rows))('Redis', self.history).prompt
        self.assertIn('allowed', context)
        self.assertNotIn('revoked', context)


if __name__ == '__main__':
    unittest.main()
