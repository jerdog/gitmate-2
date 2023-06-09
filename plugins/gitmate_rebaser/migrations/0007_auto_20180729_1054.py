# Generated by Django 2.0.6 on 2018-07-29 10:54

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('gitmate_rebaser', '0006_auto_20180128_1250'),
    ]

    operations = [
        migrations.AddField(
            model_name='settings',
            name='enable_squash',
            field=models.BooleanField(default=False, help_text='Squash commits in source branch.'),
        ),
        migrations.AddField(
            model_name='settings',
            name='squash_admin_only',
            field=models.BooleanField(default=False, help_text='Only admins can squash if set to True, else anyone with write access can'),
        ),
    ]
