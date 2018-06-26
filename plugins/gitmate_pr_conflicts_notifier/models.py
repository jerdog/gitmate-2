from django.db import models

from gitmate_config.models import SettingsBase


class Settings(SettingsBase):
    conflicts_label = models.CharField(
        max_length=25,
        default='needs rebase',
        help_text='Label for pull requests that have merge conflicts.')
    conflicts_message = models.CharField(
        max_length=1500,
        default='This PR has merge conflicts, please do a manual rebase and '
                'resolve conflicts.',
        help_text='Message to be returned if there are merge conflicts in the '
                  'pull request.')
