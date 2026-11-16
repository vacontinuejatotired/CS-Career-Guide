"""Conservative extractive editing, not a general semantic fact verifier."""
import copy
import re
from uuid import UUID

EDITABLE_FIELDS = ('skills', 'self_evaluation')
STAR_LABELS = {'situation': '背景', 'task': '任务', 'action': '行动', 'result': '结果'}
STAR_QUESTIONS = {'situation': '项目背景是什么？', 'task': '你承担什么任务？',
                  'action': '你具体做了什么？', 'result': '有什么可核实结果？没有数字也可描述实际完成情况。'}
# These editing words may change; the remaining normalized text must be equal.
# This is an intentionally narrow lexical check, not semantic fact verification.
CONNECTORS = ('使用', '运用', '采用', '完成', '开发', '实现', '进行', '以及', '并且', '通过', '包括', '的', '了', '与', '和')


def core(text):
    text = text.casefold()
    for word in CONNECTORS:
        text = text.replace(word, '')
    return re.sub(r'[\s，。；、：！？,.!;:?（）()【】\[\]"\'\-]+', '', text)


def validate_edit(original, suggested):
    if not isinstance(suggested, str) or not suggested.strip() or len(suggested) > 20000:
        raise ValueError('invalid suggested text')
    # Keep numbers, units and their order; punctuation normalization must not turn
    # 1.0 into 10, or erase a negative sign / percentage.
    numbers = lambda s: re.findall(r'[-+]?\d+(?:\.\d+)?\s*[%％]?', s)
    if numbers(suggested) != numbers(original):
        raise ValueError('changed numeric facts')
    source, target = core(original), core(suggested)
    if not target or target != source:
        raise ValueError('unsupported rewrite; retain original factual phrases')
    return suggested


def validate_result(snapshot, result):
    if (not isinstance(result, dict) or not {'matches', 'gaps', 'suggestions'} <= set(result)
            or set(result) - {'matches', 'gaps', 'suggestions', 'star_reviews'}):
        raise ValueError('invalid result fields')
    for key in ('matches', 'gaps'):
        if not isinstance(result[key], list) or len(result[key]) > 100 or any(
                not isinstance(item, str) or not item.strip() or len(item) > 200 for item in result[key]):
            raise ValueError('invalid matching result')
    suggestions = result['suggestions']
    if not isinstance(suggestions, list) or len(suggestions) > 20:
        raise ValueError('invalid suggestions')
    ids, fields = set(), set()
    for item in suggestions:
        if not isinstance(item, dict) or set(item) != {'id', 'field_path', 'original', 'suggested', 'reason', 'evidence'}:
            raise ValueError('invalid suggestion fields')
        sid = str(UUID(str(item['id'])))
        field = item['field_path']
        if field not in EDITABLE_FIELDS or field in fields or sid in ids:
            raise ValueError('invalid or duplicate target')
        original = snapshot[field]
        if not original.strip() or item['original'] != original:
            raise ValueError('original must match snapshot')
        validate_edit(original, item['suggested'])
        if not isinstance(item['reason'], str) or not item['reason'].strip() or len(item['reason']) > 120:
            raise ValueError('invalid reason')
        evidence = item['evidence']
        if not isinstance(evidence, list) or not 1 <= len(evidence) <= 10:
            raise ValueError('missing evidence')
        for row in evidence:
            if not isinstance(row, dict) or set(row) != {'source_id', 'field_path', 'quote'}:
                raise ValueError('invalid evidence')
            if (row['source_id'] != str(snapshot['id']) or row['field_path'] != field
                    or not isinstance(row['quote'], str) or not row['quote'].strip()
                    or row['quote'] not in original):
                raise ValueError('evidence must quote original target field')
        ids.add(sid)
        fields.add(field)
    clean = copy.deepcopy(result)
    for item in clean['suggestions']:
        item['id'] = str(UUID(str(item['id'])))
    clean['star_reviews'] = resolve_star(snapshot, result.get('star_reviews', []))
    return clean


def resolve_star(snapshot, reviews):
    """STAR slots contain only verbatim excerpts; missing facts remain questions."""
    sources = {}
    for group in ('projects', 'experiences'):
        for row in snapshot[group]:
            if row.get('description'):
                sources[f'{group}.{row["id"]}.description'] = row
    if not isinstance(reviews, list) or len(reviews) > 20:
        raise ValueError('invalid STAR review')
    indexed = {}
    for row in reviews:
        if not isinstance(row, dict) or set(row) != {'field_path', *STAR_LABELS}:
            raise ValueError('invalid STAR fields')
        path = row['field_path']
        if not isinstance(path, str) or path not in sources or path in indexed:
            raise ValueError('invalid STAR source')
        quotes = []
        for key in STAR_LABELS:
            quote = row[key]
            if not isinstance(quote, str) or len(quote) > 120:
                raise ValueError('invalid STAR quote')
            if quote and (not quote.strip() or quote not in sources[path]['description'] or quote in quotes):
                raise ValueError('STAR facts must quote original experience')
            if quote:
                quotes.append(quote)
        indexed[path] = row
    output = []
    for path, source in list(sources.items())[:20]:
        review = indexed.get(path, {})
        sections = {key: review.get(key, '') for key in STAR_LABELS}
        missing = [key for key, value in sections.items() if not value]
        output.append(dict(field_path=path, source_id=str(snapshot['id']),
            label=source.get('name') or source.get('position') or '工作经历',
            sections=sections, missing=missing,
            questions=[STAR_QUESTIONS[key] for key in missing],
            text='\n'.join(f'{STAR_LABELS[key]}：{value}' for key, value in sections.items() if value)))
    return output
