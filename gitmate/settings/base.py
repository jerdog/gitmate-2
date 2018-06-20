import os
import logging

from IGitt.GitHub import GitHubJsonWebToken

from gitmate import RANDOM_PRIVATE_KEY
from gitmate_config.enums import TaskQueue


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/stable/howto/deployment/checklist/

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Debugging and testing configuration
DEBUG = True
CELERY_ALWAYS_EAGER = True
CELERY_EAGER_PROPAGATES_EXCEPTIONS = True

# Disable logging backoff exceptions from IGitt to sentry cloud and instead
# stream them to the console.
logging.getLogger('backoff').setLevel(logging.INFO)

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = 's#x)wcdigpbgi=7nxrbqbd&$yri@2k9bs%v@*szo#&)c=qp+3-'

# Python Social Auth Configuration
# See http://python-social-auth-docs.readthedocs.io/en/latest/configuration/settings.html

SOCIAL_AUTH_URL_NAMESPACE = 'auth'
SOCIAL_AUTH_LOGIN_REDIRECT_URL = 'http://localhost:4200/repositories'
SOCIAL_AUTH_LOGOUT_REDIRECT_URL = 'http://localhost:4200'
SOCIAL_AUTH_LOGIN_URL = '/login'
SOCIAL_AUTH_PIPELINE = (
    # Get the information we can about the user and return it in a simple
    # format to create the user instance later. On some cases the details are
    # already part of the auth response from the provider, but sometimes this
    # could hit a provider API.
    'social.pipeline.social_auth.social_details',

    # Get the social uid from whichever service we're authing thru. The uid is
    # the unique identifier of the given user in the provider.
    'social.pipeline.social_auth.social_uid',

    # Verifies that the current auth process is valid within the current
    # project, this is were emails and domains whitelists are applied (if
    # defined).
    'social.pipeline.social_auth.auth_allowed',

    # Checks if the current social-account is already associated in the site.
    'social.pipeline.social_auth.social_user',

    # Make up a username for this person, appends a random string at the end if
    # there's any collision.
    'social.pipeline.user.get_username',

    # Send a validation email to the user to verify its email address.
    # Disabled by default.
    # 'social.pipeline.mail.mail_validation',

    # Associates the current social details with another user account with
    # a similar email address. Disabled by default.
    'social.pipeline.social_auth.associate_by_email',

    # Create a user account if we haven't found one yet.
    'social.pipeline.user.create_user',

    # Create the record that associated the social account with this user.
    'social.pipeline.social_auth.associate_user',

    # Populate the extra_data field in the social record with the values
    # specified by settings (and the default ones like access_token, etc).
    'social.pipeline.social_auth.load_extra_data',

    # Update the user record with any changed info from the auth service.
    'social.pipeline.user.user_details',

    # Connect the user with his/her Installation objects.
    'gitmate.pipelines.populate_repositories',
)

WEBHOOK_SECRET = 'foobar'
SOCIAL_AUTH_GITHUB_APP_KEY = None
SOCIAL_AUTH_GITHUB_APP_SECRET = None
SOCIAL_AUTH_GITHUB_KEY = None
SOCIAL_AUTH_GITHUB_SECRET = None
SOCIAL_AUTH_GITHUB_SCOPE = [
    'admin:repo_hook',
    'repo',
]

SOCIAL_AUTH_GITLAB_KEY = None
SOCIAL_AUTH_GITLAB_SECRET = None
# This needs to be specified as is including full domain name and protocol.
# Be extra careful and use the same URL used while registering the application
# on GitLab. ex. example.com/auth/complete/gitlab/
SOCIAL_AUTH_GITLAB_REDIRECT_URL = None
SOCIAL_AUTH_GITLAB_SCOPE = ['api']
SOCIAL_AUTH_GITLAB_API_URL = 'https://gitlab.com'
if not SOCIAL_AUTH_GITLAB_API_URL.startswith('http'):  # pragma: no cover
    SOCIAL_AUTH_GITLAB_API_URL = 'https://' + SOCIAL_AUTH_GITLAB_API_URL
    logging.warning('Include the protocol in GL_INSTANCE_URL! Omitting it has '
                    'been deprecated.')

SOCIAL_AUTH_BITBUCKET_KEY = None
SOCIAL_AUTH_BITBUCKET_SECRET = None

# CORS and Domain Whitelisting configuration
# See https://github.com/ottoyiu/django-cors-headers#configuration

HOOK_DOMAIN = 'localhost:8000'
# Starting with Django 1.11, unit tests require specifying ALLOWED_HOSTS
ALLOWED_HOSTS = ['testing.com', 'localhost', '127.0.0.1', 'localhost:4200',
                 'coala.io', HOOK_DOMAIN]
CORS_ORIGIN_WHITELIST = ALLOWED_HOSTS
CORS_ALLOW_CREDENTIALS = True

# Installed applications
# See https://docs.djangoproject.com/en/stable/ref/settings/#installed-apps

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'social_django',
    'gitmate_config',
    'gitmate_hooks',
    'rest_framework',
    'corsheaders',
    'coala_online',
]

# Authentication Backends
# See https://docs.djangoproject.com/en/stable/ref/settings/#authentication-backends

AUTHENTICATION_BACKENDS = (
    'gitmate.backends.GitHubAppOAuth2',
    'social_core.backends.github.GithubOAuth2',
    'social_core.backends.gitlab.GitLabOAuth2',
    'social_core.backends.bitbucket.BitbucketOAuth',
    'django.contrib.auth.backends.ModelBackend'
)

# Middleware
# See https://docs.djangoproject.com/en/stable/topics/http/middleware/

MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'gitmate.disable_csrf.DisableCSRFMiddleware',
]

ROOT_URLCONF = 'gitmate.urls'

# Templates
# See https: // docs.djangoproject.com/en/stable/ref/settings/#templates

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [os.path.join(BASE_DIR, 'templates')],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'gitmate.wsgi.application'

# Django ReST Framework Configuration
# See http://www.django-rest-framework.org/api-guide/settings/

REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework.authentication.SessionAuthentication',
    )
}

# Database
# See https://docs.djangoproject.com/en/stable/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql_psycopg2',
        'NAME': 'postgres',
        'USER': 'postgres',
        'PASSWORD': 'postgres',
        'HOST': 'localhost',
        'PORT': 5432
    }
}

# Logging
# See https://docs.djangoproject.com/en/stable/ref/settings/#logging

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
    },
    'loggers': {
        '': {
            'handlers': ['console'],
            'level': 'DEBUG',
            'propagate': False
        },
    },
}

# Internationalization
# See https://docs.djangoproject.com/en/stable/topics/i18n/

LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_L10N = True
USE_TZ = True

# Static files (CSS, JavaScript, Images)
# See https://docs.djangoproject.com/en/1.9/howto/static-files/

STATIC_ROOT = os.path.join(BASE_DIR, 'static')
STATIC_URL = '/static/'
STATICFILES_DIRS = ()

# Celery Configuration
CELERY_TASK_SERIALIZER = 'pickle'
CELERY_ACCEPT_CONTENT = ['json', 'pickle', 'yaml']
BROKER_URL = 'amqp://admin:password@rabbit/'
CELERY_BROKER_POOL_LIMIT = None

# This is required for coala_online
# Otherwise it throws NotImplementedError
CELERY_RESULT_BACKEND = 'amqp'

# Setting the task timeout hard limit to one hour
CELERYD_TASK_TIME_LIMIT = 3600

# Reserve only one task at a time for a given worker
# See http://docs.celeryproject.org/en/latest/userguide/optimizing.html#reserve-one-task-at-a-time
CELERY_WORKER_PREFETCH_MULTIPLIER = 1
CELERY_TASK_ACKS_LATE = True

# Set default task queue to short
CELERY_TASK_DEFAULT_QUEUE = TaskQueue.SHORT.value

# coafile bot access tokens
GITHUB_BOT_TOKEN = None
GITLAB_BOT_TOKEN = None

# GitMate scraper access tokens
GITHUB_SCRAPER_TOKEN = None
GITLAB_SCRAPER_TOKEN = None

# GitLab Container Registry images
REGISTRY_BASE_URL = 'registry.gitlab.com/gitmate/open-source'
COALA_RESULTS_IMAGE = f'{REGISTRY_BASE_URL}/coala-incremental-results:latest'
RESULTS_BOUNCER_IMAGE = f'{REGISTRY_BASE_URL}/result-bouncer:latest'
REBASER_IMAGE = f'{REGISTRY_BASE_URL}/mr-rebaser:latest'

# Timeout for containers in seconds
CONTAINER_TIMEOUT = 60 * 10

# GitHub Application configuration
GITHUB_APP_PRIVATE_KEY = RANDOM_PRIVATE_KEY
GITHUB_APP_ID = -1
GITHUB_JWT = GitHubJsonWebToken(GITHUB_APP_PRIVATE_KEY, GITHUB_APP_ID)

# Store SVM models for labels here
GITMATE_DATA_DIR = os.path.join(BASE_DIR, 'data')
GITMATE_MODELS_DIR = os.path.join(GITMATE_DATA_DIR, 'models')
GITMATE_DUPLICATES_DIR = os.path.join(GITMATE_DATA_DIR, 'dupes')
