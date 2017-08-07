# -*- coding: utf-8 -*-
# Generated by Django 1.11.2 on 2017-08-07 16:53
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('gitmate_approver', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='settings',
            name='status_labels',
            field=models.CharField(default='process/pending_review, process/WIP', help_text='Comma seperated labels to be removed from the merge request once it has been approved. e.g. process/WIP, status/stale, process/pending_review', max_length=500),
        ),
    ]
