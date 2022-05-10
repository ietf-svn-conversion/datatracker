# Copyright The IETF Trust 2018-2020, All Rights Reserved
# Generated by Django 1.11.10 on 2018-02-20 10:52


import datetime
from django.db import migrations, models
import django.db.models.deletion
import ietf.review.models
import ietf.utils.models
import ietf.utils.validators


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('group', '0001_initial'),
        ('name', '0001_initial'),
        ('person', '0001_initial'),
        ('doc', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='NextReviewerInTeam',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('next_reviewer', ietf.utils.models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='person.Person')),
                ('team', ietf.utils.models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='group.Group')),
            ],
            options={
                'verbose_name': 'next reviewer in team setting',
                'verbose_name_plural': 'next reviewer in team settings',
            },
        ),
        migrations.CreateModel(
            name='ReviewerSettings',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('min_interval', models.IntegerField(blank=True, choices=[(7, 'Once per week'), (14, 'Once per fortnight'), (30, 'Once per month'), (61, 'Once per two months'), (91, 'Once per quarter')], null=True, verbose_name='Can review at most')),
                ('filter_re', models.CharField(blank=True, help_text='Draft names matching this regular expression should not be assigned', max_length=255, validators=[ietf.utils.validators.RegexStringValidator()], verbose_name='Filter regexp')),
                ('skip_next', models.IntegerField(default=0, verbose_name='Skip next assignments')),
                ('remind_days_before_deadline', models.IntegerField(blank=True, help_text="To get an email reminder in case you forget to do an assigned review, enter the number of days before review deadline you want to receive it. Clear the field if you don't want a reminder.", null=True)),
                ('expertise', models.TextField(blank=True, default='', help_text="Describe the reviewer's expertise in this team's area", max_length=2048, verbose_name="Reviewer's expertise in this team's area")),
                ('person', ietf.utils.models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='person.Person')),
                ('team', ietf.utils.models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='group.Group')),
            ],
            options={
                'verbose_name_plural': 'reviewer settings',
            },
        ),
        migrations.CreateModel(
            name='ReviewRequest',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('old_id', models.IntegerField(blank=True, help_text='ID in previous review system', null=True)),
                ('time', models.DateTimeField(default=datetime.datetime.now)),
                ('deadline', models.DateField()),
                ('requested_rev', models.CharField(blank=True, help_text='Fill in if a specific revision is to be reviewed, e.g. 02', max_length=16, verbose_name='requested revision')),
                ('comment', models.TextField(blank=True, default='', help_text='Provide any additional information to show to the review team secretary and reviewer', max_length=2048, verbose_name="Requester's comments and instructions")),
                ('reviewed_rev', models.CharField(blank=True, max_length=16, verbose_name='reviewed revision')),
                ('doc', ietf.utils.models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='reviewrequest_set', to='doc.Document')),
                ('requested_by', ietf.utils.models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='person.Person')),
                ('result', ietf.utils.models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='name.ReviewResultName')),
                ('review', ietf.utils.models.OneToOneField(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='doc.Document')),
                ('reviewer', ietf.utils.models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='person.Email')),
                ('state', ietf.utils.models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='name.ReviewRequestStateName')),
                ('team', ietf.utils.models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='group.Group')),
                ('type', ietf.utils.models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='name.ReviewTypeName')),
            ],
        ),
        migrations.CreateModel(
            name='ReviewSecretarySettings',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('remind_days_before_deadline', models.IntegerField(blank=True, help_text="To get an email reminder in case a reviewer forgets to do an assigned review, enter the number of days before review deadline you want to receive it. Clear the field if you don't want a reminder.", null=True)),
                ('person', ietf.utils.models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='person.Person')),
                ('team', ietf.utils.models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='group.Group')),
            ],
            options={
                'verbose_name_plural': 'review secretary settings',
            },
        ),
        migrations.CreateModel(
            name='ReviewTeamSettings',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('autosuggest', models.BooleanField(default=True, verbose_name='Automatically suggest possible review requests')),
                ('group', ietf.utils.models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, to='group.Group')),
                ('review_results', models.ManyToManyField(default=ietf.review.models.get_default_review_results, to='name.ReviewResultName')),
                ('review_types', models.ManyToManyField(default=ietf.review.models.get_default_review_types, to='name.ReviewTypeName')),
            ],
            options={
                'verbose_name': 'Review team settings',
                'verbose_name_plural': 'Review team settings',
            },
        ),
        migrations.CreateModel(
            name='ReviewWish',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('time', models.DateTimeField(default=datetime.datetime.now)),
                ('doc', ietf.utils.models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='doc.Document')),
                ('person', ietf.utils.models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='person.Person')),
                ('team', ietf.utils.models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='group.Group')),
            ],
            options={
                'verbose_name_plural': 'review wishes',
            },
        ),
        migrations.CreateModel(
            name='UnavailablePeriod',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('start_date', models.DateField(default=datetime.date.today, help_text="Choose the start date so that you can still do a review if it's assigned just before the start date - this usually means you should mark yourself unavailable for assignment some time before you are actually away.", null=True)),
                ('end_date', models.DateField(blank=True, help_text='Leaving the end date blank means that the period continues indefinitely. You can end it later.', null=True)),
                ('availability', models.CharField(choices=[('canfinish', 'Can do follow-ups'), ('unavailable', 'Completely unavailable')], max_length=30)),
                ('person', ietf.utils.models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='person.Person')),
                ('team', ietf.utils.models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='group.Group')),
            ],
        ),
    ]
