# Generated by Django 2.2.28 on 2022-06-30 23:15


from django.db import migrations


def forward(apps, schema_editor):
    SearchRule = apps.get_model('community', 'SearchRule')
    CommunityList = apps.get_model('community', 'CommunityList')
    Group = apps.get_model('group', 'Group')
    State = apps.get_model('doc', 'State')
    for group in Group.objects.filter(type_id__in=['wg','rg'], state_id='active'):
        com_list = CommunityList.objects.filter(group=group).first()
        if com_list is not None:
            SearchRule.objects.create(community_list=com_list, rule_type="group_exp", group=group, state=State.objects.get(slug="expired", type="draft"),)


def reverse(apps, schema_editor):
    SearchRule = apps.get_model('community', 'SearchRule')
    SearchRule.objects.filter(rule_type='group_exp').delete()


class Migration(migrations.Migration):
    dependencies = [
        ('community', '0008_add_group_exp_rule'),
    ]

    operations = [
        migrations.RunPython(forward, reverse),
    ]
