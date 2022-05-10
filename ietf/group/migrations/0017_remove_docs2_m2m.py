# Copyright The IETF Trust 2019-2020, All Rights Reserved
# Generated by Django 1.11.20 on 2019-05-30 03:23


from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('group', '0016_copy_docs_m2m_table'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='groupmilestonedocs',
            name='document',
        ),
        migrations.RemoveField(
            model_name='groupmilestonedocs',
            name='groupmilestone',
        ),
        migrations.RemoveField(
            model_name='groupmilestonehistorydocs',
            name='document',
        ),
        migrations.RemoveField(
            model_name='groupmilestonehistorydocs',
            name='groupmilestonehistory',
        ),
        migrations.RemoveField(
            model_name='groupmilestone',
            name='docs2',
        ),
        migrations.RemoveField(
            model_name='groupmilestonehistory',
            name='docs2',
        ),
        migrations.DeleteModel(
            name='GroupMilestoneDocs',
        ),
        migrations.DeleteModel(
            name='GroupMilestoneHistoryDocs',
        ),
    ]
