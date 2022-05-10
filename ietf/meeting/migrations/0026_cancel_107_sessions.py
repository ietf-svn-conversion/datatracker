# Copyright The IETF Trust 2020, All Rights Reserved
# Generated by Django 1.11.29 on 2020-03-18 16:18

from django.db import migrations


def cancel_sessions(apps, schema_editor):
    Session = apps.get_model('meeting', 'Session')
    SchedulingEvent = apps.get_model('meeting', 'SchedulingEvent')
    SessionStatusName = apps.get_model('name', 'SessionStatusName')
    Person = apps.get_model('person', 'Person')
    excludes = ['txauth','dispatch','add','raw','masque','wpack','drip','gendispatch','privacypass', 'ript', 'secdispatch', 'webtrans']
    canceled = SessionStatusName.objects.get(slug='canceled')
    person = Person.objects.get(name='Ryan Cross')
    sessions = Session.objects.filter(meeting__number=107,group__type__in=['wg','rg','ag']).exclude(group__acronym__in=excludes)
    for session in sessions:
        SchedulingEvent.objects.create(
            session = session,
            status = canceled,
            by = person)


def reverse(apps, schema_editor):
    SchedulingEvent = apps.get_model('meeting', 'SchedulingEvent')
    Person = apps.get_model('person', 'Person')
    person = Person.objects.get(name='Ryan Cross')
    SchedulingEvent.objects.filter(session__meeting__number=107, by=person).delete()


class Migration(migrations.Migration):

    dependencies = [
        ('meeting', '0025_rename_type_session_to_regular'),
    ]

    operations = [
        migrations.RunPython(cancel_sessions, reverse),
    ]
