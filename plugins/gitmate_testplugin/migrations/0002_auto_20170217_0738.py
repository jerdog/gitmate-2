# -*- coding: utf-8 -*-
# Generated by Django 1.10.5 on 2017-02-17 07:38
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('gitmate_testplugin', '0001_initial'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='settings',
            name='example_setting',
        ),
        migrations.AddField(
            model_name='settings',
            name='example_bool_setting',
            field=models.BooleanField(default=True, help_text='An example Bool setting'),
        ),
        migrations.AddField(
            model_name='settings',
            name='example_char_setting',
            field=models.CharField(default='example', help_text='An example Char setting', max_length=25),
        ),
    ]