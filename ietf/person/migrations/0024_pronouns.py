# Copyright The IETF Trust 2022, All Rights Reserved
# Generated by Django 2.2.28 on 2022-06-17 15:09

from django.db import migrations, models
import jsonfield.fields


class Migration(migrations.Migration):

    dependencies = [
        ('person', '0023_auto_20220615_1006'),
    ]

    operations = [
        migrations.AddField(
            model_name='historicalperson',
            name='pronouns_freetext',
            field=models.CharField(blank=True, help_text='Optionally provide your personal pronouns. These will be displayed on your public profile page and alongside your name in Meetecho and, in future, other systems. Select any number of the checkboxes OR provide a custom string up to 30 characters.', max_length=30, null=True, verbose_name=' '),
        ),
        migrations.AddField(
            model_name='historicalperson',
            name='pronouns_selectable',
            field=jsonfield.fields.JSONCharField(blank=True, default=list, max_length=120, null=True, verbose_name='Pronouns'),
        ),
        migrations.AddField(
            model_name='person',
            name='pronouns_freetext',
            field=models.CharField(blank=True, help_text='Optionally provide your personal pronouns. These will be displayed on your public profile page and alongside your name in Meetecho and, in future, other systems. Select any number of the checkboxes OR provide a custom string up to 30 characters.', max_length=30, null=True, verbose_name=' '),
        ),
        migrations.AddField(
            model_name='person',
            name='pronouns_selectable',
            field=jsonfield.fields.JSONCharField(blank=True, default=list, max_length=120, null=True, verbose_name='Pronouns'),
        ),
        migrations.AlterField(
            model_name='historicalperson',
            name='consent',
            field=models.BooleanField(default=None, null=True, verbose_name='I hereby give my consent to the use of the personal details I have provided (photo, bio, name, pronouns, email) within the IETF Datatracker'),
        ),
        migrations.AlterField(
            model_name='person',
            name='consent',
            field=models.BooleanField(default=None, null=True, verbose_name='I hereby give my consent to the use of the personal details I have provided (photo, bio, name, pronouns, email) within the IETF Datatracker'),
        ),
    ]
