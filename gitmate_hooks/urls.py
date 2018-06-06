from django.urls import path

from .views import github_webhook_receiver
from .views import gitlab_webhook_receiver


app_name = 'gitmate_hooks'

urlpatterns = [
    path('github/', github_webhook_receiver, name='github'),
    path('gitlab/', gitlab_webhook_receiver, name='gitlab'),
]
