import copy
import threading
from concurrent.futures import ThreadPoolExecutor
from unittest.mock import patch
from django.db import close_old_connections
from django.test import TransactionTestCase
from django.contrib.auth import get_user_model

from resumes.models import Resume, Project
from career_platform.models import ResumeAnalysisRun, ResumeApplyReceipt
from career_platform.tests.accept_support import AcceptanceCase, Gateway
from career_platform.tests.helpers import request_id, PREFIX
from .service import ResumeAnalysisService
from .validation import validate_edit
from career_platform.errors import Conflict


class ResumeRuntimeTests(AcceptanceCase):
    def setUp(self):
        super().setUp()
        self.resume = Resume.objects.create(user=self.user, skills='使用Java完成课程项目', self_evaluation='熟悉Python')
        self.sid = request_id()
        self.suggestion = dict(id=self.sid, field_path='skills', original=self.resume.skills,
            suggested='使用Java开发课程项目', reason='整理表达', evidence=[dict(
                source_id=str(self.resume.pk), field_path='skills', quote=self.resume.skills)])
        self.gateway = Gateway(dict(matches=['伪造技能'], gaps=[], suggestions=[self.suggestion]))
        self.wire(resume=ResumeAnalysisService(model_gateway=self.gateway))
        self.body = dict(jd_text='Java Redis', resume_revision=0, request_id=request_id())

    def analyze(self):
        return self.post('resume-analyses/', self.body)

    def application(self, run, **changes):
        return dict(base_revision=0, accepted_suggestion_ids=[self.sid], request_id=request_id(), **changes)

    def test_analysis_replay_conflict_and_authoritative_matching(self):
        row = self.analyze()
        self.assertEqual(row['result']['matches'], ['Java'])
        self.assertEqual(row['result']['gaps'], ['Redis'])
        self.assertEqual(self.analyze(), row)
        self.assertEqual(len(self.gateway.calls), 1)
        self.post('resume-analyses/', dict(self.body, jd_text='Python'), expected=409)
        self.assertEqual(ResumeAnalysisRun.objects.count(), 1)

    def test_general_analysis_without_jd_skips_matching_and_can_apply(self):
        del self.body['jd_text']
        with patch('career_platform.resume.matching.ResumeMatcher.match', side_effect=AssertionError('no JD matching')):
            row = self.analyze()
        self.assertEqual(row['jd_text'], '')
        self.assertEqual(row['result']['matches'], [])
        self.assertEqual(row['result']['gaps'], [])
        self.assertEqual(row['result']['matching']['version'], 'not-applicable')
        self.assertEqual(self.gateway.calls[0]['analysis_mode'], 'general')
        self.assertEqual(self.analyze(), row)
        self.post('resume-analyses/', dict(self.body, jd_text='Java'), expected=409)
        self.post(f"resume-analyses/{row['id']}/apply/", self.application(row))
        self.resume.refresh_from_db()
        self.assertEqual(self.resume.skills, self.suggestion['suggested'])
        self.assertEqual(self.resume.edit_revision, 1)

    def test_blank_jd_is_general_and_invalid_type_is_rejected(self):
        for text in ('', '   '):
            self.body.update(jd_text=text, request_id=request_id())
            self.assertEqual(self.analyze()['jd_text'], '')
        self.post('resume-analyses/', dict(self.body, jd_text=None), expected=400)

    def test_job_id_without_jd_keeps_source_permissions_and_rejects_empty_job(self):
        from company_reviews.models import Company, Job
        company = Company.objects.create(name='离线企业', city='演示', description='隔离测试')
        job = Job.objects.create(company=company, title='开发', requirements='Java Redis', permission_status='allowed')
        del self.body['jd_text']
        self.body['job_id'] = job.pk
        row = self.analyze()
        self.assertEqual(row['result']['gaps'], ['Redis'])
        self.assertEqual(self.gateway.calls[0]['analysis_mode'], 'job')
        job.permission_status = 'restricted'; job.save()
        self.body['request_id'] = request_id()
        self.post('resume-analyses/', self.body, expected=400)
        job.permission_status = 'allowed'; job.requirements = ''; job.save()
        self.post('resume-analyses/', self.body, expected=400)
        self.assertEqual(len(self.gateway.calls), 1)

    def test_star_gateway_receives_current_source_paths_without_fixed_example(self):
        project = Project.objects.create(id=438, resume=self.resume, name='课程', role='成员', period='2026',
            description='负责接口开发。使用Java完成选课接口。')
        self.gateway.result['star_reviews'] = [dict(field_path=f'projects.{project.pk}.description',
            situation='', task='负责接口开发。', action='使用Java完成选课接口。', result='')]
        row = self.analyze()
        from .service import SYSTEM
        call = self.gateway.calls[0]
        self.assertNotIn('projects.1.description', SYSTEM)
        self.assertEqual(call['star_sources'], [dict(field_path='projects.438.description',
            description=project.description)])
        self.assertEqual(call['analysis_mode'], 'job')
        self.assertEqual(row['result']['star_reviews'][0]['sections']['result'], '')

    def test_history_is_owned_and_preserves_snapshot(self):
        row = self.analyze()
        self.resume.skills = '新稿'; self.resume.save()
        detail = self.get(f"resume-analyses/{row['id']}/")
        self.assertEqual(detail['resume_snapshot']['skills'], self.suggestion['original'])
        self.assertEqual(self.get('resume-analyses/')['count'], 1)
        self.assertEqual(self.stranger.get(PREFIX+'resume-analyses/').data['count'], 0)
        self.assertEqual(self.stranger.get(PREFIX+f"resume-analyses/{row['id']}/").status_code, 404)
        self.assertEqual(self.stranger.post(PREFIX+f"resume-analyses/{row['id']}/apply/",
            self.application(row), format='json').status_code, 404)

    def test_model_timeout_and_unavailable_write_nothing(self):
        self.gateway.fail = True
        self.post('resume-analyses/', self.body, expected=504)
        self.assertEqual(ResumeAnalysisRun.objects.count(), 0)
        self.resume.refresh_from_db(); self.assertEqual(self.resume.edit_revision, 0)
        self.wire(resume=ResumeAnalysisService())
        self.post('resume-analyses/', self.body, expected=503)
        self.assertEqual(ResumeAnalysisRun.objects.count(), 0)

    def test_invalid_evidence_fields_duplicates_and_new_facts(self):
        cases = []
        for field, value in [('field_path', 'name'), ('original', '伪造原文'),
                             ('suggested', '使用Redis提升50%'), ('reason', '')]:
            item = copy.deepcopy(self.suggestion); item[field] = value; cases.append([item])
        item = copy.deepcopy(self.suggestion); item['evidence'][0]['source_id'] = 'other'; cases.append([item])
        item = copy.deepcopy(self.suggestion); item['evidence'][0]['quote'] = 'Redis'; cases.append([item])
        cases.append([copy.deepcopy(self.suggestion), copy.deepcopy(self.suggestion)])
        for suggestions in cases:
            with self.subTest(suggestions=suggestions):
                self.gateway.result['suggestions'] = suggestions
                self.post('resume-analyses/', self.body, expected=400)
                self.assertEqual(ResumeAnalysisRun.objects.count(), 0)

    def test_apply_edits_replay_and_same_key_different_payload(self):
        run = self.analyze()
        body = self.application(run, suggestion_edits={self.sid: '使用Java实现课程项目'})
        path = f"resume-analyses/{run['id']}/apply/"
        result = self.post(path, body)
        self.assertEqual(self.post(path, body), result)
        self.post(path, dict(body, suggestion_edits={}), expected=409)
        self.resume.refresh_from_db()
        self.assertEqual(self.resume.skills, '使用Java实现课程项目')
        self.assertEqual(self.resume.self_evaluation, '熟悉Python')
        self.assertEqual(self.resume.edit_revision, 1)
        self.assertEqual(ResumeApplyReceipt.objects.count(), 1)
        self.post(path, self.application(run), expected=409)

    def test_unselected_edit_duplicate_selection_and_unsupported_edit_zero_writes(self):
        run = self.analyze(); path = f"resume-analyses/{run['id']}/apply/"
        for body in (
            dict(self.application(run), accepted_suggestion_ids=[self.sid, self.sid]),
            self.application(run, suggestion_edits={request_id(): 'test'}),
            self.application(run, suggestion_edits={self.sid: '精通Redis'}),
            dict(self.application(run), accepted_suggestion_ids=[request_id()]),
        ):
            self.post(path, body, expected=400)
        self.resume.refresh_from_db(); self.assertEqual(self.resume.edit_revision, 0)
        self.assertEqual(ResumeApplyReceipt.objects.count(), 0)

    def test_child_change_without_parent_revision_is_still_detected(self):
        project = Project.objects.create(resume=self.resume, name='课程', role='成员', period='2026', description='Java')
        run = self.analyze()
        project.description = 'Python'; project.save()
        self.post(f"resume-analyses/{run['id']}/apply/", self.application(run), expected=409)
        self.assertEqual(ResumeApplyReceipt.objects.count(), 0)

    def test_change_during_generation_rejects_stale_analysis(self):
        def generate(**kwargs):
            self.resume.skills = '新的真实内容'; self.resume.save()
            return self.gateway.result
        with patch.object(self.gateway, 'generate', side_effect=generate):
            self.post('resume-analyses/', self.body, expected=409)
        self.assertEqual(ResumeAnalysisRun.objects.count(), 0)

    def test_no_resume_and_old_revision(self):
        self.post('resume-analyses/', dict(self.body, resume_revision=99), expected=409)
        self.resume.delete()
        self.post('resume-analyses/', self.body, expected=404)

    def test_empty_suggestions_valid_without_invented_output(self):
        self.gateway.result['suggestions'] = []
        self.assertEqual(self.analyze()['result']['suggestions'], [])

    def test_guard_retains_negation_numbers_and_new_skills(self):
        for original, edited in [('不熟悉Redis', '熟悉Redis'), ('提升1.0%', '提升10%'),
                                 ('Java', 'Java Redis'), ('负责测试', '主导测试'),
                                 ('熟悉Java，不熟悉Python', '不熟悉Java，熟悉Python')]:
            with self.subTest(original=original, edited=edited), self.assertRaises(ValueError):
                validate_edit(original, edited)
        self.assertEqual(validate_edit('使用Java完成课程项目', '使用Java实现课程项目'), '使用Java实现课程项目')

    def test_star_uses_verbatim_experience_and_leaves_result_missing(self):
        project = Project.objects.create(resume=self.resume, name='选课项目', role='成员', period='2026',
            description='课程选课项目。负责接口开发。使用Java完成选课接口。')
        self.gateway.result['star_reviews'] = [dict(field_path=f'projects.{project.pk}.description',
            situation='课程选课项目。', task='负责接口开发。', action='使用Java完成选课接口。', result='')]
        review = self.analyze()['result']['star_reviews'][0]
        self.assertEqual(review['missing'], ['result'])
        self.assertEqual(review['sections']['result'], '')
        self.assertNotIn('50%', review['text'])
        self.assertEqual(review['source_id'], str(self.resume.pk))
        project.refresh_from_db(); self.assertEqual(project.description, '课程选课项目。负责接口开发。使用Java完成选课接口。')

    def test_fabricated_star_results_wrong_paths_and_repeated_quotes_rejected(self):
        project = Project.objects.create(resume=self.resume, name='课程', role='成员', period='2026', description='使用Java完成课程项目')
        valid = dict(field_path=f'projects.{project.pk}.description', situation='', task='',
                     action=project.description, result='')
        for changes in (dict(result='性能提升50%'), dict(field_path='projects.999.description'),
                        dict(task=project.description)):
            self.gateway.result['star_reviews'] = [dict(valid, **changes)]
            self.post('resume-analyses/', self.body, expected=400)
        self.assertEqual(ResumeAnalysisRun.objects.count(), 0)


class ResumeConcurrentApplyTests(TransactionTestCase):
    def test_two_connections_never_apply_twice_and_original_key_recovers(self):
        user = get_user_model().objects.create_user(username='concurrent-resume')
        resume = Resume.objects.create(user=user, skills='使用Java完成课程项目')
        sid = request_id()
        gateway = Gateway(dict(matches=['Java'], gaps=[], suggestions=[dict(
            id=sid, field_path='skills', original=resume.skills, suggested='使用Java开发课程项目',
            reason='整理表达', evidence=[dict(source_id=str(resume.pk), field_path='skills', quote=resume.skills)])]))
        service = ResumeAnalysisService(model_gateway=gateway)
        row = service.analyze(user=user, data=dict(jd_text='Java', resume_revision=0, request_id=request_id()))
        body = dict(id=row['id'], base_revision=0, accepted_suggestion_ids=[sid], request_id=request_id())
        barrier = threading.Barrier(2)

        def apply():
            close_old_connections()
            try:
                barrier.wait(timeout=10)
                return service.apply(user=user, data=body)
            except Conflict:
                return 'conflict'
            finally:
                close_old_connections()

        with ThreadPoolExecutor(max_workers=2) as pool:
            results = list(pool.map(lambda _: apply(), range(2)))
        self.assertTrue(all(isinstance(item, dict) or item == 'conflict' for item in results))
        # SQLite may reject lock upgrades; an explicit same-key retry recovers.
        receipt = service.apply(user=user, data=body)
        self.assertEqual(service.apply(user=user, data=body), receipt)
        self.assertEqual(ResumeApplyReceipt.objects.count(), 1)
        resume.refresh_from_db(); self.assertEqual(resume.edit_revision, 1)
