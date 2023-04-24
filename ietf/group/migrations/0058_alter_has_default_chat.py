# Copyright The IETF Trust 2022, All Rights Reserved
# Generated by Django 2.2.28 on 2022-07-15 12:24

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('group', '0057_nojabber_onlychat'),
    ]

    operations = [
        migrations.AlterField(
            model_name='groupfeatures',
            name='has_default_chat',
            field=models.BooleanField(default=False, verbose_name='Chat'),
        ),
    ]
