# -*- coding: utf-8 -*-
# Generated by Django 1.11.8 on 2017-12-12 14:05
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('gitmate_rebaser', '0002_auto_20171205_2009'),
    ]

    operations = [
        migrations.AddField(
            model_name='settings',
            name='enable_fastforward',
            field=models.BooleanField(default=False, help_text='Enables fastforward or ff command.'),
        ),
        migrations.AddField(
            model_name='settings',
            name='enable_merge',
            field=models.BooleanField(default=False, help_text='Enables merge command.'),
        ),
        migrations.AddField(
            model_name='settings',
            name='enable_rebase',
            field=models.BooleanField(default=True, help_text='Enables rebase command.'),
        ),
    ]