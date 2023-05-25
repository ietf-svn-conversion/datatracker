# Copyright The IETF Trust 2023, All Rights Reserved

import datetime
import zoneinfo

from django.db import migrations


def nametimes_by_year():
    with open("data_for_0005","r") as datafile:
        return(eval(datafile.read())) # Consider making the dump json instead.

def forward(apps, schema_editor):
    Document = apps.get_model("doc", "Document")
    DocAlias = apps.get_model("doc", "DocAlias")
    Meeting = apps.get_model("meeting", "Meeting")
    Schedule = apps.get_model("meeting", "Schedule")
    Session = apps.get_model("meeting", "Session")
    SchedulingEvent = apps.get_model("meeting", "SchedulingEvent")
    SchedTimeSessAssignment = apps.get_model("meeting", "SchedTimeSessAssignment")
    TimeSlot = apps.get_model("meeting", "TimeSlot")

    ntby = nametimes_by_year()
    for year in ntby.keys():
        counter = 1
        for nametime in ntby[year]:
            name = nametime[0]
            _, ext = name.split(".")
            start, end = nametime[1]
            meeting_name = f"interim-{year}-iab-{counter:02d}"
            minutes_docname = f"minutes-interim-{year}-iab-{counter:02d}-{start:%Y%m%d}" # Note violating the convention of having the start time...
            minutes_filename = f"{minutes_docname}-00.{ext}"  # I plan to use a management command to put the files in place after the migration is run.
            # Create Document
            doc = Document.objects.create(
                name = minutes_docname,
                type_id = "minutes",
                title = f"Minutes {meeting_name} {start:%Y-%m-%d}", # Another violation of convention,
                group_id = 7, # The IAB group
                rev = "00",
                uploaded_filename = minutes_filename,
            )
            DocAlias.objects.create(name=doc.name).docs.add(doc)
            # Create Meeting - Add a note about noon utc fake meeting times
            meeting = Meeting.objects.create(
                number=meeting_name,
                type_id='interim',
                date=start.date(),
                days=1,
                time_zone=start.tzname())
            schedule = Schedule.objects.create(
                meeting=meeting,
                owner_id=1, # The "(System)" person
                visible=True,
                public=True)
            meeting.schedule = schedule
            if start.timetz() == datetime.time(12, 0, 0, tzinfo=zoneinfo.ZoneInfo(key="UTC")):
                meeting.agenda_note = "The actual time of this meeting was not recorded and was likely not at noon UTC"
            meeting.save()
            # Create Session
            session = Session.objects.create(
                meeting = meeting,
                group_id = 7, # The IAB group
                type_id = "regular",
                purpose_id = "regular",
            )
            # Schedule the Session
            SchedulingEvent.objects.create(
                session=session,
                status_id="sched",
                by_id=1, # (System)
            )
            timeslot = TimeSlot.objects.create(
                meeting=meeting,
                type_id = "regular",
                time = start,
                duration = end - start,
            )
            SchedTimeSessAssignment.objects.create(
                timeslot=timeslot,
                session=session,
                schedule=schedule
            )
            # Add Document to Session
            session.sessionpresentation_set.create(document=doc,rev=doc.rev)

            counter += 1
    raise Exception


def reverse(apps, schema_editor):
    pass


class Migration(migrations.Migration):
    dependencies = [
        ("doc", "0003_remove_document_info_order"),
        ("meeting", "0004_session_chat_room"),
    ]

    operations = [migrations.RunPython(forward, reverse)]

"""
The following can be used to regenerate data_for_0005

import datetime
from collections import defaultdict 
from zoneinfo import ZoneInfo



def make_time_tuple(date, start_hour, start_minute, end_hour, end_minute, tz):
    return (
        (
            datetime.datetime(date.year, date.month, date.day, start_hour, start_minute, tzinfo=ZoneInfo(tz)),
            datetime.datetime(date.year, date.month, date.day, end_hour, end_minute, tzinfo=ZoneInfo(tz))   
        )
    )

def get_time(name):
    """
        From Cindy:
        2011-04-06 (and likely earlier) - 2013-02-27: 0930-1100 PST8PDT
        2013-03-27 - 2015-04-08: 0700-0830 PST8PDT
        2015-04-15 - 2016-03-23: 0800-0930 PST8PDT
        2016-04-20 - 2016-11-02: 0700-0830 PST8PDT
        2016-11-20 - 2019-03-13: 2000-2130 UTC
        2019-04-10 - 2019-10-02: 1330-1430 UTC
        2019-10-16 - 2020-03-18: 2130-2230 UTC
        2020-04-01 - 2020-10-14: 1330-1430 UTC
        2020-10-21 - 2021-03-03: 2130-2230 UTC
        2021-03-24 - Present: 0700-0800 PST8PDT
    """
    date_string = name.split(".")[0]
    date = datetime.date(*map(int,date_string.split("-")))
    times = None
    if datetime.date(2011,4,6) <= date <= datetime.date(2013,2,27):
        times = make_time_tuple(date, 9, 30, 11, 0, "PST8PDT")
    elif datetime.date(2013,3,27) <= date <= datetime.date(2015,4,8):
        times = make_time_tuple(date, 7, 0, 8, 30, "PST8PDT")
    elif datetime.date(2015,4,15) <= date <= datetime.date(2016,3,23):
        times = make_time_tuple(date, 8, 0, 9, 30, "PST8PDT")
    elif datetime.date(2016,11,20) <= date <= datetime.date(2019,3,13):
        times = make_time_tuple(date, 20, 0, 21, 30, "UTC")
    elif datetime.date(2019, 4, 10) <= date <= datetime.date(2019,10,2):
        times = make_time_tuple(date, 13, 30, 14, 30, "UTC")
    elif datetime.date(2019, 10, 16) <= date <= datetime.date(2020, 3, 18):
        times = make_time_tuple(date, 21, 30, 22, 30, "UTC")
    elif datetime.date(2020, 4, 1) <= date <= datetime.date(2020, 10, 14):
        times = make_time_tuple(date, 13, 30, 14, 30, "UTC")
    elif datetime.date(2020, 10, 21) <= date <= datetime.date(2021, 3, 3):
        times = make_time_tuple(date, 21, 30, 22, 30, "UTC")
    elif datetime.date(2021, 3, 24) <= date :
        times = make_time_tuple(date, 7, 0, 8, 0, "PST8PDT")
    else:
        times = make_time_tuple(date, 12, 0, 12, 5, "UTC")
    return times





def build_nametimes_by_year():
    from collections import defaultdict 
    scraped_basenames = [
        "2022-12-14.md",
        "2022-12-07.md",
        "2022-11-23.md",
        "2022-11-10.md",
        "2022-11-08.md",
        "2022-11-06.md",
        "2022-10-26.md",
        "2022-10-12.md",
        "2022-10-05.md",
        "2022-09-28.md",
        "2022-09-21.md",
        "2022-09-07.md",
        "2022-08-24.md",
        "2022-08-10.md",
        "2022-07-26.md",
        "2022-07-24.md",
        "2022-07-06.md",
        "2022-06-29.md",
        "2022-06-22.md",
        "2022-06-15.md",
        "2022-06-01.md",
        "2022-05-11.md",
        "2022-05-04.md",
        "2022-04-27.md",
        "2022-04-20.md",
        "2022-04-13.md",
        "2022-04-06.md",
        "2022-03-20.md",
        "2022-03-09.md",
        "2022-03-02.md",
        "2022-02-23.md",
        "2022-02-16.md",
        "2022-02-02.md",
        "2022-01-19.md",
        "2022-01-12.md",
        "2021-12-15.md",
        "2021-12-08.md",
        "2021-12-01.md",
        "2021-11-17.md",
        "2021-10-27.md",
        "2021-10-20.md",
        "2021-10-06.md",
        "2021-09-22.md",
        "2021-09-08.md",
        "2021-09-01.md",
        "2021-08-25.md",
        "2021-08-11.md",
        "2021-07-21.md",
        "2021-07-14.md",
        "2021-06-30.md",
        "2021-06-23.md",
        "2021-06-16.md",
        "2021-06-02.md",
        "2021-05-26.md",
        "2021-05-19.md",
        "2021-05-12.md",
        "2021-05-05.md",
        "2021-04-21.md",
        "2021-04-14.md",
        "2021-04-07.md",
        "2021-03-31.md",
        "2021-03-24.md",
        "2021-03-03.md",
        "2021-02-24.md",
        "2021-02-17.md",
        "2021-02-10.md",
        "2021-02-03.md",
        "2021-01-27.md",
        "2021-01-20.md",
        "2021-01-13.md",
        "2021-01-06.md",
        "2020-12-16.md",
        "2020-12-02.md",
        "2020-11-04.md",
        "2020-10-21.md",
        "2020-10-14.md",
        "2020-10-07.md",
        "2020-09-23.md",
        "2020-09-09.md",
        "2020-08-26.md",
        "2020-08-12.md",
        "2020-07-15.md",
        "2020-07-01.md",
        "2020-06-17.md",
        "2020-06-10.md",
        "2020-05-27.md",
        "2020-05-20.md",
        "2020-05-13.md",
        "2020-04-29.md",
        "2020-04-15.md",
        "2020-04-08.md",
        "2020-04-01.md",
        "2020-03-18.md",
        "2020-03-11.md",
        "2020-03-04.md",
        "2020-02-19.md",
        "2020-02-12.md",
        "2020-02-05.md",
        "2020-01-22.md",
        "2020-01-15.md",
        "2020-01-08.md",
        "2019-12-18.md",
        "2019-12-11.md",
        "2019-12-04.md",
        "2019-11-21.md",
        "2019-11-18.md",
        "2019-11-17.md",
        "2019-10-30.md",
        "2019-10-16.md",
        "2019-10-02.md",
        "2019-09-18.md",
        "2019-09-04.md",
        "2019-08-28.md",
        "2019-08-21.md",
        "2019-08-07.md",
        "2019-07-25.md",
        "2019-07-21.md",
        "2019-07-10.md",
        "2019-06-26.md",
        "2019-06-12.md",
        "2019-05-29.md",
        "2019-05-08.md",
        "2019-05-01.md",
        "2019-04-17.md",
        "2019-04-10.md",
        "2019-03-28.md",
        "2019-03-25.md",
        "2019-03-24.md",
        "2019-03-13.md",
        "2019-03-06.md",
        "2019-02-27.md",
        "2019-02-13.md",
        "2019-02-06.md",
        "2019-01-23.md",
        "2019-01-16.md",
        "2019-01-09.md",
        "2018-12-19.md",
        "2018-12-05.md",
        "2018-11-28.md",
        "2018-11-21.md",
        "2018-11-08.md",
        "2018-11-05.md",
        "2018-11-04.md",
        "2018-10-24.md",
        "2018-10-10.md",
        "2018-10-03.md",
        "2018-09-26.md",
        "2018-09-12.md",
        "2018-09-05.md",
        "2018-08-22.md",
        "2018-08-08.md",
        "2018-08-01.md",
        "2018-07-19.md",
        "2018-07-16.md",
        "2018-07-15.md",
        "2018-07-03.md",
        "2018-06-27.md",
        "2018-06-13.md",
        "2018-06-06.md",
        "2018-05-30.md",
        "2018-05-16.md",
        "2018-05-09.md",
        "2018-04-11.md",
        "2018-04-04.md",
        "2018-03-22.md",
        "2018-03-19.md",
        "2018-03-18.md",
        "2018-03-07.md",
        "2018-02-28.md",
        "2018-02-14.md",
        "2018-02-07.md",
        "2018-01-31.md",
        "2018-01-17.md",
        "2018-01-10.md",
        "2017-12-13.md",
        "2017-12-06.md",
        "2017-11-29.md",
        "2017-11-13.md",
        "2017-11-12.md",
        "2017-11-01.md",
        "2017-10-25.md",
        "2017-10-18.md",
        "2017-10-04.md",
        "2017-09-27.md",
        "2017-09-13.md",
        "2017-09-06.md",
        "2017-08-23.md",
        "2017-08-09.md",
        "2017-08-02.md",
        "2017-07-20.md",
        "2017-07-17.md",
        "2017-07-16.md",
        "2017-07-05.md",
        "2017-06-28.md",
        "2017-06-14.md",
        "2017-06-07.md",
        "2017-05-24.md",
        "2017-05-10.md",
        "2017-05-03.md",
        "2017-04-26.md",
        "2017-04-12.md",
        "2017-03-30.md",
        "2017-03-29.md",
        "2017-03-26.md",
        "2017-03-15.md",
        "2017-03-08.md",
        "2017-03-01.md",
        "2017-02-22.md",
        "2017-02-08.md",
        "2017-02-01.md",
        "2017-01-25.md",
        "2017-01-11.md",
        "2017-01-04.md",
        "2016-12-14.md",
        "2016-12-07.md",
        "2016-11-30.md",
        "2016-11-17.md",
        "2016-11-13.md",
        "2016-11-02.md",
        "2016-10-26.md",
        "2016-10-12.md",
        "2016-10-05.md",
        "2016-09-28.md",
        "2016-09-14.md",
        "2016-08-31.md",
        "2016-08-17.md",
        "2016-08-03.md",
        "2016-07-21.md",
        "2016-07-17.md",
        "2016-07-06.md",
        "2016-06-22.md",
        "2016-06-08.md",
        "2016-06-01.md",
        "2016-05-25.md",
        "2016-05-11.md",
        "2016-05-04.md",
        "2016-04-27.md",
        "2016-04-20.md",
        "2016-04-07.md",
        "2016-04-03.md",
        "2016-03-23.md",
        "2016-03-09.md",
        "2016-03-02.md",
        "2016-02-24.md",
        "2016-02-10.md",
        "2016-02-03.md",
        "2016-01-27.md",
        "2016-01-13.md",
        "2016-01-06.md",
        "2015-12-16.md",
        "2015-12-09.md",
        "2015-11-25.md",
        "2015-11-18.md",
        "2015-11-05.md",
        "2015-11-01.md",
        "2015-10-21.md",
        "2015-10-14.md",
        "2015-10-07.md",
        "2015-09-23.md",
        "2015-09-09.md",
        "2015-09-02.md",
        "2015-08-26.md",
        "2015-08-12.md",
        "2015-08-05.md",
        "2015-07-24.md",
        "2015-07-23.md",
        "2015-07-20.md",
        "2015-07-19.md",
        "2015-07-08.md",
        "2015-07-01.md",
        "2015-06-24.md",
        "2015-06-10.md",
        "2015-06-03.md",
        "2015-05-27.md",
        "2015-05-13.md",
        "2015-04-29.md",
        "2015-04-15.md",
        "2015-04-08.md",
        "2015-03-26.md",
        "2015-03-24.md",
        "2015-03-22.md",
        "2015-03-11.md",
        "2015-03-04.md",
        "2015-02-25.md",
        "2015-02-11.md",
        "2015-02-04.md",
        "2015-01-21.md",
        "2015-01-14.md",
        "2015-01-07.md",
        "2014-12-10.md",
        "2014-12-03.md",
        "2014-11-26.md",
        "2014-11-13.md",
        "2014-11-11.md",
        "2014-11-10.md",
        "2014-11-09.md",
        "2014-10-29.md",
        "2014-10-22.md",
        "2014-10-08.md",
        "2014-10-01.md",
        "2014-09-24.md",
        "2014-09-10.md",
        "2014-09-03.md",
        "2014-08-27.md",
        "2014-08-13.md",
        "2014-08-06.md",
        "2014-07-20.md",
        "2014-07-09.md",
        "2014-07-02.md",
        "2014-06-25.md",
        "2014-06-11.md",
        "2014-06-04.md",
        "2014-05-28.md",
        "2014-05-14.md",
        "2014-05-08.md",
        "2014-04-30.md",
        "2014-04-16.md",
        "2014-04-09.md",
        "2014-04-02.md",
        "2014-03-26.md",
        "2014-03-19.md",
        "2014-03-06.md",
        "2014-03-04.md",
        "2014-03-02.md",
        "2014-02-19.md",
        "2014-02-12.md",
        "2014-02-05.md",
        "2014-01-29.md",
        "2014-01-22.md",
        "2014-01-15.md",
        "2014-01-08.md",
        "2013-12-18.md",
        "2013-12-11.md",
        "2013-11-27.md",
        "2013-11-20.md",
        "2013-11-13.md",
        "2013-11-08.md",
        "2013-11-07.md",
        "2013-11-05.md",
        "2013-11-03.md",
        "2013-10-23.md",
        "2013-10-09.md",
        "2013-10-02.md",
        "2013-09-25.md",
        "2013-09-18.md",
        "2013-09-11.md",
        "2013-09-04.md",
        "2013-08-28.md",
        "2013-08-14.md",
        "2013-08-01.md",
        "2013-07-30.md",
        "2013-07-28.md",
        "2013-07-17.md",
        "2013-07-10.md",
        "2013-07-03.md",
        "2013-06-26.md",
        "2013-06-19.md",
        "2013-06-12.md",
        "2013-06-03.md",
        "2013-05-22.md",
        "2013-05-09.md",
        "2013-05-01.md",
        "2013-04-24.md",
        "2013-04-10.md",
        "2013-04-03.md",
        "2013-03-27.md",
        "2013-03-14.md",
        "2013-03-12.md",
        "2013-03-10.md",
        "2013-02-27.md",
        "2013-02-13.md",
        "2013-02-06.md",
        "2013-01-30.md",
        "2013-01-16.md",
        "2013-01-09.md",
        "2012-12-19.md",
        "2012-12-12.md",
        "2012-12-05.md",
        "2012-11-28.md",
        "2012-11-08.md",
        "2012-11-06.md",
        "2012-11-04.md",
        "2012-10-24.md",
        "2012-10-10.md",
        "2012-10-03.md",
        "2012-09-19.md",
        "2012-09-12.md",
        "2012-09-05.md",
        "2012-08-29.md",
        "2012-08-22.md",
        "2012-08-15.md",
        "2012-08-02.md",
        "2012-07-31.md",
        "2012-07-29.md",
        "2012-07-25.md",
        "2012-07-18.md",
        "2012-07-11.md",
        "2012-06-27.md",
        "2012-06-13.md",
        "2012-06-06.md",
        "2012-05-30.md",
        "2012-05-23.md",
        "2012-05-16.md",
        "2012-05-10.md",
        "2012-05-02.md",
        "2012-04-25.md",
        "2012-04-18.md",
        "2012-04-11.md",
        "2012-03-29.md",
        "2012-03-27.md",
        "2012-03-25.md",
        "2012-03-14.md",
        "2012-03-07.md",
        "2012-02-29.md",
        "2012-02-22.md",
        "2012-02-08.md",
        "2012-01-25.md",
        "2012-01-18.md",
        "2012-01-11.md",
        "2012-01-04.md",
        "2011-12-21.md",
        "2011-12-14.md",
        "2011-12-07.md",
        "2011-11-30.md",
        "2011-11-17.md",
        "2011-11-15.md",
        "2011-11-13.md",
        "2011-11-02.md",
        "2011-10-26.md",
        "2011-10-12.md",
        "2011-10-05.md",
        "2011-09-28.md",
        "2011-09-21.md",
        "2011-09-14.md",
        "2011-09-07.md",
        "2011-08-24.md",
        "2011-08-10.md",
        "2011-07-28.md",
        "2011-07-26.md",
        "2011-07-24.md",
        "2011-07-13.md",
        "2011-07-06.md",
        "2011-06-29.md",
        "2011-06-22.md",
        "2011-06-15.md",
        "2011-06-08.md",
        "2011-06-01.md",
        "2011-05-25.md",
        "2011-05-12.md",
        "2011-05-04.md",
        "2011-04-27.md",
        "2011-04-13.md",
        "2011-04-06.md",
        "2011-03-29.md",
        "2011-03-09.md",
        "2011-03-02.md",
        "2011-02-23.md",
        "2011-02-09.md",
        "2011-02-02.md",
        "2011-02-01.md",
        "2011-01-26.md",
        "2011-01-19.md",
        "2011-01-12.md",
        "2011-01-05.md",
        "2010-12-22.md",
        "2010-12-01.md",
        "2010-11-24.md",
        "2010-10-27.md",
        "2010-10-13.md",
        "2010-09-29.md",
        "2010-09-22.md",
        "2010-09-16.md",
        "2010-09-08.md",
        "2010-09-01.md",
        "2010-08-25.md",
        "2010-08-11.md",
        "2010-07-14.md",
        "2010-07-07.md",
        "2010-06-23.md",
        "2010-06-02.md",
        "2010-05-12.md",
        "2010-04-28.md",
        "2010-04-14.md",
        "2010-04-07.md",
        "2010-03-10.md",
        "2010-03-03.md",
        "2010-02-24.md",
        "2010-02-10.md",
        "2010-02-03.md",
        "2010-02-01.md",
        "2010-01-27.md",
        "2010-01-20.md",
        "2010-01-13.md",
        "2010-01-07.md",
        "2010-01-06.md",
        "2009-12-09.md",
        "2009-12-02.md",
        "2009-11-25.md",
        "2009-11-04.md",
        "2009-10-28.md",
        "2009-10-21.md",
        "2009-10-14.md",
        "2009-10-07.md",
        "2009-09-25.md",
        "2009-09-23.md",
        "2009-09-09.md",
        "2009-09-02.md",
        "2009-08-12.md",
        "2009-07-01.md",
        "2009-06-24.md",
        "2009-06-10.md",
        "2009-06-03.md",
        "2009-05-27.md",
        "2009-05-13.md",
        "2009-04-08.md",
        "2009-04-01.md",
        "2009-03-18.md",
        "2009-03-04.md",
        "2009-02-25.md",
        "2009-02-18.md",
        "2009-02-05.md",
        "2009-02-04.md",
        "2009-01-28.md",
        "2009-01-21.md",
        "2009-01-14.md",
        "2009-01-07.md",
        "2008-12-17.md",
        "2008-12-03.md",
        "2008-11-05.md",
        "2008-10-15.md",
        "2008-10-08.md",
        "2008-10-03.md",
        "2008-10-01.md",
        "2008-09-24.md",
        "2008-09-17.md",
        "2008-09-03.md",
        "2008-08-27.md",
        "2008-08-20.md",
        "2008-08-13.md",
        "2008-08-06.md",
        "2008-07-23.md",
        "2008-07-16.md",
        "2008-07-02.md",
        "2008-06-25.md",
        "2008-06-18.md",
        "2008-06-12.md",
        "2008-06-04.md",
        "2008-05-28.md",
        "2008-05-21.md",
        "2008-05-07.md",
        "2008-04-16.md",
        "2008-04-02.md",
        "2008-03-26.md",
        "2008-02-20.md",
        "2008-02-13.md",
        "2008-02-06.md",
        "2008-01-30.md",
        "2008-01-16.md",
        "2008-01-09.md",
        "2007-12-19.md",
        "2007-11-21.md",
        "2007-11-07.md",
        "2007-10-17.md",
        "2007-10-03.md",
        "2007-09-19.md",
        "2007-09-05.md",
        "2007-08-15.md",
        "2007-07-26.md",
        "2007-07-24.md",
        "2007-07-11.md",
        "2007-06-20.md",
        "2007-06-06.md",
        "2007-05-16.md",
        "2007-05-02.md",
        "2007-04-18.md",
        "2007-04-04.md",
        "2007-03-18.md",
        "2007-03-07.md",
        "2007-02-21.md",
        "2007-02-07.md",
        "2007-01-24.md",
        "2007-01-10.md",
        "2006-12-20.md",
        "2006-12-06.md",
        "2006-11-22.md",
        "2006-11-05.md",
        "2006-11-01.md",
        "2006-10-25.md",
        "2006-10-04.md",
        "2006-09-20.md",
        "2006-09-06.md",
        "2006-08-30.md",
        "2006-08-02.md",
        "2006-07-09.md",
        "2006-07-05.md",
        "2006-06-21.md",
        "2006-06-07.md",
        "2006-05-17.md",
        "2006-05-03.md",
        "2006-04-17.md",
        "2006-04-05.md",
        "2006-03-19.md",
        "2006-03-15.md",
        "2006-02-15.md",
        "2006-02-01.md",
        "2006-01-18.md",
        "2006-01-04.md",
        "2005-12-21.md",
        "2005-12-07.md",
        "2005-11-10.md",
        "2005-11-02.md",
        "2005-10-12.md",
        "2005-09-14.md",
        "2005-08-02.md",
        "2005-07-13.md",
        "2005-06-10.md",
        "2005-05-11.md",
        "2005-04-13.md",
        "2005-03-07.md",
        "2005-03-01.md",
        "2005-02-08.md",
        "2005-01-11.md",
        "2004-12-14.md",
        "2004-11-07.md",
        "2004-10-12.md",
        "2004-09-14.md",
        "2004-08-03.md",
        "2004-07-13.md",
        "2004-06-08.md",
        "2004-05-11.md",
        "2004-04-13.md",
        "2004-03-02.md",
        "2004-02-10.md",
        "2004-01-13.md",
        "2003-12-09.md",
        "2003-11-09.md",
        "2003-11-04.md",
        "2003-10-14.md",
        "2003-09-09.md",
        "2003-08-12.md",
        "2003-07-17.md",
        "2003-07-08.md",
        "2003-06-10.md",
        "2003-05-13.md",
        "2003-04-08.md",
        "2003-03-18.md",
        "2003-03-11.md",
        "2003-02-11.md",
        "2003-01-14.md",
        "2002-12-10.md",
        "2002-11-17.md",
        "2002-10-08.md",
        "2002-09-10.md",
        "2002-08-13.md",
        "2002-07-16.md",
        "2002-06-11.md",
        "2002-05-14.md",
        "2002-04-09.md",
        "2002-03-19.md",
        "2002-03-12.md",
        "2002-02-15.md",
        "2002-02-12.md",
        "2002-01-08.md",
        "2001-12-11.md",
        "2001-11-20.md",
        "2001-10-09.md",
        "2001-09-24.md",
        "2001-09-11.pdf",
        "2001-09-11.md",
        "2001-08-07.md",
        "2001-07-10.md",
        "2001-06-12.md",
        "2001-05-08.md",
        "2001-04-10.md",
        "2001-03-20.md",
        "2001-02-13.md",
        "2001-01-09.md",
        "2000-12-12.md",
        "2000-11-13.md",
        "2000-10-16.md",
        "2000-09-11.md",
        "2000-08-14.md",
        "2000-08-01.md",
        "2000-07-10.md",
        "2000-06-12.md",
        "2000-05-08.md",
        "2000-04-10.md",
        "2000-03-26.md",
        "2000-02-14.md",
        "2000-01-10.md",
        "1999-12-14.md",
        "1999-11-09.md",
        "1999-10-19.md",
        "1999-09-14.md",
        "1999-08-10.md",
        "1999-07-11.md",
        "1999-06-15.md",
        "1999-05-11.md",
        "1999-04-13.md",
        "1999-03-16.md",
        "1999-02-09.md",
        "1999-01-12.md",
        "1998-12-08.md",
        "1998-11-10.md",
        "1998-10-13.md",
        "1998-09-15.md",
        "1998-08-23.md",
        "1998-08-04.md",
        "1998-07-14.md",
        "1998-06-09.md",
        "1998-05-12.md",
        "1998-04-02.md",
        "1998-03-31.pdf",
        "1998-03-31.md",
        "1998-03-10.md",
        "1998-02-10.md",
        "1998-01-20.md",
        "1997-12-10.md",
        "1997-12-09.md",
        "1997-11-11.md",
        "1997-10-14.md",
        "1997-09-09.md",
        "1997-08-13.md",
        "1997-08-12.md",
        "1997-07-15.md",
        "1997-06-17.md",
        "1997-04-09.md",
        "1997-04-08.md",
        "1997-03-11.md",
        "1997-01-14.md",
        "1996-12-10.md",
        "1996-11-12.md",
        "1996-10-08.md",
        "1996-09-12.md",
        "1996-08-13.md",
        "1996-07-09.md",
        "1996-06-26.md",
        "1996-06-11.md",
        "1996-05-14.md",
        "1996-04-09.md",
        "1996-03-06.md",
        "1996-03-05.md",
        "1996-02-13.md",
        "1996-01-09.md",
        "1995-12-03.md",
        "1995-11-14.md",
        "1995-10-10.md",
        "1995-09-12.md",
        "1995-08-08.md",
        "1995-07-19.md",
        "1995-06-29.md",
        "1995-06-07.md",
        "1995-05-10.md",
        "1995-04-19.md",
        "1995-04-05.md",
        "1995-04-02.md",
        "1995-03-22.md",
        "1995-02-28.md",
        "1995-02-07.md",
        "1995-01-10.md",
        "1994-12-09.md",
        "1994-12-07.md",
        "1994-11-09.md",
        "1994-10-13.md",
        "1994-09-23.md",
        "1994-07-27.md",
        "1994-07-05.md",
        "1994-05-24.md",
        "1994-04-29.md",
        "1994-03-30.md",
        "1993-07-13.md",
        "1993-03-30.md",
        "1992-10-29.md",
        "1992-07-17.md",
        "1992-06-18.md",
        "1992-01-07.md",
        "1991-11-19.md",
        "1991-10-10.md",
        "1991-06-14.md",
        "1991-01-08.md",
        "1990-10-11.md",
        "1990-06-28.md",
        "1990-04-26.md",
        "1990-01-03.md",
        "1988-07-12.md",
        "1988-03-21.md",
    ]

    nametimes_by_year = defaultdict(list)
    for name in sorted(scraped_basenames):
        year = name.split("-")[0]
        nametimes_by_year[year].append( (name, get_time(name)) )
    return nametimes_by_year

"""
