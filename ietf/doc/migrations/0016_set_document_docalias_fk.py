# Copyright The IETF Trust 2019-2020, All Rights Reserved
# Generated by Django 1.11.20 on 2019-05-08 14:04


import sys

from tqdm import tqdm

from django.db import migrations

def forward(apps, schema_editor):

    def add_id_fk(o, a, nameid):
        n = getattr(o, a+'_id')
        if n:
            i = nameid[n]
            if not isinstance(i, int):
                raise ValueError(f"Inappropriate value: {o.__class__.__name__}: nameid[{n}]: {i}")
            if getattr(o, a+'2_id') != i:
                setattr(o, a+'2_id', i)
                o.save()

    DocAlias                    = apps.get_model('doc','DocAlias')
    DocEvent                    = apps.get_model('doc', 'DocEvent')
    DocHistory                  = apps.get_model('doc', 'DocHistory')
    Document                    = apps.get_model('doc', 'Document')
    DocumentAuthor              = apps.get_model('doc', 'DocumentAuthor')
    DocumentLanguages           = apps.get_model('doc', 'DocumentLanguages')
    DocumentStates              = apps.get_model('doc', 'DocumentStates')
    DocumentTags                = apps.get_model('doc', 'DocumentTags')
    DocumentURL                 = apps.get_model('doc', 'DocumentURL')
    Group                       = apps.get_model('group', 'Group')
    IprDocRel                   = apps.get_model('ipr', 'IprDocRel')
    LiaisonStatementAttachment  = apps.get_model('liaisons', 'LiaisonStatementAttachment')
    RelatedDocHistory           = apps.get_model('doc', 'RelatedDocHistory')
    RelatedDocument             = apps.get_model('doc', 'RelatedDocument')
    ReviewAssignment            = apps.get_model('review', 'ReviewAssignment')
    ReviewRequest               = apps.get_model('review', 'ReviewRequest')
    ReviewWish                  = apps.get_model('review', 'ReviewWish')
    SessionPresentation         = apps.get_model('meeting', 'SessionPresentation')
    Submission                  = apps.get_model('submit', 'Submission')

    # Document id fixup ------------------------------------------------------------

    objs = Document.objects.in_bulk()
    nameid = { o.name: o.id for id, o in objs.items() }

    sys.stderr.write('\n')

    sys.stderr.write('Setting Document FKs:\n')

    for C, a in [ 
            ( DocAlias                   , 'document'),
            ( DocEvent                   , 'doc'),
            ( DocHistory                 , 'doc'),
            ( DocumentAuthor             , 'document'),
            ( DocumentLanguages          , 'document'),
            ( DocumentStates             , 'document'),
            ( DocumentTags               , 'document'),
            ( DocumentURL                , 'doc'),
            ( Group                      , 'charter'),
            ( LiaisonStatementAttachment , 'document'),
            ( RelatedDocument            , 'source'),
            ( ReviewAssignment           , 'review'),
            ( ReviewRequest              , 'doc'),
            ( ReviewRequest              , 'unused_review'),
            ( ReviewWish                 , 'doc'),
            ( SessionPresentation        , 'document'),
            ( Submission                 , 'draft'),
        ]:
        sys.stderr.write(f' {C.__name__}.{a}:\n')
        for o in tqdm(C.objects.all()):
            add_id_fk(o, a, nameid)

    # DocAlias id fixup ------------------------------------------------------------
    
    sys.stderr.write('\n')

    objs = DocAlias.objects.in_bulk()
    nameid = { o.name: o.id for id, o in objs.items() }

    sys.stderr.write('Setting DocAlias FKs:\n')

    for C, a in [
            ( IprDocRel                  , 'document'),
            ( RelatedDocument            , 'target'),
            ( RelatedDocHistory          , 'target'),
        ]:
        sys.stderr.write(f' {C.__name__}.{a}:\n')
        for o in tqdm(C.objects.all()):
            add_id_fk(o, a, nameid)

def reverse(apps, schema_editor):
    pass

class Migration(migrations.Migration):

    dependencies = [
        ('community', '0004_set_document_m2m_keys'),
        ('doc', '0015_2_add_doc_document_m2m_fields'),
        ('group', '0014_set_document_m2m_keys'),
        ('ipr', '0003_add_ipdocrel_document2_fk'),
        ('liaisons', '0003_liaison_document2_fk'),
        ('meeting', '0015_sessionpresentation_document2_fk'),
        ('message', '0003_set_document_m2m_keys'),
        ('review', '0011_review_document2_fk'),
        ('submit', '0002_submission_document2_fk'),
    ]

    operations = [
        migrations.RunPython(forward, reverse),
    ]
