# Copyright The IETF Trust 2023, All Rights Reserved
#
# Celery task definitions
#
from celery import shared_task
from django.utils import timezone

from ietf.meeting.models import Meeting
from ietf.stats.utils import fetch_attendance_from_meetings
from ietf.utils import log


@shared_task
def fetch_meeting_attendance_task():
    # fetch most recent two meetings
    meetings = Meeting.objects.filter(type="ietf", date__lte=timezone.now()).order_by("-date")[:2]
    for meeting, stats in zip(meetings, fetch_attendance_from_meetings(meetings)):
        log.log(
            "Fetched data for meeting {:>3}: {:4d} processed, {:4d} added, {:4d} in table".format(
                meeting.number, stats.processed, stats.added, stats.total
            )
        )
