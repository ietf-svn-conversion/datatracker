# Copyright The IETF Trust 2018-2020, All Rights Reserved
# Generated by Django 1.11.16 on 2018-10-19 11:34


from django.db import migrations

def forward(apps, schema_editor):
    DocTypeName = apps.get_model('name','DocTypeName')
    DocTypeName.objects.filter(slug='liaison').update(prefix='liaison')
    DocTypeName.objects.filter(slug='review').update(prefix='review')
    DocTypeName.objects.filter(slug='shepwrit').update(prefix='shepherd')

def reverse(apps, schema_editor):
    DocTypeName = apps.get_model('name','DocTypeName')
    DocTypeName.objects.filter(slug='liaison').update(prefix='')
    DocTypeName.objects.filter(slug='review').update(prefix='')
    DocTypeName.objects.filter(slug='shepwrit').update(prefix='')

class Migration(migrations.Migration):

    dependencies = [
        ('name', '0003_agendatypename_data'),
    ]

    operations = [
        migrations.RunPython(forward, reverse)
    ]
