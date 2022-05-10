# Copyright The IETF Trust 2019-2020, All Rights Reserved
# Generated by Django 1.11.20 on 2019-05-21 14:27


import sys

from tqdm import tqdm

from django.db import migrations


def forward(apps, schema_editor):

    Document                    = apps.get_model('doc','Document')
    CommunityList               = apps.get_model('community', 'CommunityList')
    CommunityListDocs           = apps.get_model('community', 'CommunityListDocs')
    SearchRule                  = apps.get_model('community', 'SearchRule')
    SearchRuleDocs              = apps.get_model('community', 'SearchRuleDocs')

    # Document id fixup ------------------------------------------------------------

    objs = Document.objects.in_bulk()
    nameid = { o.name: o.id for id, o in objs.items() }

    sys.stderr.write('\n')

    sys.stderr.write(' {}.{}:\n'.format(CommunityList.__name__, 'added_docs'))
    count = 0
    for l in tqdm(CommunityList.objects.all()):
        for d in l.added_docs.all():
            count += 1
            CommunityListDocs.objects.get_or_create(communitylist=l, document_id=nameid[d.name])
    sys.stderr.write(f' {count} CommunityListDocs objects created\n')

    sys.stderr.write(' {}.{}:\n'.format(SearchRule.__name__, 'name_contains_index'))
    count = 0
    for r in tqdm(SearchRule.objects.all()):
        for d in r.name_contains_index.all():
            count += 1
            SearchRuleDocs.objects.get_or_create(searchrule=r, document_id=nameid[d.name])
    sys.stderr.write(f' {count} SearchRuleDocs objects created\n')

def reverse(apps, schema_editor):
    pass

class Migration(migrations.Migration):

    dependencies = [
        ('community', '0003_add_communitylist_docs2_m2m'),
        ('doc', '0014_set_document_docalias_id'),
    ]

    operations = [
        migrations.RunPython(forward, reverse),
    ]
