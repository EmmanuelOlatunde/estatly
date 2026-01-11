
# estates/urls.py
"""
URL configuration for estates app.
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

app_name = 'estates'

router = DefaultRouter()
router.register(r'', views.EstateViewSet, basename='estates')

urlpatterns = [
    path('', include(router.urls)),
]


