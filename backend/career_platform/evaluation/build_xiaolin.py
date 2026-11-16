"""从已登记的943题生成冻结语料及初步评测集；不连接数据库或网络。

python -m career_platform.evaluation.build_xiaolin --source ../data/career-platform/xiaolincoding-questions.json
标签由集成时按题干选取，尚未经成员2独立复核，且不是穷尽相关性标注。
"""
import argparse
import hashlib
import json
from pathlib import Path

from .datasets import DATASET_DIR, fingerprint

SOURCE_SHA256 = 'd5b4d0834c70558d933367f71afe13453506c5499fc56819d2f463660b0f507c'
DISPLAY_SOURCE_SHA256 = '5c41c2a85e812e11529d5023db7598da2351ff50c4e229b099c88256e0d89fab'


SAMPLES = {
    'dev': [
        ('随机访问和头部插入分别适合 ArrayList 还是 LinkedList', 'ArrayList 和 LinkedList 的应用场景？'),
        ('volatile 能不能保证多线程的复合操作安全', 'volatile可以保证线程安全吗？'),
        ('项目里线程池接收任务以后怎么执行', '介绍一下线程池的工作原理'),
        ('如何防止多个线程互相等待造成死锁', '如何避免死锁？'),
        ('SpringBoot 自动装配是怎样完成的', 'SpringBoot自动装配原理是什么？'),
        ('Docker Compose 可以在哪些开发场景中使用', 'Docker Compose 是什么？什么场景用？'),
        ('CMS 和 G1 垃圾回收器的差别', '垃圾回收器 CMS 和 G1的区别？'),
        ('HTTP 502 与 504 分别代表什么故障', 'http 502和 504 的区别？'),
    ],
    'test': [
        ('ArrayList 容量不足时如何扩容', 'ArrayList的扩容机制说一下'),
        ('ConcurrentHashMap 怎样让并发写入安全', 'ConcurrentHashMap 是怎么保证线程安全的？'),
        ('synchronized 是不是可重入锁，原理是什么', 'synchronized 支持重入吗？如何实现的?'),
        ('有哪些条件同时满足时会发生死锁', '死锁发生条件是什么？'),
        ('Spring 中哪些调用方式会导致事务失效', 'Spring的事务什么情况下会失效？'),
        ('Docker 容器和虚拟机各有什么特点', 'Docker 和虚拟机有什么区别？'),
        ('Java 类被加载的过程分几个步骤', '讲一下类加载过程？'),
        ('HTTP 1.1 与 HTTP 2.0 有什么变化', 'Http1.1和2.0的区别是什么？'),
    ],
}


def build(source, destination=DATASET_DIR):
    raw = Path(source).read_bytes()
    if hashlib.sha256(raw).hexdigest() == DISPLAY_SOURCE_SHA256:
        # 仅接受已登记的943条展示来源缩写；重建v1时还原原始元数据，
        # 再校验原始整文件哈希。题干/答案/标签等任何其他变化仍被拒绝。
        raw = raw.replace(
            '"source": "小林coding · xiaolincoding.com"'.encode('utf-8'),
            '"source": "小林coding · xiaolincoding.com（成员1声明已获作者授权）"'.encode('utf-8'))
    if hashlib.sha256(raw).hexdigest() != SOURCE_SHA256:
        raise ValueError('源数据指纹已变化，请登记新的语料/评测版本，不覆盖v1快照')
    data = json.loads(raw)
    rows = data['questions']
    if len(rows) != 943 or len({q['dedupe_key'] for q in rows}) != 943:
        raise ValueError('源数据必须是943条具有唯一去重键的题目')
    if any(q['permission_status'] != 'allowed' or q['is_demo'] for q in rows):
        raise ValueError('冻结语料只接受 allowed 正式题目')
    questions = [dict(q, id=q['dedupe_key']) for q in rows]
    corpus = {'version': 'xiaolin-corpus-v1', 'source_sha256': hashlib.sha256(raw).hexdigest(),
              'id_namespace': 'dedupe_key；仅评测快照ID，不是线上数据库UUID',
              'questions': questions}
    by_question = {q['question']: q for q in questions}
    result = {'xiaolin-corpus-v1': corpus}
    for split, samples in SAMPLES.items():
        queries = []
        for index, (query, anchor) in enumerate(samples, 1):
            question = by_question[anchor]
            queries.append({'id': f'{split}-{index:02}', 'query': query,
                            'relevant_ids': [question['id']], 'group': 'relevant',
                            'topic': question['topic'], 'label_basis': anchor})
        unrelated = '紫菜蛋花汤怎么调味' if split == 'dev' else '周末如何给绣球花浇水'
        queries.append({'id': f'{split}-unrelated', 'query': unrelated,
                        'relevant_ids': [], 'group': 'unrelated'})
        version = f'xiaolin-eval-{split}-v1'
        result[version] = {'version': version, 'task': 'question', 'split': split,
                           'corpus_version': corpus['version'], 'corpus_sha256': fingerprint(corpus),
                           'corpus_ids': [q['id'] for q in questions],
                           'provenance': {'created': '2026-11-16', 'author': '集成助手初步整理',
                               'review': '未经过成员2独立人工复核；每条只指定一个锚题，不是穷尽相关性标注',
                               'scope': '仅离线检索回归；不含用户面试记录；不证明真实模型或线上质量'},
                           'queries': queries}
    destination = Path(destination)
    destination.mkdir(parents=True, exist_ok=True)
    for version, payload in result.items():
        (destination / f'{version}.json').write_text(
            json.dumps(payload, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    return result


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', required=True)
    args = parser.parse_args()
    build(args.source)
