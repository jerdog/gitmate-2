from django.urls import re_path

from .views import github_webhook_receiver
from .views import gitlab_webhook_receiver


app_name = 'gitmate_hooks'

urlpatterns = [
    re_path(r'github/?', github_webhook_receiver, name='github'),
    re_path(r'gitlab/?', gitlab_webhook_receiver, name='gitlab'),
]
