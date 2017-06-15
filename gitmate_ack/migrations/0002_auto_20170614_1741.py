# -*- coding: utf-8 -*-
# Generated by Django 1.11.2 on 2017-06-14 17:41
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('gitmate_ack', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='settings',
            name='ack_strs',
            field=models.CharField(default='ack', help_text='Phrases that will be recognized as ack commands.', max_length=100),
        ),
        migrations.AlterField(
            model_name='settings',
            name='unack_strs',
            field=models.CharField(default='unack', help_text='Phrases that will be recognized as unack commands.', max_length=100),
        ),
    ]
