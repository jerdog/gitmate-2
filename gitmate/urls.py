"""
GitMate URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/1.9/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  url(r'^$', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  url(r'^$', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.conf.urls import url, include
    2. Add a URL to urlpatterns:  url(r'^blog/', include('blog.urls'))
"""
from django.conf import settings
from django.urls import include
from django.urls import path
from django.conf.urls.static import static
from django.contrib import admin
from django.contrib.auth.views import logout
from rest_framework.documentation import include_docs_urls

from coala_online.views import coala_online

urlpatterns = [
    path('admin/', admin.site.urls),
    path('auth/', include('social_django.urls', namespace='auth')),
    path('api/', include('gitmate_config.urls', namespace='api')),
    path('docs/', include_docs_urls(title='API Documentation')),
    path('webhooks/', include('gitmate_hooks.urls', namespace='webhooks')),
    path('logout/', logout,
         {'next_page': settings.SOCIAL_AUTH_LOGOUT_REDIRECT_URL}),
    path('coala_online/', coala_online),
] + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
