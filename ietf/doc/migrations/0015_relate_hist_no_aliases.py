# Copyright The IETF Trust 2023, All Rights Reserved

import debug # pyflakes: ignore

from django.db import migrations
import django.db.models.deletion
from django.db.models import F, Subquery, OuterRef
import ietf.utils.models

def forward(apps, schema_editor):
    import datetime; start=datetime.datetime.now()
    RelatedDocHistory = apps.get_model("doc", "RelatedDocHistory")
    DocAlias = apps.get_model("doc", "DocAlias")
    subquery = Subquery(DocAlias.objects.filter(pk=OuterRef("deprecated_target")).values("docs")[:1])
    RelatedDocHistory.objects.annotate(firstdoc=subquery).update(target=F("firstdoc"))
    end=datetime.datetime.now(); debug.show("end-start")

def reverse(apps, schema_editor):
    pass

class Migration(migrations.Migration):
    dependencies = [
        ("doc", "0014_relate_no_aliases"),
    ]

    operations = [
        migrations.AlterField(
            model_name='relateddochistory',
            name='target',
            field=ietf.utils.models.ForeignKey(
                db_index=False,
                on_delete=django.db.models.deletion.CASCADE,
                to='doc.docalias',
                related_name='reversely_related_document_history_set',
            ),
        ),
        migrations.RenameField(
            model_name="relateddochistory",
            old_name="target",
            new_name="deprecated_target"
        ),
        migrations.AlterField(
            model_name='relateddochistory',
            name='deprecated_target',
            field=ietf.utils.models.ForeignKey(
                db_index=True,
                on_delete=django.db.models.deletion.CASCADE,
                to='doc.docalias',
                related_name='deprecated_reversely_related_document_history_set',
            ),
        ),
        migrations.AddField(
            model_name="relateddochistory",
            name="target",
            field=ietf.utils.models.ForeignKey(
                default=1, # A lie, but a convenient one - no relations point here.
                on_delete=django.db.models.deletion.CASCADE,
                to="doc.document",
                db_index=False,
                related_name='reversely_related_document_history_set',
            ),
            preserve_default=False,
        ),
        migrations.RunPython(forward, reverse),
        migrations.AlterField(
            model_name="relateddochistory",
            name="target",
            field=ietf.utils.models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                to="doc.document",
                db_index=True,
                related_name='reversely_related_document_history_set',
            ),
        ),
        migrations.RemoveField(
            model_name="relateddochistory",
            name="deprecated_target",
            field=ietf.utils.models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                to='doc.DocAlias',
                related_name='deprecated_reversely_related_document_history_set',
            ),
        ),
    ]
