"""Uploaded-resume ownership and two-file limit, isolated from MySQL and model calls."""

import tempfile
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from rest_framework.authtoken.models import Token

from resumes.models import ResumeUpload
from ai_integration.interview.resume_selection import resolve_interview_resume
from ai_integration.interview.service import RESUME_MODE_ATTACHED, RESUME_MODE_NONE


class ResumeUploadTests(TestCase):
    @classmethod
    def setUpClass(cls):
        cls._media = tempfile.TemporaryDirectory()
        cls._override = override_settings(MEDIA_ROOT=cls._media.name)
        cls._override.enable()
        super().setUpClass()

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        cls._override.disable()
        cls._media.cleanup()

    @classmethod
    def setUpTestData(cls):
        cls.user = get_user_model().objects.create_user(username='resume-owner', password='test-password')
        cls.other = get_user_model().objects.create_user(username='resume-other', password='test-password')
        cls.token = Token.objects.create(user=cls.user)
        cls.other_token = Token.objects.create(user=cls.other)

    def headers(self, token=None):
        return {'HTTP_AUTHORIZATION': f'Token {(token or self.token).key}'}

    def upload(self, name='sample.pdf', token=None):
        file = SimpleUploadedFile(name, b'%PDF-1.7\nresume', content_type='application/pdf')
        return self.client.post(
            '/api/resumes/uploads/',
            {'file': file},
            **self.headers(token),
        )

    def test_upload_parse_list_and_two_file_limit(self):
        parsed = {
            'target_role': '开发',
            'years': '',
            'skills': 'Python',
            'education': [],
            'experience': [],
            'projects': [],
            'degraded': False,
        }
        with patch('resumes.views.parse_resume_file', return_value=parsed):
            first = self.upload()
            second = self.upload('second.pdf')
            third = self.upload('third.pdf')

        self.assertEqual(first.status_code, 201, first.content)
        self.assertEqual(second.status_code, 201, second.content)
        self.assertEqual(third.status_code, 409, third.content)
        self.assertEqual(third.json()['code'], 'RESUME_UPLOAD_LIMIT')
        self.assertIn('请先删除旧简历', third.json()['error'])

        listed = self.client.get('/api/resumes/uploads/', **self.headers())
        self.assertEqual(listed.status_code, 200, listed.content)
        self.assertEqual(listed.json()['count'], 2)
        self.assertEqual(
            {item['file_name'] for item in listed.json()['results']},
            {'sample.pdf', 'second.pdf'},
        )
        self.assertFalse(any('parsed' in item for item in listed.json()['results']))

    def test_uploads_are_user_scoped_and_delete_removes_file(self):
        with patch('resumes.views.parse_resume_file', return_value={'target_role': '开发', 'degraded': False}):
            created = self.upload()
        upload_id = created.json()['upload']['id']
        upload = ResumeUpload.objects.get(pk=upload_id)
        stored_path = Path(upload.file.path)
        self.assertTrue(stored_path.exists())

        forbidden = self.client.delete(
            f'/api/resumes/uploads/{upload_id}/',
            **self.headers(self.other_token),
        )
        self.assertEqual(forbidden.status_code, 404, forbidden.content)
        self.assertTrue(ResumeUpload.objects.filter(pk=upload_id).exists())

        deleted = self.client.delete(
            f'/api/resumes/uploads/{upload_id}/',
            **self.headers(),
        )
        self.assertEqual(deleted.status_code, 200, deleted.content)
        self.assertFalse(ResumeUpload.objects.filter(pk=upload_id).exists())
        self.assertFalse(stored_path.exists())

    def test_interview_selection_uses_only_the_users_parsed_upload(self):
        upload = ResumeUpload.objects.create(
            user=self.user,
            file='resumes/test-selection.pdf',
            file_name='selection.pdf',
            parsed={
                'target_role': '开发',
                'years': '',
                'skills': 'Python',
                'education': [],
                'experience': [],
                'projects': [],
                'degraded': False,
            },
        )
        platform_context, platform_mode, error = resolve_interview_resume(
            SimpleNamespace(user=self.user), 'platform', None,
        )
        self.assertIsNone(platform_context)
        self.assertEqual(platform_mode, RESUME_MODE_NONE)
        self.assertIsNone(error)

        context, mode, error = resolve_interview_resume(
            SimpleNamespace(user=self.user), 'uploaded', str(upload.id),
        )
        self.assertEqual(mode, RESUME_MODE_ATTACHED)
        self.assertIsNone(error)
        self.assertEqual(context.target_role, '开发')

        context, mode, error = resolve_interview_resume(
            SimpleNamespace(user=self.other), 'uploaded', str(upload.id),
        )
        self.assertIsNone(context)
        self.assertEqual(mode, RESUME_MODE_NONE)
        self.assertEqual(error.status_code, 404)
