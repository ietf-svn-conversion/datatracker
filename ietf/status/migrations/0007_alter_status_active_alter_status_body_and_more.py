# Generated by Django 4.2.13 on 2024-07-08 23:12

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("status", "0006_alter_status_slug"),
    ]

    operations = [
        migrations.AlterField(
            model_name="status",
            name="active",
            field=models.BooleanField(
                default=True,
                help_text="Only active messages will be shown.",
                verbose_name="Active?",
            ),
        ),
        migrations.AlterField(
            model_name="status",
            name="body",
            field=models.CharField(
                help_text="Your site status notification body.",
                max_length=255,
                verbose_name="Status body",
            ),
        ),
        migrations.AlterField(
            model_name="status",
            name="page",
            field=models.TextField(
                blank=True,
                help_text="More detail shown after people click 'Read more'. If empty no 'read more' will be shown",
                null=True,
                verbose_name="More detail (markdown)",
            ),
        ),
        migrations.AlterField(
            model_name="status",
            name="title",
            field=models.CharField(
                help_text="Your site status notification title.",
                max_length=255,
                verbose_name="Status title",
            ),
        ),
    ]
