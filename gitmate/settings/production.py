"""
GitMate settings for production environment, please fill in the following
details before deploying your application. For more details, please refer the
base settings file, ``gitmate/settings/base.py``.
"""
import os

from gitmate.settings import get_configuration
from gitmate.settings import get_release_version
from gitmate.settings.local import *


DEBUG = False
CONFIG = get_configuration(os.environ.get('PRODUCTION_CONFIG_PATH'))

INSTALLED_APPS += [
    'raven.contrib.django.raven_compat',
]

# OAuth credentials
SOCIAL_AUTH_GITHUB_APP_KEY = CONFIG.get('SOCIAL_AUTH_GITHUB_APP_KEY')
SOCIAL_AUTH_GITHUB_APP_SECRET = CONFIG.get('SOCIAL_AUTH_GITHUB_APP_SECRET')
SOCIAL_AUTH_GITHUB_KEY = CONFIG.get('SOCIAL_AUTH_GITHUB_KEY')
SOCIAL_AUTH_GITHUB_SECRET = CONFIG.get('SOCIAL_AUTH_GITHUB_SECRET')
SOCIAL_AUTH_GITLAB_KEY = CONFIG.get('SOCIAL_AUTH_GITLAB_KEY')
SOCIAL_AUTH_GITLAB_SECRET = CONFIG.get('SOCIAL_AUTH_GITLAB_SECRET')
SOCIAL_AUTH_GITLAB_REDIRECT_URL = CONFIG.get('SOCIAL_AUTH_GITLAB_REDIRECT_URL')

SOCIAL_AUTH_LOGIN_REDIRECT_URL = CONFIG.get(
    'SOCIAL_AUTH_REDIRECT') + '/repositories'
SOCIAL_AUTH_LOGOUT_REDIRECT_URL = CONFIG.get('SOCIAL_AUTH_REDIRECT')

# coafile bot access tokens
GITHUB_BOT_TOKEN = CONFIG.get('GITHUB_BOT_TOKEN')
GITLAB_BOT_TOKEN = CONFIG.get('GITLAB_BOT_TOKEN')

# GitMate scraper access tokens
GITHUB_SCRAPER_TOKEN = CONFIG.get('GITHUB_SCRAPER_TOKEN')
GITLAB_SCRAPER_TOKEN = CONFIG.get('GITLAB_SCRAPER_TOKEN')

# Database configuration
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql_psycopg2',
        'NAME': CONFIG.get('DB_NAME'),
        'USER': CONFIG.get('DB_USER'),
        'PASSWORD': CONFIG.get('DB_PASSWORD'),
        'HOST': CONFIG.get('DB_ADDRESS'),
        'PORT': CONFIG.get('DB_PORT')
    }
}

# Logging configuration
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,

    'formatters': {
        'console': {
            'format': '[%(asctime)s][%(levelname)s] %(name)s '
                      '%(filename)s:%(funcName)s:%(lineno)d | %(message)s',
            'datefmt': '%H:%M:%S',
        },
    },

    'handlers': {
        'console': {
            'level': 'INFO',
            'class': 'logging.StreamHandler',
            'formatter': 'console'
        },
        'sentry': {
            'level': 'WARNING',
            'class': 'raven.handlers.logging.SentryHandler',
            'dsn': RAVEN_CONFIG['dsn'],
        },
    },

    'loggers': {
        'django': {
            'handlers': ['console'],
            'level': 'DEBUG',
            'propagate': True
        },
        '': {
            'handlers': ['sentry'],
            'level': 'WARNING',
            'propogate': False
        }
    }
}

# Sentry configuration
GIT_DIR = os.path.join(BASE_DIR, '.git')
VERSION_FILE = os.path.join(BASE_DIR, '.version')
RELEASE_VERSION = get_release_version(GIT_DIR, BASE_DIR, VERSION_FILE)
RAVEN_CONFIG = {
    'dsn': CONFIG.get('RAVEN_DSN'),
    'release': RELEASE_VERSION,
}

SECRET_KEY = CONFIG.get('SECRET_KEY')
WEBHOOK_SECRET = CONFIG.get('WEBHOOK_SECRET')
HOOK_DOMAIN = CONFIG.get('HOOK_DOMAIN')
ALLOWED_HOSTS = [HOOK_DOMAIN]
CORS_ORIGIN_WHITELIST = ALLOWED_HOSTS
CORS_ALLOW_CREDENTIALS = True

try:
    GITHUB_APP_PRIVATE_KEY = open(
        CONFIG.get('GITHUB_APP_PRIVATE_KEY_PATH'), 'r').read()
    GITHUB_APP_ID = CONFIG.get('GITHUB_APP_ID')
    GITHUB_JWT = GitHubJsonWebToken(GITHUB_APP_PRIVATE_KEY, GITHUB_APP_ID)
except FileNotFoundError:
    logging.warning(
        'GitHub Application Private Key not found. You will not be able to use'
        ' GitMate as a native GitHub Application.')

GITMATE_DATA_DIR = CONFIG.get('GITMATE_DATA_DIR')
GITMATE_MODELS_DIR = CONFIG.get('GITMATE_MODELS_DIR')
GITMATE_DUPLICATES_DIR = CONFIG.get('GITMATE_DUPLICATES_DIR')
