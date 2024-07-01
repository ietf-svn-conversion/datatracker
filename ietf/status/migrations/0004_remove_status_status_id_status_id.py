# Generated by Django 4.2.13 on 2024-07-01 01:07

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("status", "0003_remove_status_id_alter_status_status_id"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="status",
            name="status_id",
        ),
        migrations.AddField(
            model_name="status",
            name="id",
            field=models.BigAutoField(
                auto_created=True,
                primary_key=True,
                serialize=False,
                verbose_name="ID",
            ),
            preserve_default=False,
        ),
    ]
