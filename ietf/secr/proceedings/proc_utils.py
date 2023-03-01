# Copyright The IETF Trust 2013-2020, All Rights Reserved
# -*- coding: utf-8 -*-


'''
proc_utils.py

This module contains all the functions for generating static proceedings pages
'''
import datetime
import os
import pytz
import subprocess
from urllib.parse import urlencode

import debug        # pyflakes:ignore

from django.conf import settings

from ietf.doc.models import Document, DocAlias, DocEvent, NewRevisionDocEvent, State
from ietf.group.models import Group
from ietf.meeting.models import Meeting, SessionPresentation, SchedTimeSessAssignment
from ietf.person.models import Person
from ietf.utils.log import log
from ietf.utils.timezone import make_aware


def _get_session(number,name,date,time):
    '''Lookup session using data from video title'''
    meeting = Meeting.objects.get(number=number)
    timeslot_time = make_aware(datetime.datetime.strptime(date + time,'%Y%m%d%H%M'), meeting.tz())
    try:
        assignment = SchedTimeSessAssignment.objects.get(
            schedule__in = [meeting.schedule, meeting.schedule.base],
            session__group__acronym = name.lower(),
            timeslot__time = timeslot_time,
        )
    except (SchedTimeSessAssignment.DoesNotExist, SchedTimeSessAssignment.MultipleObjectsReturned):
        return None

    return assignment.session

def _get_urls_from_json(doc):
    '''Returns list of dictionary title,url from search results'''
    urls = []
    for item in doc['items']:
        title = item['snippet']['title']
        #params = dict(v=item['snippet']['resourceId']['videoId'], list=item['snippet']['playlistId'])
        params = [('v',item['snippet']['resourceId']['videoId']), ('list',item['snippet']['playlistId'])]
        url = settings.YOUTUBE_BASE_URL + '?' + urlencode(params)
        urls.append(dict(title=title, url=url))
    return urls

def create_recording(session, url, title=None, user=None):
    '''
    Creates the Document type=recording, setting external_url and creating
    NewRevisionDocEvent
    '''
    sequence = get_next_sequence(session.group,session.meeting,'recording')
    name = 'recording-{}-{}-{}'.format(session.meeting.number,session.group.acronym,sequence)
    time = session.official_timeslotassignment().timeslot.time.strftime('%Y-%m-%d %H:%M')
    if not title:
        if url.endswith('mp3'):
            title = 'Audio recording for {}'.format(time)
        else:
            title = 'Video recording for {}'.format(time)
        
    doc = Document.objects.create(name=name,
                                  title=title,
                                  external_url=url,
                                  group=session.group,
                                  rev='00',
                                  type_id='recording')
    doc.set_state(State.objects.get(type='recording', slug='active'))

    DocAlias.objects.create(name=doc.name).docs.add(doc)
    
    # create DocEvent
    NewRevisionDocEvent.objects.create(type='new_revision',
                                       by=user or Person.objects.get(name='(System)'),
                                       doc=doc,
                                       rev=doc.rev,
                                       desc='New revision available',
                                       time=doc.time)
    pres = SessionPresentation.objects.create(session=session,document=doc,rev=doc.rev)
    session.sessionpresentation_set.add(pres)

    return doc

def get_next_sequence(group,meeting,type):
    '''
    Returns the next sequence number to use for a document of type = type.
    Takes a group=Group object, meeting=Meeting object, type = string
    '''
    aliases = DocAlias.objects.filter(name__startswith='{}-{}-{}-'.format(type,meeting.number,group.acronym))
    if not aliases:
        return 1
    aliases = aliases.order_by('name')
    sequence = int(aliases.last().name.split('-')[-1]) + 1
    return sequence


def get_activity_stats(sdate, edate):
    '''
    This function takes a date range and produces a dictionary of statistics / objects for
    use in an activity report.  Generally the end date will be the date of the last meeting
    and the start date will be the date of the meeting before that.

    Data between midnight UTC on the specified dates are included in the stats.
    '''
    sdatetime = pytz.utc.localize(datetime.datetime.combine(sdate, datetime.time()))
    edatetime = pytz.utc.localize(datetime.datetime.combine(edate, datetime.time()))

    data = {}
    data['sdate'] = sdate
    data['edate'] = edate

    events = DocEvent.objects.filter(doc__type='draft', time__gte=sdatetime, time__lt=edatetime)
    
    data['actions_count'] = events.filter(type='iesg_approved').count()
    data['last_calls_count'] = events.filter(type='sent_last_call').count()
    new_draft_events = events.filter(newrevisiondocevent__rev='00')
    new_drafts = list(set([ e.doc_id for e in new_draft_events ]))
    data['new_docs'] = list(set([ e.doc for e in new_draft_events ]))
    data['new_drafts_count'] = len(new_drafts)
    data['new_drafts_updated_count'] = events.filter(doc__id__in=new_drafts,newrevisiondocevent__rev='01').count()
    data['new_drafts_updated_more_count'] = events.filter(doc__id__in=new_drafts,newrevisiondocevent__rev='02').count()
    
    update_events = events.filter(type='new_revision').exclude(doc__id__in=new_drafts)
    data['updated_drafts_count'] = len(set([ e.doc_id for e in update_events ]))
    
    # Calculate Final Four Weeks stats (ffw)
    ffwdate = edatetime - datetime.timedelta(days=28)
    ffw_new_count = events.filter(time__gte=ffwdate,newrevisiondocevent__rev='00').count()
    try:
        ffw_new_percent = format(ffw_new_count / float(data['new_drafts_count']),'.0%')
    except ZeroDivisionError:
        ffw_new_percent = 0
        
    data['ffw_new_count'] = ffw_new_count
    data['ffw_new_percent'] = ffw_new_percent
    
    ffw_update_events = events.filter(time__gte=ffwdate,type='new_revision').exclude(doc__id__in=new_drafts)
    ffw_update_count = len(set([ e.doc_id for e in ffw_update_events ]))
    try:
        ffw_update_percent = format(ffw_update_count / float(data['updated_drafts_count']),'.0%')
    except ZeroDivisionError:
        ffw_update_percent = 0
    
    data['ffw_update_count'] = ffw_update_count
    data['ffw_update_percent'] = ffw_update_percent

    rfcs = events.filter(type='published_rfc')
    data['rfcs'] = rfcs.select_related('doc').select_related('doc__group').select_related('doc__intended_std_level')

    data['counts'] = {'std':rfcs.filter(doc__intended_std_level__in=('ps','ds','std')).count(),
                      'bcp':rfcs.filter(doc__intended_std_level='bcp').count(),
                      'exp':rfcs.filter(doc__intended_std_level='exp').count(),
                      'inf':rfcs.filter(doc__intended_std_level='inf').count()}

    data['new_groups'] = Group.objects.filter(
        type='wg',
        groupevent__changestategroupevent__state='active',
        groupevent__time__gte=sdatetime,
        groupevent__time__lt=edatetime)
        
    data['concluded_groups'] = Group.objects.filter(
        type='wg',
        groupevent__changestategroupevent__state='conclude',
        groupevent__time__gte=sdatetime,
        groupevent__time__lt=edatetime)

    return data

def is_powerpoint(doc):
    '''
    Returns true if document is a Powerpoint presentation
    '''
    return doc.file_extension() in ('ppt','pptx')

def post_process(doc):
    '''
    Does post processing on uploaded file.
    - Convert PPT to PDF
    '''
    if is_powerpoint(doc) and hasattr(settings,'SECR_PPT2PDF_COMMAND'):
        try:
            cmd = list(settings.SECR_PPT2PDF_COMMAND) # Don't operate on the list actually in settings
            cmd.append(doc.get_file_path())                                 # outdir
            cmd.append(os.path.join(doc.get_file_path(),doc.uploaded_filename))  # filename
            subprocess.check_call(cmd)
        except (subprocess.CalledProcessError, OSError) as error:
            log("Error converting PPT: %s" % (error))
            return
        # change extension
        base,ext = os.path.splitext(doc.uploaded_filename)
        doc.uploaded_filename = base + '.pdf'

        e = DocEvent.objects.create(
            type='changed_document',
            by=Person.objects.get(name="(System)"),
            doc=doc,
            rev=doc.rev,
            desc='Converted document to PDF',
        )
        doc.save_with_history([e])
