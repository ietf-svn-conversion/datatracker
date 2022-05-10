# Generated by Django 2.2.19 on 2021-04-13 09:17

from django.db import migrations

def populate_parent_types(apps, schema_editor):
    """Add default parent_types entries

    Data were determined from existing groups via this query:
    {t.slug: list(
        Group.objects.filter(type=t, parent__isnull=False).values_list('parent__type', flat=True).distinct()
    ) for t in GroupTypeName.objects.all()}
    """
    GroupFeatures = apps.get_model('group', 'GroupFeatures')
    GroupTypeName = apps.get_model('name', 'GroupTypeName')
    type_map = {
        'adhoc': ['ietf'],
        'admin': [],
        'ag': ['area', 'ietf'],
        'area': ['ietf'],
        'dir': ['area'],
        'iab': ['ietf'],
        'iana': [],
        'iesg': [],
        'ietf': ['ietf'],
        'individ': ['area'],
        'irtf': ['irtf'],
        'ise': [],
        'isoc': ['isoc'],
        'nomcom': ['area'],
        'program': ['ietf'],
        'rag': ['irtf'],
        'review': ['area'],
        'rfcedtyp': [],
        'rg': ['irtf'],
        'sdo': ['sdo', 'area'],
        'team': ['area'],
        'wg': ['area']
    }
    for type_slug, parent_slugs in type_map.items():
        if len(parent_slugs) > 0:
            features = GroupFeatures.objects.get(type__slug=type_slug)
            features.parent_types.add(*GroupTypeName.objects.filter(slug__in=parent_slugs))

    # validate
    for gtn in GroupTypeName.objects.all():
        slugs_in_db = {type.slug for type in gtn.features.parent_types.all()}
        assert(slugs_in_db == set(type_map[gtn.slug]))


def set_need_parent_values(apps, schema_editor):
    """Set need_parent values

    Data determined from existing groups using:

    GroupTypeName.objects.exclude(pk__in=Group.objects.filter(parent__isnull=True).values('type'))

    'iesg' has been removed because there are no groups of this type, so no parent types have
    been made available to it.
    """
    GroupFeatures = apps.get_model('group', 'GroupFeatures')

    GroupFeatures.objects.filter(
        type_id__in=('area', 'dir', 'individ', 'review', 'rg',)
    ).update(need_parent=True)


def set_default_parents(apps, schema_editor):
    GroupFeatures = apps.get_model('group', 'GroupFeatures')

    # rg-typed groups are children of the irtf group
    rg_features = GroupFeatures.objects.filter(type_id='rg').first()
    if rg_features:
        rg_features.default_parent = 'irtf'
        rg_features.save()


def empty_reverse(apps, schema_editor):
    pass  # nothing to do, field will be dropped


class Migration(migrations.Migration):

    dependencies = [
        ('group', '0043_add_groupfeatures_parent_type_fields'),
        ('person', '0019_auto_20210604_1443'),
    ]

    operations = [
        migrations.RunPython(populate_parent_types, empty_reverse),
        migrations.RunPython(set_need_parent_values, empty_reverse),
        migrations.RunPython(set_default_parents, empty_reverse),
    ]
