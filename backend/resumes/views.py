from pathlib import Path

from django.contrib.auth import get_user_model
from django.db import transaction
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from .models import Resume, ResumeUpload
from .serializers import ResumeSerializer, ResumeUploadSerializer

from .parse import parse_resume_file


MAX_RESUME_UPLOADS = 2
RESUME_LIMIT_MESSAGE = '最多保存两份上传简历，请先删除旧简历后再上传。'
ALLOWED_RESUME_EXTS = {'.pdf', '.jpg', '.jpeg', '.png', '.webp'}


def _validate_resume_file(request):
    resume_file = request.FILES.get('file')
    if resume_file is None:
        return None, Response(
            {'code': 'RESUME_FILE_REQUIRED', 'error': '请选择要上传的简历文件'},
            status=status.HTTP_400_BAD_REQUEST,
        )
    ext = Path(resume_file.name).suffix.lower()
    if ext not in ALLOWED_RESUME_EXTS:
        return None, Response(
            {'code': 'RESUME_FILE_TYPE', 'error': '只支持 PDF, JPG, PNG, WEBP 格式的文件'},
            status=status.HTTP_400_BAD_REQUEST,
        )
    if resume_file.size > 10 * 1024 * 1024:
        return None, Response(
            {'code': 'RESUME_FILE_TOO_LARGE', 'error': '文件大小不能超过 10MB'},
            status=status.HTTP_400_BAD_REQUEST,
        )
    return resume_file, None


def _create_upload(user, resume_file, request):
    with transaction.atomic():
        get_user_model().objects.select_for_update().get(pk=user.pk)
        if ResumeUpload.objects.filter(user=user).count() >= MAX_RESUME_UPLOADS:
            return None, Response(
                {'code': 'RESUME_UPLOAD_LIMIT', 'error': RESUME_LIMIT_MESSAGE},
                status=status.HTTP_409_CONFLICT,
            )
        upload = ResumeUpload.objects.create(
            user=user,
            file=resume_file,
            file_name=Path(resume_file.name).name[:255],
        )
    try:
        upload.file.open('rb')
        record = parse_resume_file(upload.file, Path(resume_file.name).suffix.lower())
    finally:
        upload.file.close()
    upload.parsed = record
    upload.parsed_degraded = bool(record.get('degraded'))
    upload.save(update_fields=['parsed', 'parsed_degraded'])
    serializer = ResumeUploadSerializer(upload, context={'request': request})
    return serializer.data, None


class ResumeViewSet(viewsets.ModelViewSet):
    serializer_class = ResumeSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        return Resume.objects.filter(user=self.request.user)
    
    def perform_create(self, serializer):
        serializer.save(user=self.request.user)
    
    def list(self, request):
        try:
            resume = Resume.objects.get(user=request.user)
            serializer = self.get_serializer(resume, context={'request': request})
            return Response(serializer.data)
        except Resume.DoesNotExist:
            return Response({'detail': '简历不存在'}, status=status.HTTP_404_NOT_FOUND)
    
    @action(detail=False, methods=['get', 'post', 'put'])
    def my(self, request):
        if request.method == 'GET':
            try:
                resume = Resume.objects.get(user=request.user)
                serializer = self.get_serializer(resume)
                return Response(serializer.data)
            except Resume.DoesNotExist:
                return Response({'detail': '简历不存在'}, status=status.HTTP_404_NOT_FOUND)
        
        elif request.method in ['POST', 'PUT']:
            try:
                resume = Resume.objects.get(user=request.user)
                serializer = self.get_serializer(resume, data=request.data, partial=True, context={'request': request})
            except Resume.DoesNotExist:
                serializer = self.get_serializer(data=request.data, context={'request': request})
            
            if serializer.is_valid():
                serializer.save(user=request.user)
                return Response(serializer.data, status=status.HTTP_200_OK)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['post'])
    def upload_avatar(self, request):
        try:
            resume = Resume.objects.get(user=request.user)
        except Resume.DoesNotExist:
            resume = Resume.objects.create(user=request.user)
        
        if 'avatar' not in request.FILES:
            return Response({'error': '请选择要上传的图片'}, status=status.HTTP_400_BAD_REQUEST)
        
        avatar_file = request.FILES['avatar']
        
        # 验证文件类型
        allowed_types = ['image/jpeg', 'image/png', 'image/gif', 'image/webp']
        if avatar_file.content_type not in allowed_types:
            return Response({'error': '只支持 JPEG, PNG, GIF, WEBP 格式的图片'}, status=status.HTTP_400_BAD_REQUEST)
        
        # 验证文件大小 (最大 5MB)
        if avatar_file.size > 5 * 1024 * 1024:
            return Response({'error': '图片大小不能超过 5MB'}, status=status.HTTP_400_BAD_REQUEST)
        
        # 删除旧头像
        if resume.avatar:
            resume.avatar.delete(save=False)
        
        # 保存新头像
        resume.avatar = avatar_file
        resume.save()
        
        serializer = self.get_serializer(resume, context={'request': request})
        return Response({
            'message': '头像上传成功',
            'avatar_url': serializer.data.get('avatar_url')
        })
    
    @action(detail=False, methods=['delete'])
    def delete_avatar(self, request):
        try:
            resume = Resume.objects.get(user=request.user)
            if resume.avatar:
                resume.avatar.delete()
                resume.save()
                return Response({'message': '头像删除成功'})
            return Response({'error': '没有头像可删除'}, status=status.HTTP_400_BAD_REQUEST)
        except Resume.DoesNotExist:
            return Response({'error': '简历不存在'}, status=status.HTTP_404_NOT_FOUND)
    @action(detail=False, methods=['post'])
    def upload_resume(self, request):
        resume_file, error = _validate_resume_file(request)
        if error:
            return error
        upload, error = _create_upload(request.user, resume_file, request)
        if error:
            return error
        return Response(
            {'message': '简历上传并解析成功', 'upload': upload},
            status=status.HTTP_201_CREATED,
        )

    @action(detail=False, methods=['delete'])
    def delete_resume_file(self, request):
        upload_id = request.query_params.get('upload_id') or request.data.get('upload_id')
        if not upload_id:
            return Response(
                {'code': 'RESUME_UPLOAD_ID_REQUIRED', 'error': '请指定要删除的上传简历'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        try:
            upload = ResumeUpload.objects.get(pk=upload_id, user=request.user)
        except ResumeUpload.DoesNotExist:
            return Response({'error': '上传简历不存在'}, status=status.HTTP_404_NOT_FOUND)
        stored_file = upload.file
        upload.delete()
        if stored_file:
            stored_file.delete(save=False)
        return Response({'message': '上传简历已删除'})


class ResumeUploadViewSet(viewsets.GenericViewSet):
    permission_classes = [IsAuthenticated]
    serializer_class = ResumeUploadSerializer

    def get_queryset(self):
        return ResumeUpload.objects.filter(user=self.request.user)

    def list(self, request):
        serializer = self.get_serializer(self.get_queryset(), many=True)
        return Response({'count': len(serializer.data), 'results': serializer.data})

    def create(self, request):
        resume_file, error = _validate_resume_file(request)
        if error:
            return error
        upload, error = _create_upload(request.user, resume_file, request)
        if error:
            return error
        return Response(
            {'message': '简历上传并解析成功', 'upload': upload},
            status=status.HTTP_201_CREATED,
        )

    def destroy(self, request, pk=None):
        try:
            upload = self.get_queryset().get(pk=pk)
        except ResumeUpload.DoesNotExist:
            return Response({'error': '上传简历不存在'}, status=status.HTTP_404_NOT_FOUND)
        stored_file = upload.file
        upload.delete()
        if stored_file:
            stored_file.delete(save=False)
        return Response({'message': '上传简历已删除'}, status=status.HTTP_200_OK)
