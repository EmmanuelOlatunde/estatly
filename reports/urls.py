# reports/urls.py
"""
URL routing for reports app.
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter

from . import views

# Create router and register viewsets
router = DefaultRouter()
router.register(r'', views.ReportsViewSet, basename='reports')

app_name = 'reports'

urlpatterns = [
    path('', include(router.urls)),
]