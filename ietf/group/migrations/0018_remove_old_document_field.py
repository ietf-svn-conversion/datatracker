# Copyright The IETF Trust 2019-2020, All Rights Reserved
# Generated by Django 1.11.20 on 2019-05-25 06:51


from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('group', '0017_remove_docs2_m2m'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='group',
            name='charter',
        ),
    ]
