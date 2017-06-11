# -*- coding: utf-8 -*-
# Generated by Django 1.11.2 on 2017-06-11 16:15
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('gitmate_config', '0008_repository_admins'),
    ]

    operations = [
        migrations.CreateModel(
            name='Settings',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('ack_strs', models.TextField(default='ack', help_text='Phrases that will be recognized as ack commands.')),
                ('unack_strs', models.TextField(default='unack', help_text='Phrases that will be recognized as unack commands.')),
                ('repo', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='gitmate_ack_repository', to='gitmate_config.Repository')),
            ],
        ),
    ]
