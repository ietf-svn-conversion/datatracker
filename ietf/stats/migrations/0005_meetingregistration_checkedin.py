# Generated by Django 2.2.28 on 2022-07-26 08:37

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('stats', '0004_split_records'),
    ]

    operations = [
        migrations.AddField(
            model_name='meetingregistration',
            name='checkedin',
            field=models.BooleanField(default=False),
        ),
    ]
