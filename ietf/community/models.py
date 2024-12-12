# Copyright The IETF Trust 2012-2020, All Rights Reserved
# -*- coding: utf-8 -*-


from django.conf import settings
from django.db import models, transaction
from django.db.models import signals
from django.urls import reverse as urlreverse

from ietf.doc.models import Document, DocEvent, State
from ietf.group.models import Group
from ietf.person.models import Person, Email
from ietf.utils.models import ForeignKey

from .tasks import notify_event_to_subscribers_task


class CommunityList(models.Model):
    person = ForeignKey(Person, blank=True, null=True)
    group = ForeignKey(Group, blank=True, null=True)
    added_docs = models.ManyToManyField(Document)

    def long_name(self):
        if self.person:
            return 'Personal I-D list of %s' % self.person.plain_name()
        elif self.group:
            return 'I-D list for %s' % self.group.name
        else:
            return 'I-D list'

    def __str__(self):
        return self.long_name()

    def get_absolute_url(self):
        import ietf.community.views
        if self.person:
            return urlreverse(ietf.community.views.view_list, kwargs={ 'email_or_name': self.person.email() })
        elif self.group:
            return urlreverse("ietf.group.views.group_documents", kwargs={ 'acronym': self.group.acronym })
        return ""


class SearchRule(models.Model):
    # these types define the UI for setting up the rule, and also
    # helps when interpreting the rule and matching documents
    RULE_TYPES = [
        ('group', 'All I-Ds associated with a particular group'),
        ('area', 'All I-Ds associated with all groups in a particular Area'),
        ('group_rfc', 'All RFCs associated with a particular group'),
        ('area_rfc', 'All RFCs associated with all groups in a particular Area'),
        ('group_exp', 'All expired I-Ds of a particular group'),

        ('state_iab', 'All I-Ds that are in a particular IAB state'),
        ('state_iana', 'All I-Ds that are in a particular IANA state'),
        ('state_iesg', 'All I-Ds that are in a particular IESG state'),
        ('state_irtf', 'All I-Ds that are in a particular IRTF state'),
        ('state_ise', 'All I-Ds that are in a particular ISE state'),
        ('state_rfceditor', 'All I-Ds that are in a particular RFC Editor state'),
        ('state_ietf', 'All I-Ds that are in a particular Working Group state'),

        ('author', 'All I-Ds with a particular author'),
        ('author_rfc', 'All RFCs with a particular author'),

        ('ad', 'All I-Ds with a particular responsible AD'),

        ('shepherd', 'All I-Ds with a particular document shepherd'),

        ('name_contains', 'All I-Ds with particular text/regular expression in the name'),
    ]

    community_list = ForeignKey(CommunityList)
    rule_type = models.CharField(max_length=30, choices=RULE_TYPES)

    # these are filled in depending on the type
    state = ForeignKey(State, blank=True, null=True)
    group = ForeignKey(Group, blank=True, null=True)
    person = ForeignKey(Person, blank=True, null=True)
    text = models.CharField(verbose_name="Text/RegExp", max_length=255, blank=True, default="")

    # store a materialized view/index over which documents are matched
    # by the name_contains rule to avoid having to scan the whole
    # database - we update this manually when the rule is changed and
    # when new documents are submitted
    name_contains_index = models.ManyToManyField(Document)

    def __str__(self):
        return "%s %s %s/%s/%s/%s" % (self.community_list, self.rule_type, self.state, self.group, self.person, self.text)

class EmailSubscription(models.Model):
    community_list = ForeignKey(CommunityList)
    email = ForeignKey(Email)

    NOTIFICATION_CHOICES = [
        ("all", "All changes"),
        ("significant", "Only significant state changes")
    ]
    notify_on = models.CharField(max_length=30, choices=NOTIFICATION_CHOICES, default="all")

    def __str__(self):
        return "%s to %s (%s changes)" % (self.email, self.community_list, self.notify_on)


def notify_of_event(event: DocEvent):
    """Send subscriber notification emails for a 'draft'-related DocEvent
    
    If the event is attached to a draft of type 'doc', queues a task to send notification emails to
    community list subscribers. No emails will be sent when SERVER_MODE is 'test'.
    """
    if event.doc.type_id != 'draft':
        return

    if getattr(event, "skip_community_list_notification", False):
        return
    
    # kludge alert: queuing a celery task in response to a signal can cause unexpected attempts to
    # start a Celery task during tests. To prevent this, don't queue a celery task if we're running
    # tests.
    if settings.SERVER_MODE != "test":
        # Wrap in on_commit in case a transaction is open
        transaction.on_commit(
            lambda: notify_event_to_subscribers_task.delay(event_id=event.pk)
        )


def notify_of_events_receiver(sender, instance, **kwargs):
    """Call notify_of_event after saving a new DocEvent"""
    if not isinstance(instance, DocEvent):
        return

    if not kwargs.get("created", False):
        return  # only notify on creation

    notify_of_event(instance)


signals.post_save.connect(notify_of_events_receiver)
