import os

from gitmate.settings.local import *


GITMATE_PLUGINS += ['testplugin']
INSTALLED_APPS += [
    'plugins.gitmate_testplugin.apps.GitmateTestpluginConfig'
]

GITHUB_TEST_REPO = os.environ.get('GITHUB_TEST_REPO')
GITLAB_TEST_REPO = os.environ.get('GITLAB_TEST_REPO')
GITHUB_TEST_TOKEN = os.environ.get('GITHUB_TEST_TOKEN')
GITLAB_TEST_TOKEN = os.environ.get('GITLAB_TEST_TOKEN')
GITHUB_BOT_TOKEN = 'foobar'
GITLAB_BOT_TOKEN = 'foobar'
WEBHOOK_SECRET = 'somerandomstring'

DATABASES['default']['HOST'] = 'postgres'
