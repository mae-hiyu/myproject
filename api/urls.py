# api/urls.py
from django.urls import path
from .views import get_population_data

urlpatterns = [
    path('population-data/', get_population_data, name='population_data'),
]