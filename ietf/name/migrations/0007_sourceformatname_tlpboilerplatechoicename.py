# Generated by Django 4.2.4 on 2023-08-24 14:42

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("name", "0006_feedbacktypename_data"),
    ]

    operations = [
        migrations.CreateModel(
            name="SourceFormatName",
            fields=[
                (
                    "slug",
                    models.CharField(max_length=32, primary_key=True, serialize=False),
                ),
                ("name", models.CharField(max_length=255)),
                ("desc", models.TextField(blank=True)),
                ("used", models.BooleanField(default=True)),
                ("order", models.IntegerField(default=0)),
            ],
            options={
                "ordering": ["order", "name"],
                "abstract": False,
            },
        ),
        migrations.CreateModel(
            name="TlpBoilerplateChoiceName",
            fields=[
                (
                    "slug",
                    models.CharField(max_length=32, primary_key=True, serialize=False),
                ),
                ("name", models.CharField(max_length=255)),
                ("desc", models.TextField(blank=True)),
                ("used", models.BooleanField(default=True)),
                ("order", models.IntegerField(default=0)),
            ],
            options={
                "ordering": ["order", "name"],
                "abstract": False,
            },
        ),
    ]
