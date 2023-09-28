# Copyright The IETF Trust 2023, All Rights Reserved

import debug # pyflakes:ignore

from django.db import migrations
import django.db.models.deletion
from django.db.models import F, Subquery, OuterRef
import ietf.utils.models

def forward(apps, schema_editor):
    import datetime; start = datetime.datetime.now()
    RelatedDocument = apps.get_model("doc", "RelatedDocument")
    DocAlias = apps.get_model("doc", "DocAlias")
    subquery = Subquery(DocAlias.objects.filter(pk=OuterRef("deprecated_target")).values("docs")[:1])
    RelatedDocument.objects.annotate(firstdoc=subquery).update(target=F("firstdoc"))
    end = datetime.datetime.now(); debug.show("end-start")

def reverse(apps, schema_editor):
    pass

class Migration(migrations.Migration):
    dependencies = [
        ("doc", "0013_move_rfc_docaliases"),
    ]

    operations = [
        migrations.AlterField(
            model_name='relateddocument',
            name='target',
            field=ietf.utils.models.ForeignKey(
                db_index=False,
                on_delete=django.db.models.deletion.CASCADE,
                to='doc.docalias',
            ),
        ),
        migrations.RenameField(
            model_name="relateddocument",
            old_name="target",
            new_name="deprecated_target"
        ),
        migrations.AlterField(
            model_name='relateddocument',
            name='deprecated_target',
            field=ietf.utils.models.ForeignKey(
                db_index=True,
                on_delete=django.db.models.deletion.CASCADE,
                to='doc.docalias',
            ),
        ),
        migrations.AddField(
            model_name="relateddocument",
            name="target",
            field=ietf.utils.models.ForeignKey(
                default=1, # A lie, but a convenient one - no relations point here.
                on_delete=django.db.models.deletion.CASCADE,
                related_name="targets_related",
                to="doc.document",
                db_index=False,
            ),
            preserve_default=False,
        ),
        migrations.RunPython(forward, reverse),
        migrations.AlterField(
            model_name="relateddocument",
            name="target",
            field=ietf.utils.models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name="targets_related",
                to="doc.document",
                db_index=True,
            ),
        ),
        migrations.RemoveField(
            model_name="relateddocument",
            name="deprecated_target",
            field=ietf.utils.models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                to='doc.DocAlias',
            ),
        ),
    ]
