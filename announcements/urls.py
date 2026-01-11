# announcements/urls.py

"""
URL configuration for announcements app.

Maps URL patterns to views using DRF routers.
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

app_name = 'announcements'

router = DefaultRouter()
router.register(r'', views.AnnouncementViewSet, basename='announcement')

urlpatterns = [
    path('', include(router.urls)),
]