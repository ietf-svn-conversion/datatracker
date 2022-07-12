# Generated by Django 2.2.28 on 2022-07-12 11:24

from django.db import migrations, models
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ('group', '0056_dir_chair_groupman_role'),
    ]

    operations = [
        migrations.AlterField(
            model_name='group',
            name='time',
            field=models.DateTimeField(default=django.utils.timezone.now),
        ),
        migrations.AlterField(
            model_name='groupevent',
            name='time',
            field=models.DateTimeField(default=django.utils.timezone.now, help_text='When the event happened'),
        ),
        migrations.AlterField(
            model_name='grouphistory',
            name='time',
            field=models.DateTimeField(default=django.utils.timezone.now),
        ),
    ]
