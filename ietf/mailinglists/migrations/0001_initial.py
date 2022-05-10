# Copyright The IETF Trust 2018-2020, All Rights Reserved
# Generated by Django 1.11.10 on 2018-02-20 10:52


import django.core.validators
from django.db import migrations, models
import django.db.models.deletion
import ietf.utils.models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('person', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='List',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=32)),
                ('description', models.CharField(max_length=256)),
                ('advertised', models.BooleanField(default=True)),
            ],
        ),
        migrations.CreateModel(
            name='Subscribed',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('time', models.DateTimeField(auto_now_add=True)),
                ('email', models.CharField(max_length=64, validators=[django.core.validators.EmailValidator()])),
                ('lists', models.ManyToManyField(to='mailinglists.List')),
            ],
            options={
                'verbose_name_plural': 'Subscribed',
            },
        ),
        migrations.CreateModel(
            name='Whitelisted',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('time', models.DateTimeField(auto_now_add=True)),
                ('email', models.CharField(max_length=64, validators=[django.core.validators.EmailValidator()], verbose_name='Email address')),
                ('by', ietf.utils.models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='person.Person')),
            ],
            options={
                'verbose_name_plural': 'Whitelisted',
            },
        ),
    ]
