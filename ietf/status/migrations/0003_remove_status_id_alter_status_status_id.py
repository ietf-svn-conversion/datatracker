# Generated by Django 4.2.13 on 2024-06-30 21:52

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("status", "0002_rename_message_status_body_remove_status_url_and_more"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="status",
            name="id",
        ),
        migrations.AlterField(
            model_name="status",
            name="status_id",
            field=models.IntegerField(primary_key=True, serialize=False),
        ),
    ]
