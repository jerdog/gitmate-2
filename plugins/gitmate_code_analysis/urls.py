from django.urls import path

from .views import get_analysis_result


urlpatterns = [
    path('results/', get_analysis_result, name='result')
]
