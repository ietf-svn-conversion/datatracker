# Copyright The IETF Trust 2016-2020, All Rights Reserved
# -*- coding: utf-8 -*-

import json
import datetime
from django.http import HttpResponse
from django.shortcuts import render
from ietf.status.models import Status

import debug                            # pyflakes:ignore

def get_context_data():
    status = Status.objects.order_by("-date").first()
    if status is None or status.active == False:
        return { "hasMessage": False }


    print("what", dir(status))
    context = {
        "hasMessage": True,
        "id": status.id,
        "slug": status.slug,
        "title": status.title,
        "body": status.body,
        "url": "/status/%s" % status.slug,
        "date": status.date.isoformat(),
        "by": status.by.name,
    }
    return context

def status_index(request):
    return render(request, "status/index.html", context=get_context_data())

def status_latest_html(request):
    return render(request, "status/latest.html", context=get_context_data())

def status_latest_json(request):
    return HttpResponse(json.dumps(get_context_data()), status=200, content_type='application/json')
