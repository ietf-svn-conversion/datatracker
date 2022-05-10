# Copyright The IETF Trust 2018-2020, All Rights Reserved
# Generated by Django 1.11.13 on 2018-07-10 13:47


from django.db import migrations

agenda_type_names = (
    {
        'slug': 'ietf',
        'name': 'IETF Agenda',
        'desc': '',
        'used': True,
        'order': 0,
    },
    {
        'slug': 'ad',
        'name': 'AD Office Hours',
        'desc': '',
        'used': True,
        'order': 0,
    },
    {
        'slug': 'side',
        'name': 'Side Meetings',
        'desc': '',
        'used': True,
        'order': 0,
    },
    {
        'slug': 'workshop',
        'name': 'Workshops',
        'desc': '',
        'used': True,
        'order': 0,
    },
)

def forward(apps, schema_editor):
    AgendaTypeName = apps.get_model('name', 'AgendaTypeName')
    for entry in agenda_type_names:
        AgendaTypeName.objects.create(**entry)

def reverse(apps, schema_editor):
    pass

class Migration(migrations.Migration):

    dependencies = [
        ('name', '0002_agendatypename'),
        ('group', '0002_groupfeatures_historicalgroupfeatures'),
    ]

    operations = [
        migrations.RunPython(forward, reverse),
    ]
