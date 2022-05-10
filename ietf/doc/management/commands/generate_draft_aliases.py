# Copyright The IETF Trust 2012-2021, All Rights Reserved

# This was written as a script by Markus Stenberg <markus.stenberg@iki.fi>.
# It was turned into a management command by Russ Housley <housley@vigisec.com>.

import datetime
import io
import os
import re
import shutil
import stat
import time

from tempfile import mkstemp
    
from django.conf import settings
from django.core.management.base import BaseCommand

import debug                            # pyflakes:ignore

from ietf.doc.models import Document
from ietf.group.utils import get_group_role_emails, get_group_ad_emails
from ietf.utils.aliases import dump_sublist
from utils.mail import parseaddr

DEFAULT_YEARS = 2


def get_draft_ad_emails(doc):
    """Get AD email addresses for the given draft, if any."""
    ad_emails = set()
    # If working group document, return current WG ADs
    if doc.group and doc.group.acronym != 'none':
        ad_emails.update(get_group_ad_emails(doc.group))
    # Document may have an explicit AD set
    if doc.ad:
        ad_emails.add(doc.ad.email_address())
    return ad_emails


def get_draft_chair_emails(doc):
    """Get chair email addresses for the given draft, if any."""
    chair_emails = set()
    if doc.group:
        chair_emails.update(get_group_role_emails(doc.group, ['chair', 'secr']))
    return chair_emails


def get_draft_shepherd_email(doc):
    """Get shepherd email addresses for the given draft, if any."""
    shepherd_email = set()
    if doc.shepherd:
        shepherd_email.add(doc.shepherd.email_address())
    return shepherd_email


def get_draft_authors_emails(doc):
    """Get list of authors for the given draft."""
    author_emails = set()
    for author in doc.documentauthor_set.all():
        if author.email and author.email.email_address():
            author_emails.add(author.email.email_address())
    return author_emails


def get_draft_notify_emails(doc):
    """Get list of email addresses to notify for the given draft."""
    ad_email_alias_regex = r"^{}.ad@({}|{})$".format(doc.name, settings.DRAFT_ALIAS_DOMAIN, settings.TOOLS_SERVER)
    all_email_alias_regex = r"^{}.all@({}|{})$".format(doc.name, settings.DRAFT_ALIAS_DOMAIN, settings.TOOLS_SERVER)
    author_email_alias_regex = r"^{}@({}|{})$".format(doc.name, settings.DRAFT_ALIAS_DOMAIN, settings.TOOLS_SERVER)
    notify_email_alias_regex = r"^{}.notify@({}|{})$".format(doc.name, settings.DRAFT_ALIAS_DOMAIN, settings.TOOLS_SERVER)
    shepherd_email_alias_regex = r"^{}.shepherd@({}|{})$".format(doc.name, settings.DRAFT_ALIAS_DOMAIN, settings.TOOLS_SERVER)
    notify_emails = set()
    if doc.notify:
        for e in doc.notify.split(','):
            e = e.strip()
            if re.search(ad_email_alias_regex, e):
                notify_emails.update(get_draft_ad_emails(doc))
            elif re.search(author_email_alias_regex, e):
                notify_emails.update(get_draft_authors_emails(doc))
            elif re.search(shepherd_email_alias_regex, e):
                notify_emails.update(get_draft_shepherd_email(doc))
            elif re.search(all_email_alias_regex, e):
                notify_emails.update(get_draft_ad_emails(doc))
                notify_emails.update(get_draft_authors_emails(doc))
                notify_emails.update(get_draft_shepherd_email(doc))
            elif re.search(notify_email_alias_regex, e):
                pass
            else:
                (name, email) = parseaddr(e)
                notify_emails.add(email)
    return notify_emails


class Command(BaseCommand):
    help = ('Generate the draft-aliases and draft-virtual files for Internet-Draft '
            'mail aliases, placing them in the files configured in '
            'settings.DRAFT_ALIASES_PATH and settings.DRAFT_VIRTUAL_PATH, '
            'respectively.  The generation includes aliases for Internet-Drafts '
            'that have seen activity in the last %s years.' % (DEFAULT_YEARS))

    def handle(self, *args, **options):
        show_since = datetime.datetime.now() - datetime.timedelta(DEFAULT_YEARS*365)

        date = time.strftime("%Y-%m-%d_%H:%M:%S")
        signature = '# Generated by {} at {}\n'.format(__file__, date)

        ahandle, aname = mkstemp()
        os.close(ahandle)
        afile = open(aname,"w")

        vhandle, vname = mkstemp()
        os.close(vhandle)
        vfile = open(vname,"w")

        afile.write(signature)
        vfile.write(signature)
        vfile.write("%s anything\n" % settings.DRAFT_VIRTUAL_DOMAIN)

        # Internet-Drafts with active status or expired within DEFAULT_YEARS
        drafts = Document.objects.filter(name__startswith='draft-')
        active_drafts = drafts.filter(states__slug='active')
        inactive_recent_drafts = drafts.exclude(states__slug='active').filter(expires__gte=show_since)
        interesting_drafts = active_drafts | inactive_recent_drafts

        alias_domains = ['ietf.org', ]
        for draft in interesting_drafts.distinct().iterator():
            # Omit RFCs, unless they were published in the last DEFAULT_YEARS
            if draft.docalias.filter(name__startswith='rfc'):
                if draft.latest_event(type='published_rfc').time < show_since:
                    continue

            alias = draft.name
            all = set()

            # no suffix and .authors are the same list
            emails = get_draft_authors_emails(draft)
            all.update(emails)
            dump_sublist(afile, vfile, alias, alias_domains, settings.DRAFT_VIRTUAL_DOMAIN, emails)
            dump_sublist(afile, vfile, alias+'.authors', alias_domains, settings.DRAFT_VIRTUAL_DOMAIN, emails)

            # .chairs = group chairs
            emails = get_draft_chair_emails(draft)
            if emails:
                all.update(emails)
                dump_sublist(afile, vfile, alias+'.chairs', alias_domains, settings.DRAFT_VIRTUAL_DOMAIN, emails)

            # .ad = sponsoring AD / WG AD (WG document)
            emails = get_draft_ad_emails(draft)
            if emails:
                all.update(emails)
                dump_sublist(afile, vfile, alias+'.ad', alias_domains, settings.DRAFT_VIRTUAL_DOMAIN, emails)

            # .notify = notify email list from the Document
            emails = get_draft_notify_emails(draft)
            if emails:
                all.update(emails)
                dump_sublist(afile, vfile, alias+'.notify', alias_domains, settings.DRAFT_VIRTUAL_DOMAIN, emails)

            # .shepherd = shepherd email from the Document
            emails = get_draft_shepherd_email(draft)
            if emails:
                all.update(emails)
                dump_sublist(afile, vfile, alias+'.shepherd', alias_domains, settings.DRAFT_VIRTUAL_DOMAIN, emails)

            # .all = everything from above
            dump_sublist(afile, vfile, alias+'.all', alias_domains, settings.DRAFT_VIRTUAL_DOMAIN, all)

        afile.close()
        vfile.close()

        os.chmod(aname, stat.S_IWUSR|stat.S_IRUSR|stat.S_IRGRP|stat.S_IROTH) 
        os.chmod(vname, stat.S_IWUSR|stat.S_IRUSR|stat.S_IRGRP|stat.S_IROTH) 

        shutil.move(aname, settings.DRAFT_ALIASES_PATH)
        shutil.move(vname, settings.DRAFT_VIRTUAL_PATH)

