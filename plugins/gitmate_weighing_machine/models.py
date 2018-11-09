from django.db import models

from gitmate_config.models import SettingsBase


class Settings(SettingsBase):
    check_issue_weight_presence = models.BooleanField(
        default=False,
        help_text='Checks for presence of a weight on newly opened issues')
    no_weight_label = models.TextField(
        default='dev/missing-weight',
        help_text='The label used to indicate that an issue was not associated'
                  'with a weight')
    check_overweight_issues = models.BooleanField(
        default=True,
        help_text='Check for issues having too much weight')
    max_issue_weight = models.IntegerField(
        default=4,
        help_text='The maximum weight that can be assigned to an issue')
    max_weight_label = models.TextField(
        default='dev/over-weight',
        help_text='The label used to indicate that an issue has too much'
                  'weight and needs to be broken down into smaller chunks')
