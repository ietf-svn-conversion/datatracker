# Copyright The IETF Trust 2019-2020, All Rights Reserved
# Generated by Django 1.11.20 on 2019-05-21 05:31


from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('doc', '0019_rename_field_document2'),
        ('review', '0012_remove_old_document_field'),
    ]

    operations = [
        migrations.RenameField(
            model_name='reviewrequest',
            old_name='doc2',
            new_name='doc',
        ),
        migrations.RenameField(
            model_name='reviewwish',
            old_name='doc2',
            new_name='doc',
        ),
        migrations.RenameField(
            model_name='reviewassignment',
            old_name='review2',
            new_name='review',
        ),
    ]
