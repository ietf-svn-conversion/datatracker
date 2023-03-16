# Generated by Django 2.2.28 on 2023-03-25 02:52

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('nomcom', '0013_update_accepting_volunteers_helptext'),
    ]

    operations = [
        migrations.AlterField(
            model_name='nomcom',
            name='send_questionnaire',
            field=models.BooleanField(default=False, help_text='If you check this box, questionnaires are sent automatically after nominations. DO NOT CHECK if they are not ready yet.', verbose_name='Send questionnaires automatically'),
        ),
    ]
