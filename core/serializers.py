
# core/serializers.py
"""
Serializers for core app.
Provides base serializers and mixins for other apps.
"""

from rest_framework import serializers


class TimestampedSerializer(serializers.Serializer):
    """Mixin to add standard timestamp fields to serializers."""
    
    created_at = serializers.DateTimeField(read_only=True)
    updated_at = serializers.DateTimeField(read_only=True)


class UUIDSerializer(serializers.Serializer):
    """Mixin to add UUID field to serializers."""
    
    id = serializers.UUIDField(read_only=True)

