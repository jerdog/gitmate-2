# -*- coding: utf-8 -*-
# Generated by Django 1.11.10 on 2018-03-09 06:51
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('gitmate_config', '0022_convert_plugins_field_to_array_of_charfields'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='repository',
            name='plugins',
        ),
        migrations.RenameField(
            model_name='repository',
            old_name='temp_plugins',
            new_name='plugins',
        )
    ]