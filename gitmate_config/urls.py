from os import path as os_path

from django.conf import settings
from django.urls import include
from django.urls import path
from rest_framework.routers import DefaultRouter

from .views import PluginSettingsViewSet
from .views import RepositoryViewSet
from .views import UserViewSet


app_name = 'gitmate_config'

router = DefaultRouter()
router.register(r'repos', RepositoryViewSet, basename='repository')
router.register(r'plugins', PluginSettingsViewSet, basename='settings')
router.register(r'users', UserViewSet, basename='users')
urlpatterns = router.urls

plugin_routes = [
    path(f'plugin/{plugin}/', include(f'plugins.gitmate_{plugin}.urls'))
    for plugin in settings.GITMATE_PLUGINS
    if os_path.isfile(f'plugins/gitmate_{plugin}/urls.py')
]
urlpatterns.extend(plugin_routes)
