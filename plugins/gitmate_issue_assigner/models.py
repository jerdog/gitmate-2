from django.contrib.postgres import fields as psql_fields
from django.db import models


from gitmate_config.models import SettingsBase


class Settings(SettingsBase):
    keywords = psql_fields.JSONField(
        help_text='Comma seperated keywords (values) triggering assignees ('
                  'keys) '
                  'to be set; e.g. sils: bug, crash.',
        default={}
    )
    enable_auto_assign = models.BooleanField(
        default=False,
        help_text='Auto assign issues if they are referenced in commit message'
                  ' of a pull request and there is no CI failure.')
    assigned_message = models.CharField(
        max_length=3000,
        default=('Sorry, but the issues {issues} are assigned to someone else.'
                 ' Please try working on some other issues.'),
        help_text=('Message to be returned when referenced issue is assigned'
                   ' to someone else, use {issues} as placeholder.'))
    enable_assign_request = models.BooleanField(
        default=False,
        help_text='Assign issue if any member comments on an issue requesting'
                  ' for assignment to the issue.')
    blocked_labels = psql_fields.ArrayField(
        models.CharField(max_length=30),
        default=list,
        help_text=('Comma seperated labels of issues for which assignment'
                   'should be blocked'))
    blocked_assignees = psql_fields.ArrayField(
        models.CharField(max_length=30),
        default=list,
        help_text=('Comma seperated usernames of members for whom assignment'
                   'should be blocked'))
    label_numbers = psql_fields.JSONField(
        help_text='Max number(values) of issues with label (keys) a member can'
                  ' work on '
                  'to be set; e.g. difficulty/newcomer: 1',
        default=dict
    )
    difficulty_order = psql_fields.ArrayField(
        models.CharField(max_length=30),
        default=list,
        help_text='Comma seperated labels of issues representing order of'
                  'difficulty level of an issue in ascending order',
    )
    org_level = models.BooleanField(
        default=False,
        help_text='Consider number of issues across all repositories within '
                  'the entire organization')
