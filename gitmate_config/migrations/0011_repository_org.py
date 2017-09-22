# -*- coding: utf-8 -*-
# Generated by Django 1.11.4 on 2017-09-23 08:32
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('gitmate_config', '0010_organization'),
    ]

    operations = [
        migrations.AddField(
            model_name='repository',
            name='org',
            field=models.ForeignKey(default=None, on_delete=django.db.models.deletion.CASCADE, related_name='repos', to='gitmate_config.Organization'),
        ),
    ]
