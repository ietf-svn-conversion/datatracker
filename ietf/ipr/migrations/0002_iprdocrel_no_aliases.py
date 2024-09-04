# Generated by Django 4.2.2 on 2023-06-16 13:40

from django.db import migrations
import django.db.models.deletion
from django.db.models import F, Subquery, OuterRef, ManyToManyField, CharField
import ietf.utils.models

def forward(apps, schema_editor):
    IprDocRel = apps.get_model("ipr", "IprDocRel")
    DocAlias = apps.get_model("doc", "DocAlias")
    document_subquery = Subquery(
        DocAlias.objects.filter(
            pk=OuterRef("deprecated_document")
        ).values("docs")[:1]
    )
    name_subquery = Subquery(
        DocAlias.objects.filter(
            pk=OuterRef("deprecated_document")
        ).values("name")[:1]
    )
    IprDocRel.objects.annotate(
        firstdoc=document_subquery,
        aliasname=name_subquery,
    ).update(
        document=F("firstdoc"),
        originaldocumentaliasname=F("aliasname"),
    ) 
    # This might not be right - we may need here (and in the relateddocument migrations) to pay attention to
    # whether the name being pointed to is and rfc name or a draft name and point to the right object instead...

def reverse(apps, schema_editor):
    pass

class Migration(migrations.Migration):
    dependencies = [
        ("ipr", "0001_initial"),
        ("doc", "0016_relate_hist_no_aliases")
    ]

    operations = [
        migrations.AlterField(
            model_name='iprdocrel',
            name='document',
            field=ietf.utils.models.ForeignKey(
                db_index=False,
                on_delete=django.db.models.deletion.CASCADE,
                to='doc.docalias',
            ),
        ),
        migrations.RenameField(
            model_name="iprdocrel",
            old_name="document",
            new_name="deprecated_document"
        ),
        migrations.AlterField(
            model_name='iprdocrel',
            name='deprecated_document',
            field=ietf.utils.models.ForeignKey(
                db_index=True,
                on_delete=django.db.models.deletion.CASCADE,
                to='doc.docalias',
            ),
        ),
        migrations.AddField(
            model_name="iprdocrel",
            name="document",
            field=ietf.utils.models.ForeignKey(
                default=1, # A lie, but a convenient one - no iprdocrel objects point here.
                on_delete=django.db.models.deletion.CASCADE,
                to="doc.document",
                db_index=False,
            ),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name="iprdocrel",
            name="originaldocumentaliasname",
            field=CharField(max_length=255,null=True,blank=True),
            preserve_default=True,
        ),
        migrations.RunPython(forward, reverse),
        migrations.AlterField(
            model_name="iprdocrel",
            name="document",
            field=ietf.utils.models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                to="doc.document",
                db_index=True,
            ),
        ),
        migrations.AlterField(
            model_name='iprdisclosurebase',
            name='docs',
            field=ManyToManyField(through='ipr.IprDocRel', to='doc.Document'),
        ),
        migrations.RemoveField(
            model_name="iprdocrel",
            name="deprecated_document",
            field=ietf.utils.models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                to='doc.DocAlias',
            ),
        ),
    ]
