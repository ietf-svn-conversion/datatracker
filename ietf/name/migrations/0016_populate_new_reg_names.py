# Generated by Django 4.2.17 on 2025-01-02 18:26

from django.db import migrations

def forward(apps, schema_editor):
    AttendanceTypeName = apps.get_model('name', 'AttendanceTypeName')
    RegistrationTicketTypeName = apps.get_model('name', 'RegistrationTicketTypeName')
    AttendanceTypeName.objects.create(slug='onsite', name='Onsite')
    AttendanceTypeName.objects.create(slug='remote', name='Remote')
    AttendanceTypeName.objects.create(slug='hackathon_onsite', name='Hackathon Onsite')
    AttendanceTypeName.objects.create(slug='hackathon_remote', name='Hackathon Remote')
    AttendanceTypeName.objects.create(slug='anrw_onsite', name='ANRW Onsite')
    RegistrationTicketTypeName.objects.create(slug='week_pass', name='Week Pass')
    RegistrationTicketTypeName.objects.create(slug='one_day', name='One Day')
    RegistrationTicketTypeName.objects.create(slug='student', name='Student')
    RegistrationTicketTypeName.objects.create(slug='hackathon_only', name='Hackathon Only')
    RegistrationTicketTypeName.objects.create(slug='hackathon_combo', name='Hackathon Combo')
    RegistrationTicketTypeName.objects.create(slug='anrw_only', name='ANRW Only')
    RegistrationTicketTypeName.objects.create(slug='anrw_combo', name='ANRW Combo')


def reverse(apps, schema_editor):
    AttendanceTypeName = apps.get_model('name', 'AttendanceTypeName')
    RegistrationTicketTypeName = apps.get_model('name', 'RegistrationTicketTypeName')
    AttendanceTypeName.objects.delete()
    RegistrationTicketTypeName.objects.delete()


class Migration(migrations.Migration):

    dependencies = [
        ("name", "0015_attendancetypename_registrationtickettypename"),
    ]

    operations = [
        migrations.RunPython(forward, reverse),
    ]
