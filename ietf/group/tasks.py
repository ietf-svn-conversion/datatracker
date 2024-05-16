# Copyright The IETF Trust 2024, All Rights Reserved
#
# Celery task definitions
#
from celery import shared_task
from pathlib import Path

from django.conf import settings
from django.template.loader import render_to_string

from .models import Group
from .utils import fill_in_charter_info, fill_in_wg_drafts, fill_in_wg_roles


@shared_task
def generate_1wg_charter_files_task():
    areas = Group.objects.filter(type="area", state="active").order_by("name")
    for area in areas:
        area.groups = Group.objects.filter(parent=area, type="wg", state="active").order_by("name")
        for group in area.groups:
            fill_in_charter_info(group)
            fill_in_wg_roles(group)
            fill_in_wg_drafts(group)
    charter_path = Path(settings.CHARTER_PATH)
    (charter_path / "1wg-charters.txt").write_text(
        render_to_string("group/1wg-charters.txt", {"areas": areas}),
        encoding="utf8",
    )
    (charter_path / "1wg-charters-by-acronym.txt").write_text(
        render_to_string("group/1wg-charters-by-acronym.txt", {"areas": areas}),
        encoding="utf8",
    )
