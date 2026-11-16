"""纯内存文本检索基线；候选由调用方提供，不读取 ORM、索引或模型。"""

import math
import re
import unicodedata
from collections import Counter
from collections.abc import Iterable, Mapping
from copy import deepcopy
from typing import Any

from ..contracts import Evidence, RankedQuestion


def _normalize(text: str) -> str:
    return unicodedata.normalize('NFKC', text).strip().casefold()


def _tokens(text: str) -> set[str]:
    """英文/数字按词，连续中文按二元组；不需要分词模型。"""
    return set(_token_sequence(text))


def _token_sequence(text: str) -> list[str]:
    """与 ``_tokens`` 相同的切分，但保留重复词供 BM25 统计词频。"""
    sequence = []
    for part in re.findall(r'[a-z0-9_+#]+|[\u3400-\u9fff]+', _normalize(text)):
        if '\u3400' <= part[0] <= '\u9fff' and len(part) > 1:
            sequence.extend(part[i:i + 2] for i in range(len(part) - 1))
        else:
            sequence.append(part)
    return sequence


class TextRetrievalStrategy:
    """接收沿用 InterviewQuestion 字段的字典序列，输出 RankedQuestion。

    构造时复制候选形成离线快照，必须显式提供候选，避免将未配置数据源
    冒充无命中。权重依次为题干、标签、参考要点、参考答案。
    """

    def __init__(
        self,
        questions: Iterable[Mapping[str, Any]],
        *,
        min_score: float = 0.0,
        field_weights: Mapping[str, float] | None = None,
        scoring: str = 'coverage',
    ):
        weights = dict(field_weights) if field_weights is not None else {
            'question': 4.0, 'tags': 3.0, 'key_points': 2.0, 'reference_answer': 1.0,
        }
        fields = {'question', 'tags', 'key_points', 'reference_answer'}
        if not weights or not weights.keys() <= fields:
            raise ValueError('field_weights 只能包含题干、标签、参考要点和参考答案字段')
        if (
            any(not math.isfinite(w) or w < 0 for w in weights.values())
            or not math.isfinite(sum(weights.values()))
            or not sum(weights.values())
        ):
            raise ValueError('field_weights 必须有限、非负且至少一个为正')
        if not math.isfinite(min_score) or not 0 <= min_score <= 1:
            raise ValueError('min_score 必须在 0 到 1 之间')
        if scoring not in {'coverage', 'bm25'}:
            raise ValueError('scoring 只能是 coverage 或 bm25')
        self._questions = tuple(deepcopy(dict(q)) for q in questions
                                if q.get('permission_status') == 'allowed'
                                and q.get('id') and q.get('question', '').strip()
                                and q.get('source', '').strip())
        self._weights = weights
        self._min_score = min_score
        self._scoring = scoring
        self._field_lengths = (tuple(self._field_tokens(q) for q in self._questions)
                               if scoring == 'bm25' else ())
        self._avg_lengths = {
            field: (sum(sum(tokens[field].values()) for tokens in self._field_lengths) / len(self._field_lengths)
                    if self._field_lengths else 0.0)
            for field in ('question', 'tags', 'key_points', 'reference_answer')
        }
        corpus_frequency = {
            field: Counter(token for tokens in self._field_lengths for token in tokens[field])
            for field in ('question', 'tags', 'key_points', 'reference_answer')
        }
        self._document_frequency = corpus_frequency

    @staticmethod
    def _field_tokens(candidate: Mapping[str, Any]) -> dict[str, Counter]:
        result = {}
        for field in ('question', 'tags', 'key_points', 'reference_answer'):
            is_list = field in {'tags', 'key_points'}
            value = candidate.get(field, []) if is_list else candidate.get(field, '')
            parts = value if is_list else [value]
            result[field] = Counter(token for part in parts for token in _token_sequence(str(part)))
        return result

    def _bm25_score(self, query_tokens: set[str], candidate_index: int) -> float:
        """以允许的完整语料计算字段加权 BM25，单调映射到 0..1。"""
        if not query_tokens:
            return 0.0
        n_docs = len(self._questions)
        raw = 0.0
        k1, b = 1.2, 0.75
        fields = self._field_lengths[candidate_index]
        for field, weight in self._weights.items():
            counts = fields[field]
            length = sum(counts.values())
            average = self._avg_lengths[field]
            if not length or not average:
                continue
            field_score = 0.0
            for token in query_tokens:
                term_frequency = counts.get(token, 0)
                if not term_frequency:
                    continue
                document_frequency = self._document_frequency[field].get(token, 0)
                idf = math.log(1 + (n_docs - document_frequency + 0.5) /
                               (document_frequency + 0.5))
                field_score += idf * (term_frequency * (k1 + 1)) / (
                    term_frequency + k1 * (1 - b + b * length / average))
            raw += weight * field_score
        raw /= sum(self._weights.values())
        return raw / (1.0 + raw)

    def retrieve(
        self,
        *,
        query: str,
        role: str,
        topic: str,
        difficulty: str,
        top_k: int,
    ) -> list[RankedQuestion]:
        """先筛选，再按所选算法排序；空查询仅作条件筛选。"""
        if isinstance(top_k, bool) or not isinstance(top_k, int) or not 1 <= top_k <= 20:
            raise ValueError('top_k 必须是 1 到 20 的整数')
        filters = {'role': role, 'topic': topic, 'difficulty': difficulty}
        filters = {field: _normalize(value) for field, value in filters.items() if value.strip()}
        query_tokens = _tokens(query)
        if query.strip() and not query_tokens:
            return []
        results = []
        for candidate_index, candidate in enumerate(self._questions):
            if candidate.get('permission_status') != 'allowed':
                continue
            if any(_normalize(candidate.get(field, '')) != value for field, value in filters.items()):
                continue
            # 缺少来源、稳定 ID 或题干的候选不可伪造来源后返回。
            if (
                not candidate.get('id')
                or not candidate.get('source', '').strip()
                or not candidate.get('question', '').strip()
            ):
                continue
            score = 0.0
            if query_tokens and self._scoring == 'bm25':
                score = self._bm25_score(query_tokens, candidate_index)
                if score == 0:
                    continue
            elif query_tokens:
                for field, weight in self._weights.items():
                    is_list = field in {'tags', 'key_points'}
                    value = candidate.get(field, []) if is_list else candidate.get(field, '')
                    parts = value if is_list else [value]
                    field_tokens = set().union(*(_tokens(part) for part in parts))
                    score += weight * len(query_tokens & field_tokens) / len(query_tokens)
                score /= sum(self._weights.values())
                if score == 0:
                    continue
            if score < self._min_score:
                continue
            question_id = str(candidate['id'])
            evidence = [Evidence(question_id, 'source', candidate['source'])]
            for field in ('source_url', 'question', 'reference_answer', 'role', 'topic', 'difficulty'):
                if candidate.get(field):
                    evidence.append(Evidence(question_id, field, candidate[field]))
            collected = candidate.get('collected_at')
            if collected:
                collected = collected.isoformat() if hasattr(collected, 'isoformat') else str(collected)
                evidence.append(Evidence(question_id, 'collected_at', collected))
            for field in ('tags', 'key_points'):
                evidence.extend(
                    Evidence(question_id, f'{field}[{index}]', quote)
                    for index, quote in enumerate(candidate.get(field, []))
                )
            results.append(RankedQuestion(
                question_id=question_id,
                question=candidate['question'],
                key_points=tuple(candidate.get('key_points', [])),
                evidence=tuple(evidence),
                score=score,
            ))
        results.sort(key=lambda result: (-result.score, result.question_id))
        return results[:top_k]


class DjangoQuestionRetriever:
    """Build the deterministic text baseline from the current allowed catalog."""

    def retrieve(self, **query):
        from ..models import InterviewQuestion

        query = dict(query)
        topic = str(query.get('topic') or '').strip()
        if not topic and _normalize(str(query.get('query') or '')) == _normalize(str(query.get('role') or '')):
            # 只有岗位条件时浏览可选题，岗位是过滤条件，不要求题干重复岗位名。
            query['query'] = ''
        rows = InterviewQuestion.objects.filter(permission_status='allowed').values(
            'id', 'category', 'role', 'topic', 'difficulty', 'question', 'key_points',
            'reference_answer', 'tags', 'source', 'source_url', 'permission_status',
            'collected_at', 'dedupe_key', 'is_demo',
        )
        if topic and not InterviewQuestion.objects.filter(
                permission_status='allowed', topic__iexact=topic).exists():
            # topic 是规范分类；未命中分类时，将输入作为检索词，允许
            # “mysql” 命中 topic=数据库 下题干/标签中的 MySQL。
            query['query'] = f"{query.get('query', '')} {topic}".strip()
            query['topic'] = ''
            topic_tokens = _tokens(topic)
            rows = [row for row in rows if topic_tokens and topic_tokens <= set().union(
                *TextRetrievalStrategy._field_tokens(row).values())]
        return TextRetrievalStrategy(rows, scoring='bm25').retrieve(**query)
