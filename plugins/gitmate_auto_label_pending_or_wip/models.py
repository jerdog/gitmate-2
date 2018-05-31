from django.db import models

from gitmate_config.models import SettingsBase


class Settings(SettingsBase):
    wip_label = models.CharField(
        max_length=25,
        default='process/WIP',
        help_text='Label for pull requests that are work in progress')
    pending_review_label = models.CharField(
        max_length=25,
        default='process/pending_review',
        help_text='Label for pull requests that need review')
    enable_fixes_vs_closes = models.BooleanField(
        default=False,
        help_text='Check usage of <tt>fixes</tt> and <tt>closes</tt> keywords '
                  'in a commit message.')
    bug_label = models.CharField(
        max_length=25,
        default='type/bug',
        help_text='Label for issues describing a bug')
    no_bug_label_message = models.CharField(
        max_length=1500,
        default=("`Fixes` is used but referenced issue doesn't have a bug "
                 'label, if issue is updated to include the bug label then ask'
                 ' a maintainer to add bug label else use `Closes`.'),
        help_text=('Message to be returned when Fixes is used but there is no '
                   'bug label on the issue(GitHub/GitLab Markdown supported)'))
    bug_label_message = models.CharField(
        max_length=1500,
        default=('`Closes` is used but issue has a bug label, '
                 'if issue is updated to remove the bug label then ask a '
                 'maintainer to remove bug label else use `Fixes`.'),
        help_text=('Message to be returned when Closes is used but there is '
                   'bug label on the issue(GitHub/GitLab Markdown supported)'))
