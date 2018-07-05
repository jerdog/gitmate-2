# Generated by Django 2.0.6 on 2018-06-29 15:24

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('gitmate_issue_assigner', '0002_auto_20171205_2009'),
    ]

    operations = [
        migrations.AddField(
            model_name='settings',
            name='assigned_message',
            field=models.CharField(default='Sorry, but the issues {issues} are assigned to someone else. Please try working on some other issues.', help_text='Message to be returned when referenced issue is assigned to someone else, use {issues} as placeholder.', max_length=3000),
        ),
        migrations.AddField(
            model_name='settings',
            name='enable_auto_assign',
            field=models.BooleanField(default=False, help_text='Auto assign issues if they are referenced in commit message of a pull request and there is no CI failure.'),
        ),
    ]