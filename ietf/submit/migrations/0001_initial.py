# Generated by Django 2.2.28 on 2023-03-20 19:22

from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone
import ietf.utils.accesstoken
import ietf.utils.models
import ietf.utils.timezone
import jsonfield.fields


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('message', '0001_initial'),
        ('name', '0001_initial'),
        ('person', '0001_initial'),
        ('group', '0001_initial'),
        ('doc', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Submission',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('remote_ip', models.CharField(blank=True, max_length=100)),
                ('access_key', models.CharField(default=ietf.utils.accesstoken.generate_random_key, max_length=255)),
                ('auth_key', models.CharField(blank=True, max_length=255)),
                ('name', models.CharField(db_index=True, max_length=255)),
                ('title', models.CharField(blank=True, max_length=255)),
                ('abstract', models.TextField(blank=True)),
                ('rev', models.CharField(blank=True, max_length=3)),
                ('pages', models.IntegerField(blank=True, null=True)),
                ('words', models.IntegerField(blank=True, null=True)),
                ('authors', jsonfield.fields.JSONField(default=list, help_text='List of authors with name, email, affiliation and country.')),
                ('note', models.TextField(blank=True)),
                ('replaces', models.CharField(blank=True, max_length=1000)),
                ('first_two_pages', models.TextField(blank=True)),
                ('file_types', models.CharField(blank=True, max_length=50)),
                ('file_size', models.IntegerField(blank=True, null=True)),
                ('document_date', models.DateField(blank=True, null=True)),
                ('submission_date', models.DateField(default=ietf.utils.timezone.date_today)),
                ('xml_version', models.CharField(default=None, max_length=4, null=True)),
                ('submitter', models.CharField(blank=True, help_text='Name and email of submitter, e.g. "John Doe &lt;john@example.org&gt;".', max_length=255)),
                ('draft', ietf.utils.models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='doc.Document')),
                ('formal_languages', models.ManyToManyField(blank=True, help_text='Formal languages used in document', to='name.FormalLanguageName')),
                ('group', ietf.utils.models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='group.Group')),
                ('state', ietf.utils.models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='name.DraftSubmissionStateName')),
            ],
        ),
        migrations.CreateModel(
            name='SubmissionEvent',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('time', models.DateTimeField(default=django.utils.timezone.now)),
                ('desc', models.TextField()),
                ('by', ietf.utils.models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='person.Person')),
                ('submission', ietf.utils.models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='submit.Submission')),
            ],
            options={
                'ordering': ('-time', '-id'),
            },
        ),
        migrations.CreateModel(
            name='SubmissionEmailEvent',
            fields=[
                ('submissionevent_ptr', models.OneToOneField(auto_created=True, on_delete=django.db.models.deletion.CASCADE, parent_link=True, primary_key=True, serialize=False, to='submit.SubmissionEvent')),
                ('msgtype', models.CharField(max_length=25)),
            ],
            options={
                'ordering': ['-time', '-id'],
            },
            bases=('submit.submissionevent',),
        ),
        migrations.CreateModel(
            name='SubmissionExtResource',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('display_name', models.CharField(blank=True, default='', max_length=255)),
                ('value', models.CharField(max_length=2083)),
                ('name', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='name.ExtResourceName')),
                ('submission', ietf.utils.models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='external_resources', to='submit.Submission')),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='SubmissionCheck',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('time', models.DateTimeField(default=django.utils.timezone.now)),
                ('checker', models.CharField(blank=True, max_length=256)),
                ('passed', models.BooleanField(default=False, null=True)),
                ('message', models.TextField(blank=True, null=True)),
                ('errors', models.IntegerField(blank=True, default=None, null=True)),
                ('warnings', models.IntegerField(blank=True, default=None, null=True)),
                ('items', jsonfield.fields.JSONField(blank=True, default='{}', null=True)),
                ('symbol', models.CharField(default='', max_length=64)),
                ('submission', ietf.utils.models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='checks', to='submit.Submission')),
            ],
        ),
        migrations.CreateModel(
            name='Preapproval',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(db_index=True, max_length=255)),
                ('time', models.DateTimeField(default=django.utils.timezone.now)),
                ('by', ietf.utils.models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='person.Person')),
            ],
        ),
        migrations.AddIndex(
            model_name='submissionevent',
            index=models.Index(fields=['-time', '-id'], name='submit_subm_time_fcd790_idx'),
        ),
        migrations.AddField(
            model_name='submissionemailevent',
            name='in_reply_to',
            field=ietf.utils.models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='irtomanual', to='message.Message'),
        ),
        migrations.AddField(
            model_name='submissionemailevent',
            name='message',
            field=ietf.utils.models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='manualevents', to='message.Message'),
        ),
        migrations.AddIndex(
            model_name='submission',
            index=models.Index(fields=['submission_date'], name='submit_subm_submiss_8e58a9_idx'),
        ),
    ]
