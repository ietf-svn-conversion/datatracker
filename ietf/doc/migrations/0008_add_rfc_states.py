# Generated by Django 4.2.2 on 2023-06-14 20:57

from django.db import migrations


def forward(apps, schema_editor):
    StateType = apps.get_model("doc", "StateType")
    rfc_statetype, _ = StateType.objects.get_or_create(slug="rfc", label="State")

    State = apps.get_model("doc", "State")
    State.objects.get_or_create(
        type=rfc_statetype, slug="published", name="Published", used=True, order=1
    )


class Migration(migrations.Migration):
    dependencies = [
        ("doc", "0007_alter_docevent_type"),
    ]

    operations = [
        migrations.RunPython(forward),
    ]
