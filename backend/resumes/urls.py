from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import ResumeUploadViewSet, ResumeViewSet

router = DefaultRouter()
router.register(r'uploads', ResumeUploadViewSet, basename='resume-upload')
router.register(r'', ResumeViewSet, basename='resume')

urlpatterns = [
    path('', include(router.urls)),
]
