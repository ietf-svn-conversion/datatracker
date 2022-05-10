# Copyright The IETF Trust 2018-2020, All Rights Reserved


import datetime

from django.core.management.base import BaseCommand

import debug                            # pyflakes:ignore

from ietf.name.models import ImportantDateName
from ietf.meeting.helpers import update_important_dates
from ietf.meeting.models import Meeting, ImportantDate

class Command(BaseCommand):

    help = 'Updates the important dates for the given meeting'

    def add_arguments(self, parser):
        parser.add_argument('meeting', nargs='+', type=int)

    def handle(self, *args, **options):
        datenames = ImportantDateName.objects.all()
        slugs = list(datenames.values_list('slug', flat=True))
        max_offset = - min(list(datenames.values_list('default_offset_days', flat=True)))
        #
        for m in options['meeting']:
            meeting = Meeting.objects.filter(number=m).first()
            if not meeting:
                self.stderr.write(f"\nMeeting not found: {m}\n")
                continue
            if meeting.date < datetime.date.today() + datetime.timedelta(days=max_offset):
                self.stderr.write(f"\nMeeting {meeting}: Won't change dates for meetings in the past or close future\n")
                continue
            self.stdout.write(f'\n{meeting}\n\n')
            pre_dates = { d.name_id: d for d in ImportantDate.objects.filter(meeting=meeting) }
            update_important_dates(meeting)
            post_dates = { d.name_id: d for d in ImportantDate.objects.filter(meeting=meeting) }
            for slug in slugs:
                if slug in pre_dates:
                    if pre_dates[slug].date == post_dates[slug].date:
                        self.stdout.write('%-16s  %s    unchanged\n' % (slug, pre_dates[slug].date ))
                    else:
                        self.stdout.write('%-16s  %s > %s\n' % (slug, pre_dates[slug].date, post_dates[slug].date))
