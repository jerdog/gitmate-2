from django.db import models

from gitmate_config.models import SettingsBase


class Settings(SettingsBase):
    operating_namespace = models.TextField(
        default='dev',
        help_text='The namespace under which current scrum process resides.')
    ongoing_label = models.TextField(
        default='ongoing',
        help_text='The label which identifies a process as in progress.')
    review_label = models.TextField(
        default='code-review',
        help_text='The label which identifies the process as in code review.')
    acceptance_label = models.TextField(
        default='acceptance-QA',
        help_text=('The label which identifies the process as requiring '
                   'acceptance testing.'))
