"""Small deterministic skill baseline exposed for subsequent evaluation."""
import re

SKILLS = ('Java', 'JavaScript', 'TypeScript', 'Python', 'C++', 'C#', 'Go', 'SQL',
          'MySQL', 'PostgreSQL', 'Redis', 'MongoDB', 'Spring', 'Spring Boot',
          'Django', 'Flask', 'React', 'Vue', 'Docker', 'Kubernetes', 'Linux',
          'Git', 'HTTP', 'TCP', 'Kafka', 'RabbitMQ', 'Elasticsearch', '算法',
          '数据结构', '数据库', '并发', '网络', '测试', '机器学习')


def skills(text):
    return [skill for skill in SKILLS if re.search(
        (r'(?<![A-Za-z0-9_])' + re.escape(skill) + r'(?![A-Za-z0-9_])')
        if skill[0].isascii() else re.escape(skill), text, re.I)]


class ResumeMatcher:
    def match(self, *, jd_text, snapshot):
        fields = {key: snapshot[key] for key in ('skills', 'self_evaluation')}
        for group in ('educations', 'experiences', 'projects', 'certificates', 'awards'):
            for row in snapshot[group]:
                for key, value in row.items():
                    if key != 'id' and isinstance(value, str):
                        fields[f'{group}.{row["id"]}.{key}'] = value
        required = skills(jd_text)
        evidence = []
        matches, gaps = [], []
        for skill in required:
            found = next(((path, text) for path, text in fields.items() if skill in skills(text)), None)
            (matches if found else gaps).append(skill)
            if found:
                start = found[1].casefold().find(skill.casefold())
                quote = found[1][max(0, start-30):start+len(skill)+60]
                evidence.append(dict(skill=skill, source_id=str(snapshot['id']),
                                     field_path=found[0], quote=quote))
        return dict(matches=matches, gaps=gaps, evidence=evidence, version='skills-v1')
