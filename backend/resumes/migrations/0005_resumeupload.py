from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import resumes.models


def copy_legacy_resume_file(apps, schema_editor):
    Resume = apps.get_model('resumes', 'Resume')
    ResumeUpload = apps.get_model('resumes', 'ResumeUpload')
    for resume in Resume.objects.exclude(file='').exclude(file__isnull=True).iterator():
        ResumeUpload.objects.create(
            user_id=resume.user_id,
            file=resume.file.name,
            file_name=resume.file_name or resume.file.name.rsplit('/', 1)[-1],
            parsed=resume.parsed,
            parsed_degraded=resume.parsed_degraded,
        )


def restore_legacy_resume_file(apps, schema_editor):
    Resume = apps.get_model('resumes', 'Resume')
    ResumeUpload = apps.get_model('resumes', 'ResumeUpload')
    for upload in ResumeUpload.objects.order_by('created_at', 'id').iterator():
        Resume.objects.filter(user_id=upload.user_id).update(
            file=upload.file.name,
            file_name=upload.file_name,
            parsed=upload.parsed,
            parsed_degraded=upload.parsed_degraded,
        )


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('resumes', '0004_resume_file_resume_file_name'),
    ]

    operations = [
        migrations.AddField(
            model_name='resume',
            name='parsed',
            field=models.JSONField(blank=True, null=True, verbose_name='AI 解析的结构化结果'),
        ),
        migrations.AddField(
            model_name='resume',
            name='parsed_degraded',
            field=models.BooleanField(default=False, verbose_name='解析降级标记'),
        ),
        migrations.CreateModel(
            name='ResumeUpload',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('file', models.FileField(upload_to=resumes.models.resume_upload_path, verbose_name='文件')),
                ('file_name', models.CharField(max_length=255, verbose_name='文件名称')),
                ('parsed', models.JSONField(blank=True, null=True, verbose_name='AI 解析的结构化结果')),
                ('parsed_degraded', models.BooleanField(default=False, verbose_name='解析降级标记')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='上传时间')),
                ('user', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='resume_uploads',
                    to=settings.AUTH_USER_MODEL,
                    verbose_name='用户',
                )),
            ],
            options={
                'verbose_name': '上传简历',
                'verbose_name_plural': '上传简历',
                'db_table': 'resume_uploads',
                'ordering': ('-created_at', '-id'),
            },
        ),
        migrations.RunPython(copy_legacy_resume_file, restore_legacy_resume_file),
    ]
