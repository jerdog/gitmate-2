from django.apps import AppConfig
from django.core.cache import cache as django_cache

from IGitt.Utils import Cache


class GitmateConfigConfig(AppConfig):
    name = 'gitmate_config'
    verbose_name = 'Configuration'
    description = 'Provides a REST API for configuring GitMate.'

    def ready(self):
        # Initialise the IGitt Cache management
        Cache.use(django_cache.get, django_cache.set)
