# Generated by Django 2.2.14 on 2020-07-28 09:29

from django.db import migrations

def forward(apps, schema_editor):
    GroupTypeName = apps.get_model('name','GroupTypeName')
    GroupTypeName.objects.create(
        slug = 'rag',
        name = 'RAG',
        desc = 'Research Area Group',
        used = True,
        order = 0,
        verbose_name='Research Area Group'
    )

def reverse(apps, schema_editor):
    GroupTypeName = apps.get_model('name','GroupTypeName')
    GroupTypeName.objects.filter(slug='rag').delete()

class Migration(migrations.Migration):

    dependencies = [
        ('name', '0015_populate_extres'),
    ]

    operations = [
        migrations.RunPython(forward,reverse),
    ]
