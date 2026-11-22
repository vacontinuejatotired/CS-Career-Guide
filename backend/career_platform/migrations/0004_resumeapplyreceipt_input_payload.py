from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('career_platform', '0003_practice_records_runtime'),
    ]

    operations = [
        migrations.AddField(
            model_name='resumeapplyreceipt',
            name='input_payload',
            field=models.JSONField(default=dict),
        ),
    ]
