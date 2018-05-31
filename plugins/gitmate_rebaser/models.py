from django.db import models

from gitmate_config.models import SettingsBase


class Settings(SettingsBase):
    enable_rebase = models.BooleanField(
        default=True,
        help_text='Rebase on default branch (git rebase).')
    enable_merge = models.BooleanField(
        default=False,
        help_text='Merge to default branch (git merge --no-ff).')
    enable_squash = models.BooleanField(
        default=False,
        help_text='Squash commits in source branch.')
    merge_admin_only = models.BooleanField(
        default=False,
        help_text='Only admins can merge if set to True, else anyone with '
                  'write access can')
    enable_fastforward = models.BooleanField(
        default=False,
        help_text='Fast forward default branch (git merge --ff-only)')
    fastforward_admin_only = models.BooleanField(
        default=False,
        help_text='Only admins can fastforward if set to True, else anyone '
                  'with write access can')
    squash_admin_only = models.BooleanField(
        default=False,
        help_text='Only admins can squash if set to True, else anyone with '
                  'write access can')
