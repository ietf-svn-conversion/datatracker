# Generated by Django 2.2.28 on 2022-04-27 12:23

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('submit', '0008_submissionextresource'),
    ]

    operations = [
        migrations.AddIndex(
            model_name='submission',
            index=models.Index(fields=['submission_date'], name='submit_subm_submiss_8e58a9_idx'),
        ),
    ]
