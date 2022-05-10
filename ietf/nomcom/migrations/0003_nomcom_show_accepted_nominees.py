# Copyright The IETF Trust 2018-2020, All Rights Reserved
# Generated by Django 1.11.15 on 2018-09-26 11:10


from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('nomcom', '0002_auto_20180918_0550'),
    ]

    operations = [
        migrations.AddField(
            model_name='nomcom',
            name='show_accepted_nominees',
            field=models.BooleanField(default=True, help_text='Show accepted nominees on the public nomination page', verbose_name='Show accepted nominees'),
        ),
    ]
