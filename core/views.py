
# core/views.py
"""
API views for core app.
Provides base viewsets and mixins for other apps.
"""

import logging
from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters

from .permissions import IsEstateManagerOrSuperAdmin
from . import services

logger = logging.getLogger(__name__)


class EstateContextMixin:
    """
    Mixin to automatically filter querysets by user's estate context.
    """
    
    def get_queryset(self):
        """Filter queryset to user's estate."""
        queryset = super().get_queryset()
        return services.enforce_estate_context(queryset, self.request.user)
    
    def perform_create(self, serializer):
        """Automatically set estate on creation."""
        if not self.request.user.is_superuser:
            estate = services.get_user_estate(self.request.user)
            serializer.save(estate=estate)
        else:
            serializer.save()


class BaseEstateViewSet(EstateContextMixin, viewsets.ModelViewSet):
    """
    Base ViewSet for estate-scoped resources.
    Automatically handles estate filtering and permissions.
    """
    
    permission_classes = [IsAuthenticated, IsEstateManagerOrSuperAdmin]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]


