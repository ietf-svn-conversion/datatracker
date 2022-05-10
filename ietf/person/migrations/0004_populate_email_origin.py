# Copyright The IETF Trust 2018-2020, All Rights Reserved
# Generated by Django 1.11.12 on 2018-05-10 05:28


import sys

from django.db import migrations

import debug                            # pyflakes:ignore

def populate_email_origin(apps, schema_editor):
    Submission      = apps.get_model('submit', 'Submission')
    Document        = apps.get_model('doc', 'Document')
    DocHistory      = apps.get_model('doc', 'DocHistory')
    DocumentAuthor  = apps.get_model('doc', 'DocumentAuthor')
    DocHistoryAuthor= apps.get_model('doc', 'DocHistoryAuthor')
    Role            = apps.get_model('group', 'Role')
    RoleHistory     = apps.get_model('group', 'RoleHistory')
    ReviewRequest   = apps.get_model('review', 'ReviewRequest')
    LiaisonStatement= apps.get_model('liaisons', 'LiaisonStatement')
    #
    Email           = apps.get_model('person', 'Email')
    #
    sys.stdout.write("\n")
    #
    sys.stdout.write("\n    ** This migration may take some time.  Expect at least a few minutes **.\n\n")
    sys.stdout.write("    Initializing data structures...\n")
    emails = { e.address: e for e in Email.objects.filter(origin='') }

    count = 0
    sys.stdout.write("    Assigning email origins from Submission records...\n")
    for o in Submission.objects.all().order_by('-submission_date'):
        for a in o.authors:
            addr = a['email']
            if addr in emails:
                e = emails[addr]
                if e.origin != o.name:
                    e.origin = "author: %s" % o.name
                    count += 1
                    e.save()
                    del emails[addr]
    sys.stdout.write("    Submission email origins assigned: %d\n" % count)

    for model in (DocumentAuthor, DocHistoryAuthor, ):
        count = 0
        sys.stdout.write("    Assigning email origins from %s records...\n" % model.__name__)
        for o in model.objects.filter(email__origin=''):
            if not o.email.origin:
                o.email.origin = "author: %s" % o.document.name
                o.email.save()
                count += 1
        sys.stdout.write("    %s email origins assigned: %d\n" % (model.__name__, count))

    for model in (Role, RoleHistory, ):
        count = 0
        sys.stdout.write("    Assigning email origins from %s records...\n" % model.__name__)
        for o in model.objects.filter(email__origin=''):
            if not o.email.origin:
                o.email.origin = "role: {} {}".format(o.group.acronym, o.name.slug)
                o.email.save()
                count += 1
        sys.stdout.write("    %s email origins assigned: %d\n" % (model.__name__, count))

    for model in (ReviewRequest, ):
        count = 0
        sys.stdout.write("    Assigning email origins from %s records...\n" % model.__name__)
        for o in model.objects.filter(reviewer__origin=''):
            if not o.reviewer.origin:
                o.reviewer.origin = "reviewer: %s" % (o.doc.name)
                o.reviewer.save()
                count += 1
        sys.stdout.write("    %s email origins assigned: %d\n" % (model.__name__, count))

    for model in (LiaisonStatement, ):
        count = 0
        sys.stdout.write("    Assigning email origins from %s records...\n" % model.__name__)
        for o in model.objects.filter(from_contact__origin=''):
            if not o.from_contact.origin:
                o.from_contact.origin = "liaison: %s" % (','.join([ g.acronym for g in o.from_groups.all() ]))
                o.from_contact.save()
                count += 1
        sys.stdout.write("    %s email origins assigned: %d\n" % (model.__name__, count))

    for model in (Document, DocHistory, ):
        count = 0
        sys.stdout.write("    Assigning email origins from %s records...\n" % model.__name__)
        for o in model.objects.filter(shepherd__origin=''):
            if not o.shepherd.origin:
                o.shepherd.origin = "shepherd: %s" % o.name
                o.shepherd.save()
                count += 1
        sys.stdout.write("    %s email origins assigned: %d\n" % (model.__name__, count))

    sys.stdout.write("\n")
    sys.stdout.write("    Email records with origin indication: %d\n" % Email.objects.exclude(origin='').count())
    sys.stdout.write("    Email records without origin indication: %d\n" % Email.objects.filter(origin='').count())

def reverse(apps, schema_editor):
    pass

class Migration(migrations.Migration):

    dependencies = [
        ('person', '0003_auto_20180504_1519'),
    ]

    operations = [
        migrations.RunPython(populate_email_origin, reverse)
    ]
