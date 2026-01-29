
# core/mixins.py
"""
Model mixins for common functionality.
"""

import uuid
from django.db import models


class UUIDMixin(models.Model):
    """Mixin to add UUID primary key to models."""
    
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False
    )
    
    class Meta:
        abstract = True


class TimestampMixin(models.Model):
    """Mixin to add timestamp fields to models."""
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        abstract = True


class EstateOwnedMixin(models.Model):
    """
    Mixin for models that belong to an estate.
    Adds estate foreign key with proper indexing.
    """
    
    estate = models.ForeignKey(
        'estates.Estate',
        on_delete=models.CASCADE,
        related_name='%(class)s_set',
        db_index=True
    )
    
    class Meta:
        abstract = True

# core/mixins.py or similar
class SwaggerSafeQuerysetMixin:
    """
    Mixin to prevent queryset evaluation during Swagger schema generation.
    """
    def get_queryset(self):
        if getattr(self, 'swagger_fake_view', False):
            # Return empty queryset during schema generation
            return self.queryset.model.objects.none()
        return super().get_queryset()