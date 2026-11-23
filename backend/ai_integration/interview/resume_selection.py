"""Resolve the current user's selected interview resume without trusting client text."""

from django.http import JsonResponse

from .service import RESUME_MODE_ATTACHED, RESUME_MODE_NONE
from .legacy import ResumeContext


def resolve_interview_resume(request, resume_mode, uploaded_resume_id):
    mode = (resume_mode or 'platform').strip().lower()
    if mode != 'uploaded':
        return None, RESUME_MODE_NONE, None
    if not getattr(request.user, 'is_authenticated', False):
        return None, RESUME_MODE_NONE, JsonResponse(
            {'error': '登录后才能选择上传的简历', 'code': 'AUTH_REQUIRED'},
            status=401,
        )

    from resumes.models import ResumeUpload

    try:
        upload_id = int(uploaded_resume_id)
    except (TypeError, ValueError):
        return None, RESUME_MODE_NONE, JsonResponse(
            {'error': '请选择要使用的上传简历', 'code': 'RESUME_UPLOAD_REQUIRED'},
            status=400,
        )
    try:
        upload = ResumeUpload.objects.get(pk=upload_id, user=request.user)
    except ResumeUpload.DoesNotExist:
        return None, RESUME_MODE_NONE, JsonResponse(
            {'error': '所选上传简历不存在或不属于当前账号', 'code': 'RESUME_UPLOAD_NOT_FOUND'},
            status=404,
        )
    if upload.parsed_degraded or not upload.parsed:
        return None, RESUME_MODE_NONE, JsonResponse(
            {'error': '所选上传简历尚未正确解析，请重新上传后再试', 'code': 'RESUME_PARSE_UNAVAILABLE'},
            status=422,
        )
    context = ResumeContext.from_record(upload.parsed)
    if context.degraded or not any((context.target_role, context.years, context.skills,
                                    context.education, context.experience, context.projects)):
        return None, RESUME_MODE_NONE, JsonResponse(
            {'error': '所选上传简历没有可用于面试的内容，请重新上传清晰简历', 'code': 'RESUME_CONTENT_EMPTY'},
            status=422,
        )
    return context, RESUME_MODE_ATTACHED, None
