from django.db import models
from django.contrib.postgres.fields import ArrayField

from gitmate_config.models import SettingsBase


def default_branch():
    return ['master']


class Settings(SettingsBase):
    branch_names = ArrayField(
        base_field=models.CharField(max_length=40),
        default=default_branch,
        help_text='Automatically close pull requests opened from these'
                  'specified branches of forks.')
    message = models.TextField(
        default='Open PR on a different source branch other than master.',
        help_text='Comment this message when someone open PR on'
                  'specified branch')
