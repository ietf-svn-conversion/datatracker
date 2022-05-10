# Copyright The IETF Trust 2019-2020, All Rights Reserved
# Generated by Django 1.11.22 on 2019-07-22 14:56


import datetime
from django.db import migrations


def forward(apps, schema_editor):
    Meeting = apps.get_model('meeting', 'Meeting')
    today = datetime.datetime.today()
    meetings = Meeting.objects.filter(date__gt=today, type='ietf')
    for meeting in meetings:
        meeting.agenda.assignments.all().delete()
        meeting.session_set.all().delete()
        meeting.timeslot_set.all().delete()


def backward(apps, schema_editor):
    return


class Migration(migrations.Migration):

    dependencies = [
        ('meeting', '0019_slidesubmission_time'),
    ]

    operations = [
        migrations.RunPython(forward, backward),
    ]
