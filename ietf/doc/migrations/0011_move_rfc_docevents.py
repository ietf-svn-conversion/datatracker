# Copyright The IETF Trust 2023, All Rights Reserved

import debug # pyflakes:ignore

from django.db import migrations
from django.db.models import Q


def forward(apps, schema_editor):
    """Move RFC events from the draft to the rfc Document"""
    import datetime; start=datetime.datetime.now()
    DocAlias = apps.get_model("doc", "DocAlias")
    DocEvent = apps.get_model("doc", "DocEvent")
    Document = apps.get_model("doc", "Document")

    # queryset with events migrated regardless of whether before or after the "published_rfc" event
    events_always_migrated = DocEvent.objects.filter(
        Q(
            type__in=[
                "published_rfc",  # do not remove this one!
            ]
        )
    )

    # queryset with events migrated only after the "published_rfc" event
    events_migrated_after_pub = DocEvent.objects.exclude(
        type__in=[
            "created_ballot",
            "closed_ballot",
            "sent_ballot_announcement",
            "changed_ballot_position",
            "changed_ballot_approval_text",
            "changed_ballot_writeup_text",
        ]
    ).exclude(
        type="added_comment",
        desc__contains="ballot set",  # excludes 311 comments that all apply to drafts
    )

    # special case for rfc 6312/6342 draft, which has two published_rfc events
    ignore = ["rfc6312", "rfc6342"]  # do not reprocess these later
    rfc6312 = Document.objects.get(name="rfc6312")
    rfc6342 = Document.objects.get(name="rfc6342")
    draft = DocAlias.objects.get(name="rfc6312").docs.first()
    assert draft == DocAlias.objects.get(name="rfc6342").docs.first()
    published_events = list(
        DocEvent.objects.filter(doc=draft, type="published_rfc").order_by("time")
    )
    assert len(published_events) == 2
    (
        pub_event_6312,
        pub_event_6342,
    ) = published_events  # order matches pub dates at rfc-editor.org

    pub_event_6312.doc = rfc6312
    pub_event_6312.save()
    events_migrated_after_pub.filter(
        doc=draft,
        time__gte=pub_event_6312.time,
        time__lt=pub_event_6342.time,
    ).update(doc=rfc6312)

    pub_event_6342.doc = rfc6342
    pub_event_6342.save()
    events_migrated_after_pub.filter(
        doc=draft,
        time__gte=pub_event_6342.time,
    ).update(doc=rfc6342)

    # Now handle all the rest
    for rfc in Document.objects.filter(type_id="rfc").exclude(name__in=ignore):
        draft = DocAlias.objects.get(name=rfc.name).docs.first()
        assert draft is not None
        published_event = DocEvent.objects.get(doc=draft, type="published_rfc")
        events_always_migrated.filter(
            doc=draft,
        ).update(doc=rfc)
        events_migrated_after_pub.filter(
            doc=draft,
            time__gte=published_event.time,
        ).update(doc=rfc)

    end = datetime.datetime.now()
    debug.show("end-start")

class Migration(migrations.Migration):
    dependencies = [
        ("doc", "0010_create_rfc_documents"),
    ]

    operations = [
        migrations.RunPython(forward),
    ]
