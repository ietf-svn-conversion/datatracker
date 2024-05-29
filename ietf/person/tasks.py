# Copyright The IETF Trust 2024, All Rights Reserved
#
# Celery task definitions
#
import datetime

from celery import shared_task
from django.conf import settings
from django.utils import timezone

from ietf.utils.mail import send_mail
from .models import PersonalApiKey, PersonApiKeyEvent


@shared_task
def send_apikey_usage_emails_task(days):
    """Send usage emails to Persons who have API keys"""
    keys = PersonalApiKey.objects.filter(valid=True)
    for key in keys:
        earliest = timezone.now() - datetime.timedelta(days=days)
        events = PersonApiKeyEvent.objects.filter(key=key, time__gt=earliest)
        count = events.count()
        events = events[:32]
        if count:
            key_name = key.hash()[:8]
            subject = "API key usage for key '%s' for the last %s days" % (
                key_name,
                days,
            )
            to = key.person.email_address()
            frm = settings.DEFAULT_FROM_EMAIL
            send_mail(
                None,
                to,
                frm,
                subject,
                "utils/apikey_usage_report.txt",
                {
                    "person": key.person,
                    "days": days,
                    "key": key,
                    "key_name": key_name,
                    "count": count,
                    "events": events,
                },
            )
