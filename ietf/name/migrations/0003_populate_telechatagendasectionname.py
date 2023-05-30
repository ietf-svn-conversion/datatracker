# Generated by Django 2.2.28 on 2023-03-10 16:30

from django.db import migrations


def forward(apps, schema_editor):
    TelechatAgendaSectionName = apps.get_model('name', 'TelechatAgendaSectionName')
    for slug, name, desc, order in (
            ('roll_call', 'Roll Call', 'Roll call section', 1),
            ('minutes', 'Minutes', 'Minutes section', 2),
            ('action_items', 'Action Items', 'Action items section', 3),
    ):
        TelechatAgendaSectionName.objects.create(slug=slug, name=name, desc=desc, order=order)


def reverse(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('name', '0002_telechatagendasectionname'),
    ]

    operations = [
        migrations.RunPython(forward, reverse),
    ]
