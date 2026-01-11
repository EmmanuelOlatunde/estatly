# payments/urls.py

"""
URL configuration for the payments app.

Registers all ViewSets with the DRF router.
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'fees', views.FeeViewSet, basename='fee')
router.register(r'assignments', views.FeeAssignmentViewSet, basename='fee-assignment')
router.register(r'payments', views.PaymentViewSet, basename='payment')
router.register(r'receipts', views.ReceiptViewSet, basename='receipt')

urlpatterns = [
    path('', include(router.urls)),
    
]