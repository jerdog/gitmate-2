from gitmate.settings.base import *
from gitmate.utils import get_plugins
from gitmate.utils import snake_case_to_camel_case


GITMATE_PLUGINS = get_plugins()
GITMATE_PLUGINS.remove('testplugin')

INSTALLED_APPS += [
    (f'plugins.gitmate_{name}.apps.'
     f'{snake_case_to_camel_case("gitmate_"+name)}Config')
    for name in GITMATE_PLUGINS
]

SOCIAL_AUTH_GITHUB_APP_KEY = None
SOCIAL_AUTH_GITHUB_APP_SECRET = None
SOCIAL_AUTH_GITHUB_KEY = None
SOCIAL_AUTH_GITHUB_SECRET = None
SOCIAL_AUTH_GITLAB_KEY = None
SOCIAL_AUTH_GITLAB_SECRET = None
SOCIAL_AUTH_GITLAB_REDIRECT_URL = None
