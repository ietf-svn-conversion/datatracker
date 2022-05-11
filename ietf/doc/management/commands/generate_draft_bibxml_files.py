# Copyright The IETF Trust 2012-2020, All Rights Reserved


import datetime

import os
import re
import sys

from django.conf import settings
from django.core.management.base import BaseCommand
from django.template.loader import render_to_string

import debug                            # pyflakes:ignore

from ietf.doc.models import NewRevisionDocEvent

DEFAULT_DAYS = 7

class Command(BaseCommand):
    help = ('Generate draft bibxml files for xml2rfc references, placing them in the '
            'directory configured in settings.BIBXML_BASE_PATH: %s.  '
            'By default, generate files as needed for new draft revisions from the '
            'last %s days.' % (settings.BIBXML_BASE_PATH, DEFAULT_DAYS))

    def add_arguments(self, parser):
        parser.add_argument('--all', action='store_true', default=False, help="Process all documents, not only recent submissions")
        parser.add_argument('--days', type=int, default=DEFAULT_DAYS, help="Look submissions from the last DAYS days, instead of %s" % DEFAULT_DAYS)

    def say(self, msg):
        if self.verbosity > 0:
            sys.stdout.write(msg)
            sys.stdout.write('\n')

    def note(self, msg):
        if self.verbosity > 1:
            sys.stdout.write(msg)
            sys.stdout.write('\n')

    def mutter(self, msg):
        if self.verbosity > 2:
            sys.stdout.write(msg)
            sys.stdout.write('\n')

    def write(self, fn, new):
        # normalize new
        new = re.sub(r'\r\n?', r'\n', new)
        try:
            with open(fn, encoding='utf-8') as f:
                old = f.read()
        except OSError:
            old = ""
        if old.strip() != new.strip():
            self.note('Writing %s' % os.path.basename(fn))
            with open(fn, "w", encoding='utf-8') as f:
                f.write(new)

    def handle(self, *args, **options):
        self.verbosity = options.get("verbosity", 1)
        process_all = options.get("all")
        days = options.get("days")
        #
        bibxmldir = os.path.join(settings.BIBXML_BASE_PATH, 'bibxml-ids')
        if not os.path.exists(bibxmldir):
            os.makedirs(bibxmldir)
        #
        if process_all:
            doc_events = NewRevisionDocEvent.objects.filter(type='new_revision', doc__type_id='draft')
        else:
            start = datetime.datetime.now() - datetime.timedelta(days=days)
            doc_events = NewRevisionDocEvent.objects.filter(type='new_revision', doc__type_id='draft', time__gte=start)
        doc_events = doc_events.order_by('time')

        for e in doc_events:
            self.mutter(f'{e.time} {e.doc.name}')
            try:
                doc = e.doc
                if e.rev != doc.rev:
                    for h in doc.history_set.order_by("-time"):
                        if e.rev == h.rev:
                            doc = h
                            break
                doc.date = e.time.date()
                ref_text = '%s' % render_to_string('doc/bibxml.xml', {'name':doc.name, 'doc': doc, 'doc_bibtype':'I-D'})
                # if e.rev == e.doc.rev:
                #     for name in (doc.name, doc.name[6:]):
                #         ref_file_name = os.path.join(bibxmldir, 'reference.I-D.%s.xml' % (name, ))
                #         self.write(ref_file_name, ref_text)
                # for name in (doc.name, doc.name[6:]):
                #     ref_rev_file_name = os.path.join(bibxmldir, 'reference.I-D.%s-%s.xml' % (name, doc.rev))
                #     self.write(ref_rev_file_name, ref_text)
                ref_rev_file_name = os.path.join(bibxmldir, f'reference.I-D.{doc.name}-{doc.rev}.xml')
                self.write(ref_rev_file_name, ref_text)
            except Exception as ee:
                sys.stderr.write(f'\n{doc.name}-{doc.rev}: {ee}\n')
