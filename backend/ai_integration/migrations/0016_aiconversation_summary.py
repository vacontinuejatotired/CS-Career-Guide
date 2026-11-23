from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('ai_integration', '0015_alter_aiprompt_prompt_type'),
    ]

    operations = [
        migrations.AddField(
            model_name='aiconversation',
            name='summary',
            field=models.TextField(blank=True, default='', verbose_name='旧历史的压缩摘要'),
        ),
        migrations.AddField(
            model_name='aiconversation',
            name='summary_upto',
            field=models.IntegerField(default=0, verbose_name='摘要覆盖到的历史轮数'),
        ),
    ]
