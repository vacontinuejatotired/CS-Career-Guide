"""逐题反馈的纯校验组件；不调用模型、不读写数据库。

snapshot 必须来自服务端保存的已下发题快照，不能使用客户端提供的依据。
校验通过只能证明引用来自输入，不能证明模型对回答的语义判断正确。
"""
from copy import deepcopy


class InvalidFeedback(ValueError):
    """模型反馈不符合逐题证据约定；异常不携带原始模型内容。"""


def resolve_model_feedback(*, answer: str, snapshot: dict, feedback: dict) -> dict:
    """模型选择要点序号，服务端从快照组装引用；旧完整格式仍须严格校验。"""
    fields = {'answer_quote', 'covered_indices', 'missing_indices', 'follow_up'}
    if isinstance(feedback, dict) and set(feedback) == fields:
        points = snapshot.get('key_points', [])
        covered, missing = feedback['covered_indices'], feedback['missing_indices']
        for indices in (covered, missing):
            if (not isinstance(indices, list) or
                any(type(index) is not int or not 0 <= index < len(points) for index in indices) or
                len(indices) != len(set(indices))):
                raise InvalidFeedback('反馈要点序号无效')
        if set(covered).intersection(missing) or not covered + missing:
            raise InvalidFeedback('反馈要点序号冲突或为空')
        sources = snapshot.get('evidence', [])
        evidence = []
        for index in covered + missing:
            match = next((e for e in sources if e.get('source_id') == str(snapshot.get('question_id'))
                          and e.get('field_path') == f'key_points[{index}]' and e.get('quote') == points[index]), None)
            if match is None:
                raise InvalidFeedback('快照缺少要点依据')
            evidence.append(deepcopy(match))
        feedback = {'answer_quote': feedback['answer_quote'],
                    'key_points_covered': [points[i] for i in covered],
                    'missing_points': [points[i] for i in missing],
                    'evidence': evidence, 'follow_up': feedback['follow_up']}
    return validate_feedback(answer=answer, snapshot=snapshot, feedback=feedback)


def validate_feedback(*, answer: str, snapshot: dict, feedback: dict) -> dict:
    """返回隔离副本；不修补、不猜测或自动接受模型多余字段。"""
    def require(condition):
        if not condition:
            raise InvalidFeedback('反馈结构或引用依据不符合要求')

    require(isinstance(answer, str) and bool(answer.strip()))
    require(isinstance(snapshot, dict))
    points = snapshot.get('key_points')
    sources = snapshot.get('evidence')
    require(isinstance(points, list) and all(isinstance(p, str) and p.strip() for p in points))
    require(isinstance(sources, list))
    fields = {'answer_quote', 'key_points_covered', 'missing_points', 'evidence', 'follow_up'}
    require(isinstance(feedback, dict) and set(feedback) == fields)
    quote = feedback['answer_quote']
    require(isinstance(quote, str) and bool(quote.strip()) and quote in answer)
    covered = feedback['key_points_covered']
    missing = feedback['missing_points']
    for values in (covered, missing):
        require(isinstance(values, list))
        require(all(isinstance(value, str) and value in points for value in values))
        require(len(values) == len(set(values)))
    require(not set(covered).intersection(missing))
    evidence = feedback['evidence']
    require(isinstance(evidence, list) and bool(evidence))
    for item in evidence:
        require(isinstance(item, dict) and set(item) == {'source_id', 'field_path', 'quote'})
        require(all(isinstance(value, str) and bool(value.strip()) for value in item.values()))
        require(item in sources)
        # 仅有来源说明或题干不构成参考要点的反馈依据。
        path = item['field_path']
        require(path.startswith('key_points[') and path.endswith(']'))
        index_text = path[len('key_points['):-1]
        require(index_text.isascii() and index_text.isdecimal())
        index = int(index_text)
        require(index < len(points) and path == f'key_points[{index}]')
        require(item['quote'] == points[index])
        require(item['source_id'] == str(snapshot.get('question_id')))
    require(all(any(item['quote'] == point for item in evidence) for point in covered + missing))
    # Existing HTTP contract exposes a generated text suggestion, never a catalog ID.
    require(feedback['follow_up'] is None or
            (isinstance(feedback['follow_up'], str) and bool(feedback['follow_up'].strip())
             and len(feedback['follow_up']) <= 2000))
    return deepcopy(feedback)
