# Copyright The IETF Trust 2019-2020, All Rights Reserved
# Generated by Django 1.11.20 on 2019-05-25 06:44


from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('submit', '0002_submission_document2_fk'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='submission',
            name='draft',
        ),
    ]
