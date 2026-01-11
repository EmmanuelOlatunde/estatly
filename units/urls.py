"""
URL configuration for the units app.

Defines API endpoints for unit management.
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

app_name = 'units'

router = DefaultRouter()
router.register(r'', views.UnitViewSet, basename='unit')

urlpatterns = [
    path('', include(router.urls)),
]