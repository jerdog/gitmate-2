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
