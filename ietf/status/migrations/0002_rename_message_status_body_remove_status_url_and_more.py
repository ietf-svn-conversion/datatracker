# Generated by Django 4.2.13 on 2024-06-30 21:51

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("status", "0001_initial"),
    ]

    operations = [
        migrations.RenameField(
            model_name="status",
            old_name="message",
            new_name="body",
        ),
        migrations.RemoveField(
            model_name="status",
            name="url",
        ),
        migrations.AddField(
            model_name="status",
            name="page",
            field=models.TextField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="status",
            name="slug",
            field=models.SlugField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="status",
            name="status_id",
            field=models.IntegerField(null=True),
        ),
        migrations.AddField(
            model_name="status",
            name="title",
            field=models.CharField(default="", max_length=255),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name="status",
            name="date",
            field=models.DateTimeField(auto_now_add=True),
        ),
    ]
