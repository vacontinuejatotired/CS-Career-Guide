"""Resume analysis and confirmed application service."""

import copy
import re
import uuid

from django.core.exceptions import ValidationError as DjangoValidationError
from django.core.validators import URLValidator
from django.db import IntegrityError, transaction
from rest_framework.exceptions import NotFound, ValidationError

from company_reviews.models import Job
from resumes.models import Award, Certificate, Education, Experience, Project, Resume

from ..errors import Conflict, InvalidModelOutput, ModelTimeout, ModelUnavailable
from ..models import ResumeAnalysisRun, ResumeApplyReceipt


PROMPT_VERSION = 'resume-analysis-v1'
TOP_LEVEL_FIELDS = {'target_position', 'skills', 'self_evaluation'}
CHILD_FIELDS = {
    'education': (Education, {'school', 'major', 'period', 'description'}),
    'educations': (Education, {'school', 'major', 'period', 'description'}),
    'experience': (Experience, {'company', 'position', 'period', 'description'}),
    'experiences': (Experience, {'company', 'position', 'period', 'description'}),
    'project': (Project, {'name', 'role', 'period', 'url', 'description'}),
    'projects': (Project, {'name', 'role', 'period', 'url', 'description'}),
    'certificate': (Certificate, {'name', 'issuer', 'period', 'description'}),
    'certificates': (Certificate, {'name', 'issuer', 'period', 'description'}),
    'award': (Award, {'name', 'issuer', 'period', 'description'}),
    'awards': (Award, {'name', 'issuer', 'period', 'description'}),
}
SNAPSHOT_COLLECTIONS = {
    'education': 'educations', 'educations': 'educations',
    'experience': 'experiences', 'experiences': 'experiences',
    'project': 'projects', 'projects': 'projects',
    'certificate': 'certificates', 'certificates': 'certificates',
    'award': 'awards', 'awards': 'awards',
}


def _iso(value):
    if value is None:
        return None
    text = value.isoformat()
    return text[:-6] + 'Z' if text.endswith('+00:00') else text


def _child_rows(manager, fields):
    return [
        {'id': row.id, **{field: getattr(row, field) or '' for field in fields}}
        for row in manager.all().order_by('id')
    ]


class ResumeAnalysisService:
    def __init__(self, *, model_gateway=None, matcher=None, repository=None):
        self.model_gateway = model_gateway
        self.matcher = matcher
        self.repository = repository

    def analyze(self, *, user, data: dict) -> dict:
        resume = Resume.objects.filter(user=user).first()
        if resume is None:
            raise NotFound()

        existing = ResumeAnalysisRun.objects.filter(user=user, request_id=data['request_id']).first()
        if existing is not None:
            if not self._same_analysis(existing, resume, data):
                raise Conflict('同一 request_id 不能用于不同分析输入')
            return self._serialize_run(existing)

        if resume.edit_revision != data['resume_revision']:
            raise Conflict('简历版本已变化，请重新分析')

        job, job_snapshot = self._analysis_job(data.get('job_id'))
        snapshot = self._resume_snapshot(resume)
        pending, should_generate = self._reserve_analysis(user, resume, data, snapshot, job_snapshot)
        if not should_generate:
            return self._serialize_run(pending)
        try:
            if self.model_gateway is None:
                raise ModelUnavailable()
            try:
                result = self.model_gateway.generate(
                    system=(
                        '你是简历分析助手。只依据输入的简历快照和 JD 提取匹配项、缺口和可改写建议。'
                        '不得新增候选人未提供的技能、经历或数字。返回 JSON：'
                        '{"matches":["..."],"gaps":["..."],"suggestions":['
                        '{"id":"UUID","field_path":"字段路径","original":"原文",'
                        '"suggested":"建议文本","reason":"原因","evidence":['
                        '{"source_id":"来源ID","field_path":"字段路径","quote":"原文引文"}]}]}。'
                        'field_path 只能使用现有字段或当前简历子记录；建议不得写到姓名、电话、邮箱、地址、头像或用户字段。'
                    ),
                    payload={
                        'resume': copy.deepcopy(snapshot),
                        'jd_text': data['jd_text'],
                        'job': copy.deepcopy(job_snapshot),
                    },
                )
            except TimeoutError as exc:
                raise ModelTimeout() from exc
            except ValueError as exc:
                raise InvalidModelOutput() from exc
            except Exception as exc:
                raise ModelUnavailable() from exc

            validated = self._validate_result(result, snapshot, data['jd_text'], job_snapshot)
            with transaction.atomic():
                resume = Resume.objects.select_for_update().filter(user=user, pk=resume.pk).first()
                if resume is None:
                    raise NotFound()
                if resume.edit_revision != data['resume_revision']:
                    raise Conflict('分析期间简历已更新，请重新分析')
                pending = ResumeAnalysisRun.objects.select_for_update().get(pk=pending.pk)
                pending.status = 'succeeded'
                pending.failure_code = ''
                pending.result = validated
                pending.model_version = self._model_version()
                pending.prompt_version = PROMPT_VERSION
                pending.save(update_fields=[
                    'status', 'failure_code', 'result', 'model_version', 'prompt_version', 'updated_at',
                ])
        except Exception:
            ResumeAnalysisRun.objects.filter(pk=pending.pk, user=user).delete()
            raise
        return self._serialize_run(pending)

    def list_runs(self, *, user, data: dict) -> dict:
        queryset = ResumeAnalysisRun.objects.filter(user=user)
        if data.get('q'):
            queryset = queryset.filter(jd_text__icontains=data['q'])
        queryset = queryset.order_by('-created_at', '-id')
        count = queryset.count()
        page = data.get('page', 1)
        page_size = data.get('page_size', 20)
        rows = queryset[(page - 1) * page_size:page * page_size]
        return {
            'count': count,
            'page': page,
            'page_size': page_size,
            'results': [self._serialize_run(row, compact=True) for row in rows],
        }

    def get_run(self, *, user, data: dict) -> dict:
        run = ResumeAnalysisRun.objects.filter(user=user, pk=data['id']).first()
        if run is None:
            raise NotFound()
        return self._serialize_run(run)

    def apply(self, *, user, data: dict) -> dict:
        request_payload = self._apply_payload(data)
        existing = ResumeApplyReceipt.objects.filter(user=user, request_id=data['request_id']).first()
        if existing is not None:
            if existing.input_payload != request_payload:
                raise Conflict('同一 request_id 不能用于不同应用输入')
            return self._serialize_receipt(existing)

        with transaction.atomic():
            resume = Resume.objects.select_for_update().filter(user=user).first()
            if resume is None:
                raise NotFound()
            analysis = (
                ResumeAnalysisRun.objects.select_for_update()
                .filter(user=user, pk=data['id'], resume_id=resume.pk)
                .first()
            )
            if analysis is None:
                raise NotFound()
            receipt = ResumeApplyReceipt.objects.select_for_update().filter(
                user=user, request_id=data['request_id'],
            ).first()
            if receipt is not None:
                if receipt.input_payload != request_payload:
                    raise Conflict('同一 request_id 不能用于不同应用输入')
                return self._serialize_receipt(receipt)
            if analysis.base_revision != resume.edit_revision or data['base_revision'] != resume.edit_revision:
                raise Conflict('简历版本已变化，请基于最新版本重新分析')

            accepted_ids = [str(value) for value in data['accepted_suggestion_ids']]
            if len(set(accepted_ids)) != len(accepted_ids):
                raise ValidationError({'accepted_suggestion_ids': '建议不能重复'})
            suggestions = self._suggestion_map(analysis.result.get('suggestions'))
            if any(key not in suggestions for key in accepted_ids):
                raise ValidationError({'accepted_suggestion_ids': '包含不存在的建议'})
            edits = {str(key): str(value) for key, value in (data.get('suggestion_edits') or {}).items()}
            if any(key not in accepted_ids for key in edits):
                raise ValidationError({'suggestion_edits': '只能编辑已接受的建议'})

            top_level_changes = {}
            child_changes = []
            for suggestion_id in accepted_ids:
                suggestion = suggestions[suggestion_id]
                path = suggestion['field_path']
                target = self._resolve_path(analysis.resume_snapshot, path)
                current_original = str(target['value'] or '')
                if suggestion['original'] != current_original:
                    raise ValidationError({'field_path': f'{path} 的原文已变化'})
                final_text = edits.get(suggestion_id, suggestion['suggested']).strip()
                if not final_text:
                    raise ValidationError({'suggestion_edits': '建议文本不能为空'})
                self._validate_facts(suggestion['original'], final_text)
                self._validate_field_value(target, final_text)
                if target['kind'] == 'top':
                    top_level_changes[target['field']] = final_text
                else:
                    child_changes.append((target, final_text))

            for target, value in child_changes:
                row = (
                    target['model'].objects.select_for_update()
                    .filter(pk=target['row_id'], resume=resume)
                    .first()
                )
                if row is None:
                    raise ValidationError({'field_path': '建议对应的简历子记录不存在'})
                if str(getattr(row, target['field']) or '') != str(target['value'] or ''):
                    raise ValidationError({'field_path': '建议对应的简历子记录已变化'})
                setattr(row, target['field'], value)
                row.save(update_fields=[target['field']])

            for field, value in top_level_changes.items():
                setattr(resume, field, value)
            resume.save(update_fields=set(top_level_changes) | {'edit_revision'})
            resume.refresh_from_db(fields=['edit_revision'])
            receipt = ResumeApplyReceipt.objects.create(
                user=user,
                request_id=data['request_id'],
                analysis=analysis,
                status='succeeded',
                accepted_suggestion_ids=accepted_ids,
                applied_revision=resume.edit_revision,
                input_payload=request_payload,
            )
            return self._serialize_receipt(receipt)

    def _reserve_analysis(self, user, resume, data, snapshot, job_snapshot):
        try:
            run = ResumeAnalysisRun.objects.create(
                user=user,
                request_id=data['request_id'],
                resume=resume,
                base_revision=resume.edit_revision,
                resume_snapshot=snapshot,
                jd_text=data['jd_text'],
                job_snapshot=job_snapshot,
                status='pending',
                prompt_version=PROMPT_VERSION,
            )
            return run, True
        except IntegrityError:
            existing = ResumeAnalysisRun.objects.get(user=user, request_id=data['request_id'])
            if not self._same_analysis(existing, resume, data):
                raise Conflict('同一 request_id 不能用于不同分析输入')
            return existing, False

    def _analysis_job(self, job_id):
        if not job_id:
            return None, {}
        job = Job.objects.select_related('company').filter(pk=job_id).first()
        if job is None:
            raise NotFound()
        if job.permission_status != 'allowed':
            raise ValidationError({'job_id': '岗位来源未获允许'})
        return job, {
            'id': job.id,
            'title': job.title,
            'company': job.company.name,
            'description': job.description or job.requirements or '',
            'requirements': job.requirements or '',
            'skills': copy.deepcopy(job.skills or []),
            'city': job.city or '',
            'source': job.source or '',
            'source_url': job.source_url or '',
            'permission_status': job.permission_status,
            'collected_at': _iso(job.collected_at),
            'is_demo': bool(job.is_demo),
        }

    @staticmethod
    def _resume_snapshot(resume):
        return {
            'id': resume.id,
            'edit_revision': resume.edit_revision,
            'target_position': resume.target_position or '',
            'skills': resume.skills or '',
            'self_evaluation': resume.self_evaluation or '',
            'educations': _child_rows(
                resume.education, ('school', 'major', 'period', 'description'),
            ),
            'experiences': _child_rows(
                resume.experience, ('company', 'position', 'period', 'description'),
            ),
            'projects': _child_rows(
                resume.projects, ('name', 'role', 'period', 'url', 'description'),
            ),
            'certificates': _child_rows(
                resume.certificates, ('name', 'issuer', 'period', 'description'),
            ),
            'awards': _child_rows(
                resume.awards, ('name', 'issuer', 'period', 'description'),
            ),
        }

    @staticmethod
    def _same_analysis(run, resume, data):
        job_id = run.job_snapshot.get('id') if run.job_snapshot else None
        return (
            run.resume_id == resume.id
            and run.base_revision == data['resume_revision']
            and run.jd_text == data['jd_text']
            and job_id == data.get('job_id')
        )

    @staticmethod
    def _apply_payload(data):
        return {
            'analysis_id': str(data['id']),
            'base_revision': data['base_revision'],
            'accepted_suggestion_ids': sorted(str(value) for value in data['accepted_suggestion_ids']),
            'suggestion_edits': {
                str(key): str(value) for key, value in (data.get('suggestion_edits') or {}).items()
            },
        }

    def _validate_result(self, result, snapshot, jd_text, job_snapshot):
        if not isinstance(result, dict):
            raise ValidationError({'result': '模型结果必须是对象'})
        validated = {}
        for key in ('matches', 'gaps'):
            values = result.get(key)
            if not isinstance(values, list) or not all(isinstance(value, str) for value in values):
                raise ValidationError({'result': f'{key} 必须是文本数组'})
            validated[key] = values
        suggestions = result.get('suggestions')
        if not isinstance(suggestions, list):
            raise ValidationError({'result': 'suggestions 必须是数组'})
        normalized = []
        seen = set()
        for suggestion in suggestions:
            if not isinstance(suggestion, dict):
                raise ValidationError({'result': '建议必须是对象'})
            suggestion_id = str(suggestion.get('id') or '')
            path = suggestion.get('field_path')
            original = suggestion.get('original')
            suggested = suggestion.get('suggested')
            reason = suggestion.get('reason')
            evidence = suggestion.get('evidence')
            if not suggestion_id or suggestion_id in seen:
                raise ValidationError({'result': '建议 ID 缺失或重复'})
            try:
                uuid.UUID(suggestion_id)
            except ValueError:
                raise ValidationError({'result': '建议 ID 必须是 UUID'})
            seen.add(suggestion_id)
            if not isinstance(path, str) or not isinstance(original, str) or not isinstance(suggested, str):
                raise ValidationError({'result': '建议字段格式无效'})
            if not isinstance(reason, str) or not isinstance(evidence, list) or not evidence:
                raise ValidationError({'result': '建议必须包含理由和证据'})
            target = self._resolve_path(snapshot, path)
            if original != str(target['value'] or ''):
                raise ValidationError({'result': f'{path} 的 original 与快照不一致'})
            self._validate_field_value(target, suggested)
            self._validate_facts(original, suggested)
            normalized_evidence = self._validate_evidence(
                evidence, snapshot=snapshot, jd_text=jd_text, job_snapshot=job_snapshot,
            )
            normalized.append({
                'id': suggestion_id,
                'field_path': path,
                'original': original,
                'suggested': suggested,
                'reason': reason,
                'evidence': normalized_evidence,
            })
        validated['suggestions'] = normalized
        return validated

    def _validate_evidence(self, evidence, *, snapshot, jd_text, job_snapshot):
        normalized = []
        for item in evidence:
            if not isinstance(item, dict):
                raise ValidationError({'result': '证据必须是对象'})
            source_id = str(item.get('source_id') or '')
            field_path = item.get('field_path')
            quote = item.get('quote')
            if not source_id or not isinstance(field_path, str) or not isinstance(quote, str) or not quote:
                raise ValidationError({'result': '证据字段不完整'})
            if source_id == str(snapshot['id']):
                value = str(self._resolve_path(snapshot, field_path)['value'] or '')
                if quote not in value:
                    raise ValidationError({'result': '证据引文不在简历快照中'})
            elif any(
                str(row.get('id')) == source_id and field_path in row
                for collection in SNAPSHOT_COLLECTIONS.values()
                for row in snapshot.get(collection, [])
            ):
                row = next(
                    row
                    for collection in SNAPSHOT_COLLECTIONS.values()
                    for row in snapshot.get(collection, [])
                    if str(row.get('id')) == source_id and field_path in row
                )
                if quote not in str(row.get(field_path) or ''):
                    raise ValidationError({'result': '证据引文不在简历子记录中'})
            elif job_snapshot and source_id == str(job_snapshot.get('id')):
                if field_path in {'jd_text', 'description', 'requirements'}:
                    value = (
                        jd_text + '\n' + str(job_snapshot.get('description', ''))
                        + '\n' + str(job_snapshot.get('requirements', ''))
                    )
                elif field_path in job_snapshot:
                    value = str(job_snapshot[field_path])
                else:
                    raise ValidationError({'result': '岗位证据路径无效'})
                if quote not in value:
                    raise ValidationError({'result': '证据引文不在岗位快照中'})
            elif source_id in {'jd', 'input', 'jd_text'} and field_path in {'jd_text', 'description'}:
                if quote not in jd_text:
                    raise ValidationError({'result': '证据引文不在 JD 中'})
            else:
                raise ValidationError({'result': '证据来源不属于本次快照'})
            normalized.append({'source_id': source_id, 'field_path': field_path, 'quote': quote})
        return normalized

    def _resolve_path(self, snapshot, path):
        if path in TOP_LEVEL_FIELDS:
            return {
                'kind': 'top',
                'field': path,
                'value': snapshot.get(path, ''),
                'label': path,
            }
        parts = path.split('.') if isinstance(path, str) else []
        if len(parts) != 3:
            raise ValidationError({'field_path': '不允许的简历字段路径'})
        collection, row_id_text, field = parts
        if collection not in CHILD_FIELDS or field not in CHILD_FIELDS[collection][1]:
            raise ValidationError({'field_path': '不允许的简历字段路径'})
        try:
            row_id = int(row_id_text)
        except ValueError:
            raise ValidationError({'field_path': '简历子记录 ID 无效'})
        row = next(
            (item for item in snapshot.get(SNAPSHOT_COLLECTIONS[collection], []) if item.get('id') == row_id),
            None,
        )
        if row is None:
            raise ValidationError({'field_path': '简历子记录不存在'})
        return {
            'kind': 'child',
            'model': CHILD_FIELDS[collection][0],
            'row_id': row_id,
            'field': field,
            'value': row.get(field, ''),
            'label': path,
        }

    @staticmethod
    def _validate_field_value(target, value):
        if not isinstance(value, str):
            raise ValidationError({'suggested': '建议文本必须是字符串'})
        model_field = (
            target['model']._meta.get_field(target['field'])
            if target['kind'] == 'child'
            else Resume._meta.get_field(target['field'])
        )
        if model_field is not None and model_field.max_length and len(value) > model_field.max_length:
            raise ValidationError({'suggested': f'{target["field"]} 超出长度限制'})
        if target['kind'] == 'child' and target['field'] == 'url' and value:
            try:
                URLValidator()(value)
            except DjangoValidationError:
                raise ValidationError({'suggested': '项目链接必须是有效 URL'})

    @staticmethod
    def _validate_facts(original, suggested):
        source = original or ''
        numbers = re.findall(r'(?<![A-Za-z])\d+(?:\.\d+)?%?', suggested)
        if any(number not in source for number in numbers):
            raise ValidationError({'suggested': '建议包含原文没有的数字或事实'})
        tokens = re.findall(r'[A-Za-z][A-Za-z0-9+#._-]*', suggested)
        source_lower = source.lower()
        if any(token.lower() not in source_lower for token in tokens):
            raise ValidationError({'suggested': '建议包含原文没有的技能或事实'})

    @staticmethod
    def _suggestion_map(suggestions):
        mapping = {}
        for suggestion in suggestions if isinstance(suggestions, list) else []:
            if isinstance(suggestion, dict) and suggestion.get('id'):
                mapping[str(suggestion['id'])] = suggestion
        return mapping

    def _model_version(self):
        if self.model_gateway is None:
            return ''
        return str(getattr(self.model_gateway, 'model_version', 'json-model-gateway-v1'))

    @staticmethod
    def _serialize_run(run, compact=False):
        result = {
            'id': str(run.id),
            'status': run.status,
            'failure_code': run.failure_code,
            'base_revision': run.base_revision,
            'created_at': _iso(run.created_at),
            'updated_at': _iso(run.updated_at),
            'model_version': run.model_version,
            'prompt_version': run.prompt_version,
        }
        if compact:
            result.update({
                'jd_text': run.jd_text,
                'matches': copy.deepcopy((run.result or {}).get('matches', [])),
                'gaps': copy.deepcopy((run.result or {}).get('gaps', [])),
                'suggestion_count': len((run.result or {}).get('suggestions', [])),
            })
        else:
            result.update({
                'resume_snapshot': copy.deepcopy(run.resume_snapshot or {}),
                'jd_text': run.jd_text,
                'job_snapshot': copy.deepcopy(run.job_snapshot or {}),
                'result': copy.deepcopy(run.result or {}),
            })
        return result

    @staticmethod
    def _serialize_receipt(receipt):
        return {
            'id': str(receipt.id),
            'analysis_id': str(receipt.analysis_id),
            'status': receipt.status,
            'accepted_suggestion_ids': copy.deepcopy(receipt.accepted_suggestion_ids or []),
            'applied_revision': receipt.applied_revision,
            'created_at': _iso(receipt.created_at),
            'updated_at': _iso(receipt.updated_at),
        }
