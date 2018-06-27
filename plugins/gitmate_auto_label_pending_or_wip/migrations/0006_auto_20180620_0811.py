# -*- coding: utf-8 -*-
# Generated by Django 1.11.12 on 2018-06-20 08:11
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('gitmate_auto_label_pending_or_wip', '0005_auto_20171205_2009'),
    ]

    operations = [
        migrations.AddField(
            model_name='settings',
            name='bug_label',
            field=models.CharField(default='type/bug', help_text='Label for issues describing a bug', max_length=25),
        ),
        migrations.AddField(
            model_name='settings',
            name='bug_label_message',
            field=models.CharField(default='`Closes` is used but issue has a bug label, if issue is updated to remove the bug label then ask a maintainer to remove bug label else use `Fixes`.', help_text='Message to be returned when Closes is used but there is bug label on the issue(GitHub/GitLab Markdown supported)', max_length=1500),
        ),
        migrations.AddField(
            model_name='settings',
            name='enable_fixes_vs_closes',
            field=models.BooleanField(default=False, help_text='Check usage of <tt>fixes</tt> and <tt>closes</tt> keywords in a commit message.'),
        ),
        migrations.AddField(
            model_name='settings',
            name='no_bug_label_message',
            field=models.CharField(default="`Fixes` is used but referenced issue doesn't have a bug label, if issue is updated to include the bug label then ask a maintainer to add bug label else use `Closes`.", help_text='Message to be returned when Fixes is used but there is no bug label on the issue(GitHub/GitLab Markdown supported)', max_length=1500),
        ),
    ]