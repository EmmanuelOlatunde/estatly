"""
URL routing for documents app.
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

app_name = 'documents'

router = DefaultRouter()
router.register(r'documents', views.DocumentViewSet, basename='document')
router.register(r'downloads', views.DocumentDownloadViewSet, basename='document-download')

urlpatterns = [
    path('', include(router.urls)),
]