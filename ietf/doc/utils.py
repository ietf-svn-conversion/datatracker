# Copyright The IETF Trust 2011-2020, All Rights Reserved
# -*- coding: utf-8 -*-


import datetime
import hashlib
import io
import json
import math
import os
import re
import textwrap

from collections import defaultdict, namedtuple
from urllib.parse import quote
from zoneinfo import ZoneInfo

from django.conf import settings
from django.contrib import messages
from django.forms import ValidationError
from django.http import Http404
from django.template.loader import render_to_string
from django.utils import timezone
from django.utils.html import escape
from django.urls import reverse as urlreverse


import debug                            # pyflakes:ignore
from ietf.community.models import CommunityList
from ietf.community.utils import docs_tracked_by_community_list

from ietf.doc.models import Document, DocHistory, State, DocumentAuthor, DocHistoryAuthor
from ietf.doc.models import DocAlias, RelatedDocument, RelatedDocHistory, BallotType, DocReminder
from ietf.doc.models import DocEvent, ConsensusDocEvent, BallotDocEvent, IRSGBallotDocEvent, NewRevisionDocEvent, StateDocEvent
from ietf.doc.models import TelechatDocEvent, DocumentActionHolder, EditedAuthorsDocEvent
from ietf.name.models import DocReminderTypeName, DocRelationshipName
from ietf.group.models import Role, Group
from ietf.ietfauth.utils import has_role, is_authorized_in_doc_stream, is_individual_draft_author, is_bofreq_editor
from ietf.person.models import Person
from ietf.review.models import ReviewWish
from ietf.utils import draft, log
from ietf.utils.mail import send_mail
from ietf.mailtrigger.utils import gather_address_lists
from ietf.utils.timezone import date_today, datetime_from_date, datetime_today, DEADLINE_TZINFO
from ietf.utils.xmldraft import XMLDraft


def save_document_in_history(doc):
    """Save a snapshot of document and related objects in the database."""
    def get_model_fields_as_dict(obj):
        return dict((field.name, getattr(obj, field.name))
                    for field in obj._meta.fields
                    if field is not obj._meta.pk)

    # copy fields
    fields = get_model_fields_as_dict(doc)
    fields["doc"] = doc
    fields["name"] = doc.canonical_name()

    dochist = DocHistory(**fields)
    dochist.save()

    # copy many to many
    for field in doc._meta.many_to_many:
        if field.remote_field.through and field.remote_field.through._meta.auto_created:
            hist_field = getattr(dochist, field.name)
            hist_field.clear()
            hist_field.set(getattr(doc, field.name).all())

    # copy remaining tricky many to many
    def transfer_fields(obj, HistModel):
        mfields = get_model_fields_as_dict(item)
        # map doc -> dochist
        for k, v in mfields.items():
            if v == doc:
                mfields[k] = dochist
        HistModel.objects.create(**mfields)

    for item in RelatedDocument.objects.filter(source=doc):
        transfer_fields(item, RelatedDocHistory)

    for item in DocumentAuthor.objects.filter(document=doc):
        transfer_fields(item, DocHistoryAuthor)
                
    return dochist


def get_state_types(doc):
    res = []

    if not doc:
        return res

    res.append(doc.type_id)

    if doc.type_id == "draft":
        if doc.stream_id and doc.stream_id != "legacy":
            res.append("draft-stream-%s" % doc.stream_id)

        res.append("draft-iesg")
        res.append("draft-iana-review")
        res.append("draft-iana-action")
        res.append("draft-rfceditor")

    return res

def get_tags_for_stream_id(stream_id):
    if stream_id == "ietf":
        return ["w-expert", "w-extern", "w-merge", "need-aut", "w-refdoc", "w-refing", "rev-wg", "rev-wglc", "rev-ad", "rev-iesg", "sheph-u", "no-adopt", "other"]
    elif stream_id == "iab":
        return ["need-ed", "w-part", "w-review", "need-rev", "sh-f-up"]
    elif stream_id == "irtf":
        return ["need-ed", "need-sh", "w-dep", "need-rev", "iesg-com"]
    elif stream_id == "ise":
        return ["w-dep", "w-review", "need-rev", "iesg-com"]
    else:
        return []

def can_adopt_draft(user, doc):
    if not user.is_authenticated:
        return False

    if has_role(user, "Secretariat"):
        return True

    #The IRTF chair can adopt a draft into any RG
    if has_role(user, "IRTF Chair"):
        return (doc.stream_id in (None, "irtf")
                and doc.group.type_id == "individ")

    roles = Role.objects.filter(name__in=("chair", "delegate", "secr"),
                                group__type__in=("wg", "rg", "ag", "rag"),
                                group__state="active",
                                person__user=user)
    role_groups = [ r.group for r in roles ]

    return (doc.stream_id in (None, "ietf", "irtf")
            and (doc.group.type_id == "individ" or (doc.group in role_groups and len(role_groups)>1))
            and roles.exists())

def can_unadopt_draft(user, doc):
    if not user.is_authenticated:
        return False
    if has_role(user, "Secretariat"):
        return True
    if doc.stream_id == 'irtf':
        if has_role(user, "IRTF Chair"):
            return True
        return user.person.role_set.filter(name__in=('chair','delegate','secr'),group=doc.group).exists()
    elif doc.stream_id == 'ietf':
        return user.person.role_set.filter(name__in=('chair','delegate','secr'),group=doc.group).exists()
    elif doc.stream_id == 'ise':
        return user.person.role_set.filter(name='chair',group__acronym='ise').exists()
    elif doc.stream_id == 'iab':
        return False    # Right now only the secretariat can add a document to the IAB stream, so we'll
                        # leave it where only the secretariat can take it out.
    else:
        return False

def can_edit_docextresources(user, doc):
    return (has_role(user, ("Secretariat", "Area Director"))
            or is_authorized_in_doc_stream(user, doc)
            or is_individual_draft_author(user, doc)
            or is_bofreq_editor(user, doc))

def two_thirds_rule( recused=0 ):
    # For standards-track, need positions from 2/3 of the non-recused current IESG.
    active = Role.objects.filter(name="ad",group__type="area",group__state="active").count()
    return int(math.ceil((active - recused) * 2.0/3.0))

def needed_ballot_positions(doc, active_positions):
    '''Returns text answering the question "what does this document
    need to pass?".  The return value is only useful if the document
    is currently in IESG evaluation.'''
    yes = [p for p in active_positions if p and p.pos_id == "yes"]
    noobj = [p for p in active_positions if p and p.pos_id == "noobj"]
    blocking = [p for p in active_positions if p and p.pos.blocking]
    recuse = [p for p in active_positions if p and p.pos_id == "recuse"]

    answer = []
    if len(yes) < 1:
        answer.append("Needs a YES.")
    if blocking:
        if len(blocking) == 1:
            answer.append("Has a %s." % blocking[0].pos.name.upper())
        else:
            if blocking[0].pos.name.upper().endswith('S'):
                answer.append("Has %d %ses." % (len(blocking), blocking[0].pos.name.upper()))
            else:
                answer.append("Has %d %ss." % (len(blocking), blocking[0].pos.name.upper()))
    needed = 1
    if doc.type_id == "draft" and doc.intended_std_level_id in ("bcp", "ps", "ds", "std"):
        needed = two_thirds_rule(recused=len(recuse))
    elif doc.type_id == "statchg":
        if isinstance(doc,Document):
            related_set = doc.relateddocument_set
        elif isinstance(doc,DocHistory):
            related_set = doc.relateddochistory_set
        else:
            related_set = RelatedDocHistory.objects.none()
        for rel in related_set.filter(relationship__slug__in=['tops', 'tois', 'tohist', 'toinf', 'tobcp', 'toexp']):
            if (rel.target.document.std_level_id in ['bcp','ps','ds','std']) or (rel.relationship_id in ['tops','tois','tobcp']):
                needed = two_thirds_rule(recused=len(recuse))
                break
    else:
        if len(yes) < 1:
            return " ".join(answer)

    have = len(yes) + len(noobj)
    if have < needed:
        more = needed - have
        if more == 1:
            answer.append("Needs one more YES or NO OBJECTION position to pass.")
        else:
            answer.append("Needs %d more YES or NO OBJECTION positions to pass." % more)
    else:
        if blocking:
            answer.append("Has enough positions to pass once %s positions are resolved." % blocking[0].pos.name.upper())
        else:
            answer.append("Has enough positions to pass.")

    return " ".join(answer)

# Not done yet - modified version of above needed_ballot_positions
def irsg_needed_ballot_positions(doc, active_positions):
    '''Returns text answering the question "what does this document
    need to pass?".  The return value is only useful if the document
    is currently in IRSG evaluation.'''
    yes = [p for p in active_positions if p and p.pos_id == "yes"]
    needmoretime = [p for p in active_positions if p and p.pos_id == "moretime"]
    notready = [p for p in active_positions if p and p.pos_id == "notready"]

    answer = []
    needed = 2

    have = len(yes)
    if len(notready) > 0:
        answer.append("Has a Not Ready position.")
    if have < needed:
        more = needed - have
        if more == 1:
            answer.append("Needs one more YES position to pass.")
        else:
            answer.append("Needs %d more YES positions to pass." % more)
    else:
        answer.append("Has enough positions to pass.")
    if len(needmoretime) > 0:
        answer.append("Has a Need More Time position.")

    return " ".join(answer)

def create_ballot(request, doc, by, ballot_slug, time=None):
    closed = close_open_ballots(doc, by)
    for e in closed:
        messages.warning(request, "Closed earlier open ballot created %s on '%s' for %s" % (e.time.strftime('%Y-%m-%d %H:%M'), e.ballot_type, e.doc.name, ))
    if time:
        e = BallotDocEvent(type="created_ballot", by=by, doc=doc, rev=doc.rev, time=time)
    else:
        e = BallotDocEvent(type="created_ballot", by=by, doc=doc, rev=doc.rev)
    e.ballot_type = BallotType.objects.get(doc_type=doc.type, slug=ballot_slug)
    e.desc = 'Created "%s" ballot' % e.ballot_type.name
    e.save()

def create_ballot_if_not_open(request, doc, by, ballot_slug, time=None, duedate=None):
    ballot_type = BallotType.objects.get(doc_type=doc.type, slug=ballot_slug)
    if not doc.ballot_open(ballot_slug):
        if time:
            if duedate:
                e = IRSGBallotDocEvent(type="created_ballot", by=by, doc=doc, rev=doc.rev, time=time, duedate=duedate)
            else:
                e = BallotDocEvent(type="created_ballot", by=by, doc=doc, rev=doc.rev, time=time)
        else:
            if duedate:
                e = IRSGBallotDocEvent(type="created_ballot", by=by, doc=doc, rev=doc.rev, duedate=duedate)
            else:
                e = BallotDocEvent(type="created_ballot", by=by, doc=doc, rev=doc.rev)
        e.ballot_type = ballot_type
        e.desc = 'Created "%s" ballot' % e.ballot_type.name
        e.save()
        return e
    else:
        if request:
            messages.warning(request, "There already exists an open '%s' ballot for %s.  No new ballot created." % (ballot_type, doc.name))
        return None

def close_ballot(doc, by, ballot_slug):
    b = doc.ballot_open(ballot_slug)
    if b:
        e = BallotDocEvent(type="closed_ballot", doc=doc, rev=doc.rev, by=by)
        e.ballot_type = BallotType.objects.get(doc_type=doc.type,slug=ballot_slug)
        e.desc = 'Closed "%s" ballot' % e.ballot_type.name
        e.save()
    return b

def close_open_ballots(doc, by):
    closed = []
    for t in BallotType.objects.filter(doc_type=doc.type_id):
        e = close_ballot(doc, by, t.slug )
        if e:
            closed.append(e)
    return closed

def get_chartering_type(doc):
    chartering = ""
    if doc.get_state_slug() not in ("notrev", "approved"):
        if doc.group.state_id in ("proposed", "bof"):
            chartering = "initial"
        elif doc.group.state_id == "active":
            chartering = "rechartering"

    return chartering

def augment_events_with_revision(doc, events):
    """Take a set of events for doc and add a .rev attribute with the
    revision they refer to by checking NewRevisionDocEvents."""

    event_revisions = list(NewRevisionDocEvent.objects.filter(doc=doc).order_by('time', 'id').values('id', 'rev', 'time'))

    if doc.type_id == "draft" and doc.get_state_slug() == "rfc":
        # add fake "RFC" revision
        e = doc.latest_event(type="published_rfc")
        if e:
            event_revisions.append(dict(id=e.id, time=e.time, rev="RFC"))
            event_revisions.sort(key=lambda x: (x["time"], x["id"]))

    for e in sorted(events, key=lambda e: (e.time, e.id), reverse=True):
        while event_revisions and (e.time, e.id) < (event_revisions[-1]["time"], event_revisions[-1]["id"]):
            event_revisions.pop()
            
        # Check for all subtypes which have 'rev' fields:
        for sub in ['newrevisiondocevent', 'submissiondocevent', ]:
            if hasattr(e, sub):
                e = getattr(e, sub)
                break
        if not hasattr(e, 'rev'):
            if event_revisions:
                cur_rev = event_revisions[-1]["rev"]
            else:
                cur_rev = "00"
            e.rev = cur_rev

def add_links_in_new_revision_events(doc, events, diff_revisions):
    """Add direct .txt links and diff links to new_revision events."""
    prev = None

    diff_urls = dict(((name, revision), url) for name, revision, time, url in diff_revisions)

    for e in sorted(events, key=lambda e: (e.time, e.id)):
        if not e.type == "new_revision":
            continue

        for sub in ['newrevisiondocevent', 'submissiondocevent', ]:
            if hasattr(e, sub):
                e = getattr(e, sub)
                break

        if not (e.doc.name, e.rev) in diff_urls:
            continue

        full_url = diff_url = diff_urls[(e.doc.name, e.rev)]

        if doc.type_id in "draft": # work around special diff url for drafts
            full_url = "https://www.ietf.org/archive/id/" + diff_url + ".txt"

        # build links
        links = r'<a href="%s">\1</a>' % full_url
        if prev:
            links += ""

        if prev != None:
            links += ' (<a href="%s?url1=%s&amp;url2=%s">diff from previous</a>)' % (settings.RFCDIFF_BASE_URL, quote(prev, safe="~"), quote(diff_url, safe="~"))

        # replace the bold filename part
        e.desc = re.sub(r"<b>(.+-[0-9][0-9].txt)</b>", links, e.desc)

        prev = diff_url


def add_events_message_info(events):
    for e in events:
        if not e.type == "added_message":
            continue

        e.message = e.addedmessageevent.message
        e.msgtype = e.addedmessageevent.msgtype
        e.in_reply_to = e.addedmessageevent.in_reply_to


def get_unicode_document_content(key, filename, codec='utf-8', errors='ignore'):
    try:
        with io.open(filename, 'rb') as f:
            raw_content = f.read().decode(codec,errors)
    except IOError:
        if settings.DEBUG:
            error = "Error; cannot read ("+filename+")"
        else:
            error = "Error; cannot read ("+key+")"
        return error

    return raw_content


def tags_suffix(tags):
    return ("::" + "::".join(t.name for t in tags)) if tags else ""

def add_state_change_event(doc, by, prev_state, new_state, prev_tags=None, new_tags=None, timestamp=None):
    """Add doc event to explain that state change just happened."""
    if prev_state and new_state:
        assert prev_state.type_id == new_state.type_id

    # convert default args to empty lists
    prev_tags = prev_tags or []
    new_tags = new_tags or []

    if prev_state == new_state and set(prev_tags) == set(new_tags):
        return None

    e = StateDocEvent(doc=doc, rev=doc.rev, by=by)
    e.type = "changed_state"
    e.state_type = (prev_state or new_state).type
    e.state = new_state
    e.desc = "%s changed to <b>%s</b>" % (e.state_type.label, new_state.name + tags_suffix(new_tags))
    if prev_state:
        e.desc += " from %s" % (prev_state.name + tags_suffix(prev_tags))
    if timestamp:
        e.time = timestamp
    e.save()
    return e


def add_action_holder_change_event(doc, by, prev_set, reason=None):
    set_changed = False
    if doc.documentactionholder_set.exclude(person__in=prev_set).exists():
        set_changed = True  # doc has an action holder not in the old set
    # If set_changed is still False, then all of the current action holders were in
    # prev_set. Either the sets are the same or the prev_set contains at least one 
    # Person not in the current set, so just check length.
    if doc.documentactionholder_set.count() != len(prev_set):
        set_changed = True

    if not set_changed:
        return None
    
    if doc.action_holders.exists():
        ah_names = [person.plain_name() for person in doc.action_holders.all()]
        description = 'Changed action holders to %s' % ', '.join(ah_names)
    else:
        description = 'Removed all action holders'
    if reason:
        description += ' (%s)' % reason

    return DocEvent.objects.create(
        type='changed_action_holders',
        doc=doc,
        by=by,
        rev=doc.rev,
        desc=description,
    )


def update_action_holders(doc, prev_state=None, new_state=None, prev_tags=None, new_tags=None):
    """Update the action holders for doc based on state transition
    
    Returns an event describing the change which should be passed to doc.save_with_history()
    
    Only cares about draft-iesg state changes. Places where other state types are updated
    may not call this method. If you add rules for updating action holders on other state
    types, be sure this is called in the places that change that state.
    """
    # Should not call this with different state types
    if prev_state and new_state:
        assert prev_state.type_id == new_state.type_id

    # Convert tags to sets of slugs    
    prev_tag_slugs = {t.slug for t in (prev_tags or [])}
    new_tag_slugs = {t.slug for t in (new_tags or [])}

    # Do nothing if state / tag have not changed
    if (prev_state == new_state) and (prev_tag_slugs == new_tag_slugs):
        return None
    
    # Remember original list of action holders to later check if it changed
    prev_set = list(doc.action_holders.all())
    # Only draft-iesg states are of interest (for now)
    if (prev_state != new_state) and (getattr(new_state, 'type_id') == 'draft-iesg'):
        # Clear the action_holders list on a state change. This will reset the age of any that get added back.
        doc.action_holders.clear()
        if doc.ad and new_state.slug not in DocumentActionHolder.CLEAR_ACTION_HOLDERS_STATES:
            # Default to responsible AD for states other than these
            doc.action_holders.add(doc.ad)
    
    if prev_tag_slugs != new_tag_slugs:
        # If we have added or removed the need-rev tag, add or remove authors as action holders
        if ('need-rev' in prev_tag_slugs) and ('need-rev' not in new_tag_slugs):
            # Removed the 'need-rev' tag - drop authors from the action holders list
            DocumentActionHolder.objects.filter(document=doc, person__in=doc.authors()).delete()
        elif ('need-rev' not in prev_tag_slugs) and ('need-rev' in new_tag_slugs):
            # Added the 'need-rev' tag - add authors to the action holders list
            for auth in doc.authors():
                if not doc.action_holders.filter(pk=auth.pk).exists():
                    doc.action_holders.add(auth)

    # Now create an event if we changed the set
    return add_action_holder_change_event(
        doc, 
        Person.objects.get(name='(System)'), 
        prev_set,
        reason='IESG state changed',
    )


def update_documentauthors(doc, new_docauthors, by=None, basis=None):
    """Update the list of authors for a document

    Returns an iterable of events describing the change. These must be saved by the caller if
    they are to be kept.

    The new_docauthors argument should be an iterable containing objects that
    have person, email, affiliation, and country attributes. An easy way to create
    these objects is to use DocumentAuthor(), but e.g., a named tuple could be
    used. These objects will not be saved, their attributes will be used to create new
    DocumentAuthor instances. (The document and order fields will be ignored.)
    """
    def _change_field_and_describe(auth, field, newval):
        # make the change
        oldval = getattr(auth, field)
        setattr(auth, field, newval)
        
        was_empty = oldval is None or len(str(oldval)) == 0
        now_empty = newval is None or len(str(newval)) == 0
        
        # describe the change
        if oldval == newval:
            return None
        else:
            if was_empty and not now_empty:
                return 'set {field} to "{new}"'.format(field=field, new=newval)
            elif now_empty and not was_empty:
                return 'cleared {field} (was "{old}")'.format(field=field, old=oldval)
            else:
                return 'changed {field} from "{old}" to "{new}"'.format(
                    field=field, old=oldval, new=newval
                )

    persons = []
    changes = []  # list of change descriptions

    for order, docauthor in enumerate(new_docauthors):
        # If an existing DocumentAuthor matches, use that
        auth = doc.documentauthor_set.filter(person=docauthor.person).first()
        is_new_auth = auth is None
        if is_new_auth:
            # None exists, so create a new one (do not just use docauthor here because that
            # will modify the input and might cause side effects)
            auth = DocumentAuthor(document=doc, person=docauthor.person)
            changes.append('Added "{name}" as author'.format(name=auth.person.name))

        author_changes = []
        # Now fill in other author details
        author_changes.append(_change_field_and_describe(auth, 'email', docauthor.email))
        author_changes.append(_change_field_and_describe(auth, 'affiliation', docauthor.affiliation or ''))
        author_changes.append(_change_field_and_describe(auth, 'country', docauthor.country or ''))
        author_changes.append(_change_field_and_describe(auth, 'order', order + 1))
        auth.save()
        log.assertion('auth.email_id != "none"')
        persons.append(docauthor.person)
        if not is_new_auth:
            all_author_changes = ', '.join([ch for ch in author_changes if ch is not None])
            if len(all_author_changes) > 0:
                changes.append('Changed author "{name}": {changes}'.format(
                    name=auth.person.name, changes=all_author_changes
                ))

    # Finally, remove any authors no longer in the list
    removed_authors = doc.documentauthor_set.exclude(person__in=persons) 
    changes.extend(['Removed "{name}" as author'.format(name=auth.person.name)
                    for auth in removed_authors])
    removed_authors.delete()

    # Create change events - one event per author added/changed/removed.
    # Caller must save these if they want them persisted.
    return [
        EditedAuthorsDocEvent(
            type='edited_authors', by=by, doc=doc, rev=doc.rev, desc=change, basis=basis
        ) for change in changes
    ] 

def update_reminder(doc, reminder_type_slug, event, due_date):
    reminder_type = DocReminderTypeName.objects.get(slug=reminder_type_slug)

    try:
        reminder = DocReminder.objects.get(event__doc=doc, type=reminder_type, active=True)
    except DocReminder.DoesNotExist:
        reminder = None

    if due_date:
        # activate/update reminder
        if not reminder:
            reminder = DocReminder(type=reminder_type)

        reminder.event = event
        reminder.due = due_date
        reminder.active = True
        reminder.save()
    else:
        # deactivate reminder
        if reminder:
            reminder.active = False
            reminder.save()

def prettify_std_name(n, spacing=" "):
    if re.match(r"(rfc|bcp|fyi|std)[0-9]+", n):
        return n[:3].upper() + spacing + n[3:]
    else:
        return n

def default_consensus(doc):
    # if someone edits the consensus return that, otherwise
    # ietf stream => true and irtf stream => false
    consensus = None
    e = doc.latest_event(ConsensusDocEvent, type="changed_consensus")
    if (e):
        return e.consensus
    if doc.stream_id == "ietf":
        consensus = True
    elif doc.stream_id == "irtf":
        consensus = False
    else:                               # ise, iab, legacy
        return consensus

def nice_consensus(consensus):
    mapping = {
        None: "Unknown",
        True: "Yes",
        False: "No"
        }
    return mapping[consensus]

def has_same_ballot(doc, date1, date2=None):
    """ Test if the most recent ballot created before the end of date1
        is the same as the most recent ballot created before the
        end of date 2. """
    datetime1 = datetime_from_date(date1, DEADLINE_TZINFO)
    if date2 is None:
        datetime2 = datetime_today(DEADLINE_TZINFO)
    else:
        datetime2 = datetime_from_date(date2, DEADLINE_TZINFO)
    ballot1 = doc.latest_event(
        BallotDocEvent,
        type='created_ballot',
        time__lt=datetime1 + datetime.timedelta(days=1),
    )
    ballot2 = doc.latest_event(
        BallotDocEvent,
        type='created_ballot',
        time__lt=datetime2 + datetime.timedelta(days=1),
    )
    return ballot1 == ballot2

def make_notify_changed_event(request, doc, by, new_notify, time=None):

    # FOR REVIEW: This preserves the behavior from when
    # drafts and charters had separate edit_notify
    # functions. If it should be unified, there should
    # also be a migration function cause historic
    # events to match
    if doc.type.slug=='charter':
        event_type = 'changed_document'
    else:
        event_type = 'added_comment'

    e = DocEvent(type=event_type, doc=doc, rev=doc.rev, by=by)
    e.desc = "Notification list changed to %s" % (escape(new_notify) or "none")
    if doc.notify:
        e.desc += " from %s" % escape(doc.notify)
    if time:
        e.time = time
    e.save()

    return e

def update_telechat(request, doc, by, new_telechat_date, new_returning_item=None):
    on_agenda = bool(new_telechat_date)

    prev = doc.latest_event(TelechatDocEvent, type="scheduled_for_telechat")
    prev_returning = bool(prev and prev.returning_item)
    prev_telechat = prev.telechat_date if prev else None
    prev_agenda = bool(prev_telechat)

    if new_returning_item == None:
        returning = prev_returning
    else:
        returning = new_returning_item

    if returning == prev_returning and new_telechat_date == prev_telechat:
        # fully updated, nothing to do
        return

    # auto-set returning item _ONLY_ if the caller did not provide a value
    if (     new_returning_item != None
         and on_agenda
         and prev_agenda
         and new_telechat_date != prev_telechat
         and prev_telechat < date_today(DEADLINE_TZINFO)
         and has_same_ballot(doc,prev.telechat_date)
       ):
        returning = True

    e = TelechatDocEvent()
    e.type = "scheduled_for_telechat"
    e.by = by
    e.doc = doc
    e.rev = doc.rev
    e.returning_item = returning
    e.telechat_date = new_telechat_date

    if on_agenda != prev_agenda:
        if on_agenda:
            e.desc = "Placed on agenda for telechat - %s" % (new_telechat_date)
        else:
            e.desc = "Removed from agenda for telechat"
    elif on_agenda and new_telechat_date != prev_telechat:
        e.desc = "Telechat date has been changed to <b>%s</b> from <b>%s</b>" % (
            new_telechat_date, prev_telechat)
    else:
        # we didn't reschedule but flipped returning item bit - let's
        # just explain that
        if returning:
            e.desc = "Set telechat returning item indication"
        else:
            e.desc = "Removed telechat returning item indication"

    e.save()

    has_short_fuse = doc.type_id=='draft' and new_telechat_date and (( new_telechat_date - date_today() ) < datetime.timedelta(days=13))

    from ietf.doc.mails import email_update_telechat

    if has_short_fuse:
       email_update_telechat(request, doc, e.desc+"\n\nWARNING: This may not leave enough time for directorate reviews!\n")
    else:
       email_update_telechat(request, doc, e.desc)

    return e

def rebuild_reference_relations(doc, filenames):
    """Rebuild reference relations for a document

    filenames should be a dict mapping file ext (i.e., type) to the full path of each file.
    """
    if doc.type.slug != 'draft':
        return None

    # try XML first
    if 'xml' in filenames:
        refs = XMLDraft(filenames['xml']).get_refs()
    elif 'txt' in filenames:
        filename = filenames['txt']
        try:
            refs = draft.PlaintextDraft.from_file(filename).get_refs()
        except IOError as e:
            return { 'errors': ["%s :%s" %  (e.strerror, filename)] }
    else:
        return {'errors': ['No draft text available for rebuilding reference relations. Need XML or plaintext.']}

    doc.relateddocument_set.filter(relationship__slug__in=['refnorm','refinfo','refold','refunk']).delete()

    warnings = []
    errors = []
    unfound = set()
    for ( ref, refType ) in refs.items():
        # As of Dec 2021, DocAlias has a unique constraint on the name field, so count > 1 should not occur
        refdoc = DocAlias.objects.filter( name=ref )
        count = refdoc.count()
        if count == 0:
            unfound.add( "%s" % ref )
            continue
        elif count > 1:
            errors.append("Too many DocAlias objects found for %s"%ref)
        else:
            # Don't add references to ourself
            if doc != refdoc[0].document:
                RelatedDocument.objects.get_or_create( source=doc, target=refdoc[ 0 ], relationship=DocRelationshipName.objects.get( slug='ref%s' % refType ) )
    if unfound:
        warnings.append('There were %d references with no matching DocAlias'%len(unfound))

    ret = {}
    if errors:
        ret['errors']=errors
    if warnings:
        ret['warnings']=warnings
    if unfound:
        ret['unfound']=list(unfound)

    return ret

def set_replaces_for_document(request, doc, new_replaces, by, email_subject, comment=""):
    addrs = gather_address_lists('doc_replacement_changed',doc=doc)
    to = set(addrs.to)
    cc = set(addrs.cc)

    relationship = DocRelationshipName.objects.get(slug='replaces')
    old_replaces = doc.related_that_doc("replaces")

    events = []

    e = DocEvent(doc=doc, rev=doc.rev, by=by, type='changed_document')
    new_replaces_names = ", ".join(d.name for d in new_replaces) or "None"
    old_replaces_names = ", ".join(d.name for d in old_replaces) or "None"
    e.desc = "This document now replaces <b>%s</b> instead of %s" % (new_replaces_names, old_replaces_names)
    e.save()

    events.append(e)

    if comment:
        events.append(DocEvent.objects.create(doc=doc, rev=doc.rev, by=by, type="added_comment", desc=comment))

    for d in old_replaces:
        if d not in new_replaces:
            other_addrs = gather_address_lists('doc_replacement_changed',doc=d.document)
            to.update(other_addrs.to)
            cc.update(other_addrs.cc)
            RelatedDocument.objects.filter(source=doc, target=d, relationship=relationship).delete()
            if not RelatedDocument.objects.filter(target=d, relationship=relationship):
                s = 'active' if d.document.expires > timezone.now() else 'expired'
                d.document.set_state(State.objects.get(type='draft', slug=s))

    for d in new_replaces:
        if d not in old_replaces:
            other_addrs = gather_address_lists('doc_replacement_changed',doc=d.document)
            to.update(other_addrs.to)
            cc.update(other_addrs.cc)
            RelatedDocument.objects.create(source=doc, target=d, relationship=relationship)
            d.document.set_state(State.objects.get(type='draft', slug='repl'))
            
            if d.document.stream_id in ('irtf','ise','iab'):
                repl_state = State.objects.get(type_id='draft-stream-%s'%d.document.stream_id, slug='repl')
                d.document.set_state(repl_state)
                events.append(StateDocEvent.objects.create(doc=d.document, rev=d.document.rev, by=by, type='changed_state', desc="Set stream state to Replaced",state_type=repl_state.type, state=repl_state))

    # make sure there are no lingering suggestions duplicating new replacements
    RelatedDocument.objects.filter(source=doc, target__in=new_replaces, relationship="possibly-replaces").delete()

    email_desc = e.desc.replace(", ", "\n    ")

    if comment:
        email_desc += "\n" + comment

    from ietf.doc.mails import html_to_text

    send_mail(request, list(to),
              "DraftTracker Mail System <iesg-secretary@ietf.org>",
              email_subject,
              "doc/mail/change_notice.txt",
              dict(text=html_to_text(email_desc),
                   doc=doc,
                   url=settings.IDTRACKER_BASE_URL + doc.get_absolute_url()),
              cc=list(cc))

    return events

def check_common_doc_name_rules(name):
    """Check common rules for document names for use in forms, throws
    ValidationError in case there's a problem."""

    errors = []
    if re.search("[^a-z0-9-]", name):
        errors.append("The name may only contain digits, lowercase letters and dashes.")
    if re.search("--", name):
        errors.append("Please do not put more than one hyphen between any two words in the name.")
    if re.search("-[0-9]{2}$", name):
        errors.append("This name looks like ends in a version number. -00 will be added automatically. Please adjust the end of the name.")

    if errors:
        raise ValidationError(errors)

def get_initial_notify(doc,extra=None):
    # With the mailtrigger based changes, a document's notify should start empty
    receivers = []

    if extra:
        if isinstance(extra, str):
            extra = extra.split(', ')
        receivers.extend(extra)

    return ", ".join(set([x.strip() for x in receivers]))

def uppercase_std_abbreviated_name(name):
    if re.match('(rfc|bcp|std|fyi) ?[0-9]+$', name):
        return name.upper()
    else:
        return name

def extract_complete_replaces_ancestor_mapping_for_docs(names):
    """Return dict mapping all replaced by relationships of the
    replacement ancestors to docs. So if x is directly replaced by y
    and y is in names or replaced by something in names, x in
    replaces[y]."""

    replaces = defaultdict(set)

    checked = set()
    front = names
    while True:
        if not front:
            break

        relations = ( RelatedDocument.objects.filter(source__name__in=front, relationship="replaces")
                          .select_related("target").values_list("source__name", "target__docs__name") )
        if not relations:
            break

        checked.update(front)

        front = []
        for source_doc, target_doc in relations:
            replaces[source_doc].add(target_doc)

            if target_doc not in checked:
                front.append(target_doc)

    return replaces


def make_rev_history(doc):
    # return document history data for inclusion in doc.json (used by timeline)

    def get_predecessors(doc, predecessors=None):
        if predecessors is None:
            predecessors = []
        if hasattr(doc, 'relateddocument_set'):
            for alias in doc.related_that_doc('replaces'):
                for document in alias.docs.all():
                    if document not in predecessors:
                        predecessors.append(document)
                        predecessors.extend(get_predecessors(document, predecessors))
        return predecessors

    def get_ancestors(doc, ancestors = None):
        if ancestors is None:
            ancestors = []
        if hasattr(doc, 'relateddocument_set'):
            for alias in doc.related_that('replaces'):
                for document in alias.docs.all():
                    if document not in ancestors:
                        ancestors.append(document)
                        ancestors.extend(get_ancestors(document, ancestors))
        return ancestors

    def get_replaces_tree(doc):
        tree = get_predecessors(doc)
        tree.extend(get_ancestors(doc))
        return tree

    history = {}
    docs = get_replaces_tree(doc)
    if docs is not None:
        docs.append(doc)
        for d in docs:
            for e in d.docevent_set.filter(type='new_revision').distinct():
                if hasattr(e, 'newrevisiondocevent'):
                    url = urlreverse("ietf.doc.views_doc.document_main", kwargs=dict(name=d)) + e.newrevisiondocevent.rev + "/"
                    history[url] = {
                        'name': d.name,
                        'rev': e.newrevisiondocevent.rev,
                        'published': e.time.isoformat(),
                        'url': url,
                    }
                    if d.history_set.filter(rev=e.newrevisiondocevent.rev).exists():
                        history[url]['pages'] = d.history_set.filter(rev=e.newrevisiondocevent.rev).first().pages

    if doc.type_id == "draft":
        # e.time.date() agrees with RPC publication date when shown in the RPC_TZINFO time zone
        e = doc.latest_event(type='published_rfc')
    else:
        e = doc.latest_event(type='iesg_approved')
    if e:
        url = urlreverse("ietf.doc.views_doc.document_main", kwargs=dict(name=e.doc))
        history[url] = {
            'name': e.doc.canonical_name(),
            'rev': e.doc.canonical_name(),
            'published': e.time.isoformat(),
            'url': url
        }
        if hasattr(e, 'newrevisiondocevent') and doc.history_set.filter(rev=e.newrevisiondocevent.rev).exists():
            history[url]['pages'] = doc.history_set.filter(rev=e.newrevisiondocevent.rev).first().pages
    history = list(history.values())
    return sorted(history, key=lambda x: x['published'])


def get_search_cache_key(params):
    from ietf.doc.views_search import SearchForm
    fields = set(SearchForm.base_fields) - set(['sort',])
    kwargs = dict([ (k,v) for (k,v) in list(params.items()) if k in fields ])
    key = "doc:document:search:" + hashlib.sha512(json.dumps(kwargs, sort_keys=True).encode('utf-8')).hexdigest()
    return key
    
def label_wrap(label, items, joiner=',', max=50):
    lines = []
    if not items:
        return lines
    line = '%s: %s' % (label, items[0])
    for item in items[1:]:
        if len(line)+len(joiner+' ')+len(item) > max:
            lines.append(line+joiner)
            line = ' '*(len(label)+len(': ')) + item
        else:
            line += joiner+' '+item
    if line:
        lines.append(line)
    return lines

def join_justified(left, right, width=72):
    count = max(len(left), len(right))
    left = left + ['']*(count-len(left))
    right = right + ['']*(count-len(right))
    lines = []
    i = 0
    while True:
        l = left[i]
        r = right[i]
        if len(l)+1+len(r) > width:
            left = left + ['']
            right = right[:i] + [''] + right[i:]
            r = right[i]
            count += 1
        lines.append( l + ' ' + r.rjust(width-len(l)-1) )
        i += 1
        if i >= count:
            break
    return lines

def build_file_urls(doc):
    if isinstance(doc,Document) and doc.get_state_slug() == "rfc":
        name = doc.canonical_name()
        base_path = os.path.join(settings.RFC_PATH, name + ".")
        possible_types = settings.RFC_FILE_TYPES
        found_types = [t for t in possible_types if os.path.exists(base_path + t)]

        base = "https://www.rfc-editor.org/rfc/"

        file_urls = []
        for t in found_types:
            label = "plain text" if t == "txt" else t
            file_urls.append((label, base + name + "." + t))

        if "pdf" not in found_types and "txt" in found_types:
            file_urls.append(("pdf", base + "pdfrfc/" + name + ".txt.pdf"))

        if "txt" in found_types:
            file_urls.append(("htmlized", urlreverse('ietf.doc.views_doc.document_html', kwargs=dict(name=name))))
            if doc.tags.filter(slug="verified-errata").exists():
                file_urls.append(("with errata", settings.RFC_EDITOR_INLINE_ERRATA_URL.format(rfc_number=doc.rfc_number())))
        file_urls.append(("bibtex", urlreverse('ietf.doc.views_doc.document_bibtex',kwargs=dict(name=name))))
    else:
        base_path = os.path.join(settings.INTERNET_ALL_DRAFTS_ARCHIVE_DIR, doc.name + "-" + doc.rev + ".")
        possible_types = settings.IDSUBMIT_FILE_TYPES
        found_types = [t for t in possible_types if os.path.exists(base_path + t)]
        base = settings.IETF_ID_ARCHIVE_URL
        file_urls = []
        for t in found_types:
            label = "plain text" if t == "txt" else t
            file_urls.append((label, base + doc.name + "-" + doc.rev + "." + t))

        if doc.text():
            file_urls.append(("htmlized", urlreverse('ietf.doc.views_doc.document_html', kwargs=dict(name=doc.name, rev=doc.rev))))
            file_urls.append(("pdfized", urlreverse('ietf.doc.views_doc.document_pdfized', kwargs=dict(name=doc.name, rev=doc.rev))))
        file_urls.append(("bibtex", urlreverse('ietf.doc.views_doc.document_bibtex',kwargs=dict(name=doc.name,rev=doc.rev))))

    return file_urls, found_types

def build_doc_supermeta_block(doc):
    items = []
    items.append(f'[<a href="{ settings.IDTRACKER_BASE_URL }" title="Document search and retrieval page">Search</a>]')

    file_urls, found_types = build_file_urls(doc)
    file_urls = [('txt',url) if label=='plain text' else (label,url) for label,url in file_urls]

    if file_urls:
        file_labels = {
            'txt' : 'Plaintext version of this document',
            'xml' : 'XML source for this document',
            'pdf' : 'PDF version of this document',
            'html' : 'HTML version of this document, from XML2RFC',
            'bibtex' : 'BibTex entry for this document',
        }
        parts=[]
        for label,url in file_urls:
            if 'htmlized' not in label:
                file_label=file_labels.get(label,'')
                title_attribute = f' title="{file_label}"' if file_label else ''
                partstring = f'<a href="{url}"{title_attribute}>{label}</a>' 
                parts.append(partstring)
        items.append('[' + '|'.join(parts) + ']')

    items.append(f'[<a href="{ urlreverse("ietf.doc.views_doc.document_main",kwargs=dict(name=doc.canonical_name())) }" title="Datatracker information for this document">Tracker</a>]')
    if doc.group.acronym != 'none':
        items.append(f'[<a href="{urlreverse("ietf.group.views.group_home",kwargs=dict(acronym=doc.group.acronym))}" title="The working group handling this document">WG</a>]')
    items.append(f'[<a href="mailto:{doc.name}@ietf.org?subject={doc.name}" title="Send email to the document authors">Email</a>]')
    if doc.rev != "00":
        items.append(f'[<a href="{settings.RFCDIFF_BASE_URL}?difftype=--hwdiff&amp;url2={doc.name}-{doc.rev}.txt" title="Inline diff (wdiff)">Diff1</a>]')
        items.append(f'[<a href="{settings.RFCDIFF_BASE_URL}?url2={doc.name}-{doc.rev}.txt" title="Side-by-side diff">Diff2</a>]')
    items.append(f'[<a href="{settings.IDNITS_BASE_URL}?url={settings.IETF_ID_ARCHIVE_URL}{doc.name}-{doc.rev}.txt" title="Run an idnits check of this document">Nits</a>]')

    return ' '.join(items)

def build_doc_meta_block(doc, path):
    def add_markup(path, doc, lines):
        is_hst = doc.is_dochistory()
        rev = doc.rev
        if is_hst:
            doc = doc.doc
        name = doc.name
        rfcnum = doc.rfc_number()
        errata_url = settings.RFC_EDITOR_ERRATA_URL.format(rfc_number=rfcnum) if not is_hst else ""
        ipr_url = "%s?submit=draft&amp;id=%s" % (urlreverse('ietf.ipr.views.search'), name)
        for i, line in enumerate(lines):
            # add draft links
            line = re.sub(r'\b(draft-[-a-z0-9]+)\b', r'<a href="%s/\g<1>">\g<1></a>'%(path, ), line)
            # add rfcXXXX to RFC links
            line = re.sub(r' (rfc[0-9]+)\b', r' <a href="%s/\g<1>">\g<1></a>'%(path, ), line)
            # add XXXX to RFC links
            line = re.sub(r' ([0-9]{3,5})\b', r' <a href="%s/rfc\g<1>">\g<1></a>'%(path, ), line)
            # add draft revision links
            line = re.sub(r' ([0-9]{2})\b', r' <a href="%s/%s-\g<1>">\g<1></a>'%(path, name, ), line)
            if rfcnum:
                # add errata link
                line = re.sub(r'Errata exist', r'<a class="text-warning" href="%s">Errata exist</a>'%(errata_url, ), line)
            if is_hst or not rfcnum:
                # make current draft rev bold
                line = re.sub(r'>(%s)<'%rev, r'><b>\g<1></b><', line)
            line = re.sub(r'IPR declarations', r'<a class="text-warning" href="%s">IPR declarations</a>'%(ipr_url, ), line)
            line = line.replace(r'[txt]', r'[<a href="%s">txt</a>]' % doc.get_href())
            lines[i] = line
        return lines
    #
    now = timezone.now()
    draft_state = doc.get_state('draft')
    block = ''
    meta = {}
    if doc.type_id == 'draft':
        revisions = []
        ipr = doc.related_ipr()
        if ipr:
            meta['ipr'] = [ "IPR declarations" ]
        if doc.is_rfc() and not doc.is_dochistory():
            if not doc.name.startswith('rfc'):
                meta['from'] = [ "%s-%s"%(doc.name, doc.rev) ]
            meta['errata'] = [ "Errata exist" ] if doc.tags.filter(slug='errata').exists() else []
            
            meta['obsoletedby'] = [ document.rfc_number() for alias in doc.related_that('obs') for document in alias.docs.all() ]
            meta['obsoletedby'].sort()
            meta['updatedby'] = [ document.rfc_number() for alias in doc.related_that('updates') for document in alias.docs.all() ]
            meta['updatedby'].sort()
            meta['stdstatus'] = [ doc.std_level.name ]
        else:
            dd = doc.doc if doc.is_dochistory() else doc
            revisions += [ '(%s)%s'%(d.name, ' '*(2-((len(d.name)-1)%3))) for d in dd.replaces() ]
            revisions += doc.revisions()
            if doc.is_dochistory() and doc.doc.is_rfc():
                revisions += [ doc.doc.canonical_name() ]
            else:
                revisions += [ d.name for d in doc.replaced_by() ]
            meta['versions'] = revisions
            if not doc.is_dochistory and draft_state.slug == 'active' and now > doc.expires:
                # Active past expiration date
                meta['active'] = [ 'Document is active' ]
                meta['state' ] = [ doc.friendly_state() ]
            intended_std = doc.intended_std_level if doc.intended_std_level else None
            if intended_std:
                if intended_std.slug in ['ps', 'ds', 'std']:
                    meta['stdstatus'] = [ "Standards Track" ]
                else:
                    meta['stdstatus'] = [ intended_std.name ]
    elif doc.type_id == 'charter':
        meta['versions'] = doc.revisions()
    #
    # Add markup to items that needs it.
    if 'versions' in meta:
        meta['versions'] = label_wrap('Versions', meta['versions'], joiner="")
    for label in ['Obsoleted by', 'Updated by', 'From' ]:
        item = label.replace(' ','').lower()
        if item in meta and meta[item]:
            meta[item] = label_wrap(label, meta[item])
    #
    left = []
    right = []
    #right = [ '[txt]']
    for item in [ 'from', 'versions', 'obsoletedby', 'updatedby', ]:
        if item in meta and meta[item]:
            left += meta[item]
    for item in ['stdstatus', 'active', 'state', 'ipr', 'errata', ]:
        if item in meta and meta[item]:
            right += meta[item]
    lines = join_justified(left, right)
    block = '\n'.join(add_markup(path, doc, lines))
    #
    return block


def augment_docs_and_user_with_user_info(docs, user):
    """Add attribute to each document with whether the document is tracked
    or has a review wish by the user or not, and the review teams the user is on."""

    tracked = set()
    review_wished = set()
    
    if user and user.is_authenticated:
        user.review_teams = Group.objects.filter(
                reviewteamsettings__isnull=False, role__person__user=user, role__name='reviewer')

        doc_pks = [d.pk for d in docs]
        clist = CommunityList.objects.filter(user=user).first()
        if clist:
            tracked.update(
                docs_tracked_by_community_list(clist).filter(pk__in=doc_pks).values_list("pk", flat=True))

        try:
            wishes = ReviewWish.objects.filter(person=Person.objects.get(user=user))
            wishes = wishes.filter(doc__pk__in=doc_pks).values_list("doc__pk", flat=True)
            review_wished.update(wishes)
        except Person.DoesNotExist:
            pass

    for d in docs:
        d.tracked_in_personal_community_list = d.pk in tracked
        d.has_review_wish = d.pk in review_wished


def update_doc_extresources(doc, new_resources, by):
    old_res_strs = '\n'.join(sorted(r.to_form_entry_str() for r in doc.docextresource_set.all()))
    new_res_strs = '\n'.join(sorted(r.to_form_entry_str() for r in new_resources))
    
    if old_res_strs == new_res_strs:
        return False  # no change

    old_res_strs = f'\n\n{old_res_strs}\n\n' if old_res_strs else ' None '
    new_res_strs = f'\n\n{new_res_strs}' if new_res_strs else ' None'

    doc.docextresource_set.all().delete()
    for new_res in new_resources:
        new_res.doc = doc
        new_res.save()
    e = DocEvent(doc=doc, rev=doc.rev, by=by, type='changed_document')
    e.desc = f"Changed document external resources from:{old_res_strs}to:{new_res_strs}"
    e.save()
    doc.save_with_history([e])
    return True

def generate_idnits2_rfc_status():

    blob=['N']*10000

    symbols={
        'ps': 'P',
        'inf': 'I',
        'exp': 'E',
        'ds': 'D',
        'hist': 'H',
        'std': 'S',
        'bcp': 'B',
        'unkn': 'U',
    }

    rfcs = Document.objects.filter(type_id='draft',states__slug='rfc',states__type='draft')
    for rfc in rfcs:
        offset = int(rfc.rfcnum)-1
        blob[offset] = symbols[rfc.std_level_id]
        if rfc.related_that('obs'):
            blob[offset] = 'O'

    # Workarounds for unusual states in the datatracker

    # Document.get(docalias='rfc6312').rfcnum == 6342 
    # 6312 was published with the wrong rfc number in it
    # weird workaround in the datatracker - there are two 
    # DocAliases starting with rfc - the canonical name code
    # searches for the lexically highest alias starting with rfc
    # which is getting lucky.
    blob[6312 - 1] = 'O'

    # RFC200 is an old RFC List by Number
    blob[200 -1] = 'O' 

    # End Workarounds

    blob = re.sub('N*$','',''.join(blob))
    blob = textwrap.fill(blob, width=64)

    return blob

def generate_idnits2_rfcs_obsoleted():
    obsdict = defaultdict(list)
    for r in RelatedDocument.objects.filter(relationship_id='obs'):
        obsdict[int(r.target.document.rfc_number())].append(int(r.source.rfc_number()))
    for k in obsdict:
        obsdict[k] = sorted(obsdict[k])
    return render_to_string('doc/idnits2-rfcs-obsoleted.txt', context={'obsitems':sorted(obsdict.items())})


def fuzzy_find_documents(name, rev=None):
    """Find a document based on name/rev

    Applies heuristics, assuming the inputs were joined by a '-' that may have been misplaced.
    If returned documents queryset is empty, matched_rev and and matched_name are meaningless.
    The rev input is not validated - it is used to find possible names if the name input does
    not match anything, but matched_rev may not correspond to an actual version of the found
    document.
    """
    # Handle special case name formats
    if re.match(r"^\s*rfc", name, flags=re.IGNORECASE):
        name = re.sub(r"\s+", "", name.lower())
    if name.startswith('rfc0'):
        name = "rfc" + name[3:].lstrip('0')
    if name.startswith('review-') and re.search(r'-\d\d\d\d-\d\d$', name):
        name = "%s-%s" % (name, rev)
        rev = None
    if rev and not name.startswith('charter-') and re.search('[0-9]{1,2}-[0-9]{2}', rev):
        name = "%s-%s" % (name, rev[:-3])
        rev = rev[-2:]
    if re.match("^[0-9]+$", name):
        name = f'rfc{name}'

    # see if we can find a document using this name
    docs = Document.objects.filter(docalias__name=name, type_id='draft')
    if rev and not docs.exists():
        # No document found, see if the name/rev split has been misidentified.
        # Handles some special cases, like draft-ietf-tsvwg-ieee-802-11.
        name = '%s-%s' % (name, rev)
        docs = Document.objects.filter(docalias__name=name, type_id='draft')
        if docs.exists():
            rev = None  # found a doc by name with rev = None, so update that

    FoundDocuments = namedtuple('FoundDocuments', 'documents matched_name matched_rev')
    return FoundDocuments(docs, name, rev)

def bibxml_for_draft(doc, rev=None):

    if rev is not None and rev != doc.rev:
        # find the entry in the history
        for h in doc.history_set.order_by("-time"):
            if rev == h.rev:
                doc = h
                break
    if rev and rev != doc.rev:
        raise Http404("Revision not found")

    # Build the date we want to claim for the document in the bibxml
    # For documents that have relevent NewRevisionDocEvents, use the date of the event.
    # Very old documents don't have NewRevisionDocEvents - just use the document time.
        
    latest_revision_event = doc.latest_event(NewRevisionDocEvent, type="new_revision")
    latest_revision_rev = latest_revision_event.rev if latest_revision_event else None
    best_events = NewRevisionDocEvent.objects.filter(doc__name=doc.name, rev=(rev or latest_revision_rev))
    tzinfo = ZoneInfo(settings.TIME_ZONE)
    if best_events.exists():
        # There was a period where it was possible to get more than one NewRevisionDocEvent for a revision.
        # A future data cleanup would allow this to be simplified
        best_event = best_events.order_by('time').first()
        log.assertion('doc.rev == best_event.rev')
        doc.date = best_event.time.astimezone(tzinfo).date()
    else:
        doc.date = doc.time.astimezone(tzinfo).date()      # Even if this may be incorrect, what would be better?

    name = doc.name if isinstance(doc, Document) else doc.doc.name
    if name.startswith('rfc'): # bibxml3 does not speak of RFCs
        raise Http404()
        
    return render_to_string('doc/bibxml.xml', {'name':name, 'doc':doc, 'doc_bibtype':'I-D'})

