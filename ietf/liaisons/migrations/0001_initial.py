# Copyright The IETF Trust 2018-2020, All Rights Reserved
# Generated by Django 1.11.10 on 2018-02-20 10:52


from django.db import migrations, models
import django.db.models.deletion
import ietf.utils.models


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
            name='LiaisonStatement',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=255)),
                ('to_contacts', models.CharField(help_text='Contacts at recipient group', max_length=2000)),
                ('response_contacts', models.CharField(blank=True, help_text='Where to send a response', max_length=255)),
                ('technical_contacts', models.CharField(blank=True, help_text='Who to contact for clarification', max_length=255)),
                ('action_holder_contacts', models.CharField(blank=True, help_text='Who makes sure action is completed', max_length=255)),
                ('cc_contacts', models.TextField(blank=True)),
                ('deadline', models.DateField(blank=True, null=True)),
                ('other_identifiers', models.TextField(blank=True, null=True)),
                ('body', models.TextField(blank=True)),
            ],
        ),
        migrations.CreateModel(
            name='LiaisonStatementAttachment',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('removed', models.BooleanField(default=False)),
                ('document', ietf.utils.models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='doc.Document')),
                ('statement', ietf.utils.models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='liaisons.LiaisonStatement')),
            ],
        ),
        migrations.CreateModel(
            name='LiaisonStatementEvent',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('time', models.DateTimeField(auto_now_add=True)),
                ('desc', models.TextField()),
                ('by', ietf.utils.models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='person.Person')),
                ('statement', ietf.utils.models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='liaisons.LiaisonStatement')),
                ('type', ietf.utils.models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='name.LiaisonStatementEventTypeName')),
            ],
            options={
                'ordering': ['-time', '-id'],
            },
        ),
        migrations.CreateModel(
            name='LiaisonStatementGroupContacts',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('contacts', models.CharField(blank=True, max_length=255)),
                ('cc_contacts', models.CharField(blank=True, max_length=255)),
                ('group', ietf.utils.models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='group.Group', unique=True)),
            ],
        ),
        migrations.CreateModel(
            name='RelatedLiaisonStatement',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('relationship', ietf.utils.models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='name.DocRelationshipName')),
                ('source', ietf.utils.models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='source_of_set', to='liaisons.LiaisonStatement')),
                ('target', ietf.utils.models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='target_of_set', to='liaisons.LiaisonStatement')),
            ],
        ),
        migrations.AddField(
            model_name='liaisonstatement',
            name='attachments',
            field=models.ManyToManyField(blank=True, through='liaisons.LiaisonStatementAttachment', to='doc.Document'),
        ),
        migrations.AddField(
            model_name='liaisonstatement',
            name='from_contact',
            field=ietf.utils.models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='person.Email'),
        ),
        migrations.AddField(
            model_name='liaisonstatement',
            name='from_groups',
            field=models.ManyToManyField(blank=True, related_name='liaisonstatement_from_set', to='group.Group'),
        ),
        migrations.AddField(
            model_name='liaisonstatement',
            name='purpose',
            field=ietf.utils.models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='name.LiaisonStatementPurposeName'),
        ),
        migrations.AddField(
            model_name='liaisonstatement',
            name='state',
            field=ietf.utils.models.ForeignKey(default='pending', on_delete=django.db.models.deletion.CASCADE, to='name.LiaisonStatementState'),
        ),
        migrations.AddField(
            model_name='liaisonstatement',
            name='tags',
            field=models.ManyToManyField(blank=True, to='name.LiaisonStatementTagName'),
        ),
        migrations.AddField(
            model_name='liaisonstatement',
            name='to_groups',
            field=models.ManyToManyField(blank=True, related_name='liaisonstatement_to_set', to='group.Group'),
        ),
    ]
