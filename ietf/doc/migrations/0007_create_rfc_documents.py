# Generated by Django 4.2.2 on 2023-06-15 15:27

from django.db import migrations


def forward(apps, schema_editor):
    Document = apps.get_model("doc", "Document")
    DocAlias = apps.get_model("doc", "DocAlias")
    DocumentAuthor = apps.get_model("doc", "DocumentAuthor")
    
    State = apps.get_model("doc", "State")
    draft_rfc_state = State.objects.get(type_id="draft", slug="rfc")
    rfc_published_state = State.objects.get(type_id="rfc", slug="published")
    
    DocTypeName = apps.get_model("name", "DocTypeName")
    rfc_doctype = DocTypeName(slug="rfc")
    
    # Find draft Documents in the "rfc" state
    found_by_state = Document.objects.filter(states=draft_rfc_state).distinct()
    
    # Find Documents with an "rfc..." alias and confirm they're the same set
    rfc_docaliases = DocAlias.objects.filter(name__startswith="rfc")
    found_by_name = Document.objects.filter(docalias__in=rfc_docaliases).distinct()
    assert set(found_by_name) == set(found_by_state), "mismatch between rfcs identified by state and docalias"
    
    # As of 2023-06-15, there is one Document with two rfc aliases: rfc6312 and rfc6342 are the same Document. This 
    # was due to a publication error. Because we go alias-by-alias, no special handling is needed in this migration.
    
    for rfc_alias in rfc_docaliases.order_by("name"):
        assert rfc_alias.docs.count() == 1, f"DocAlias {rfc_alias} is linked to more than 1 Document"
        draft = rfc_alias.docs.first()
        if draft.name.startswith("rfc"):
            rfc = draft
            rfc.type = rfc_doctype
            rfc.rfc_number = int(draft.name[3:])
            rfc.save()
            rfc.states.set([rfc_published_state])
        else:
            rfc = Document.objects.create(
                type=rfc_doctype,
                name=rfc_alias.name,
                rfc_number=int(rfc_alias.name[3:]),
                title=draft.title,
                abstract=draft.abstract,
                pages=draft.pages,
                words=draft.words,
                std_level=draft.std_level,
                external_url=draft.external_url,
                uploaded_filename=draft.uploaded_filename,
                note=draft.note,
            )
            rfc.states.set([rfc_published_state])
            rfc.formal_languages.set(draft.formal_languages.all())
            
            # Copy Authors
            for da in draft.documentauthor_set.all():
                DocumentAuthor.objects.create(
                    document=rfc,
                    person=da.person,
                    email=da.email,
                    affiliation=da.affiliation,
                    country=da.country,
                    order=da.order,
                )


class Migration(migrations.Migration):
    dependencies = [
        ("doc", "0006_dochistory_rfc_number_document_rfc_number"),
        ("name", "0004_rfc_doctype_names"),
    ]

    operations = [
        migrations.RunPython(forward),
    ]
