# estate/serializers.py
"""
Serializers for estate app.
"""

from rest_framework import serializers
from .models import Estate


class EstateSerializer(serializers.ModelSerializer):
    """
    Serializer for Estate model.
    
    Used for reading estate data with computed fields.
    """
    
    estate_type_display = serializers.CharField(
        source='get_estate_type_display',
        read_only=True
    )
    fee_frequency_display = serializers.CharField(
        source='get_fee_frequency_display',
        read_only=True
    )
    unit_count_display = serializers.CharField(read_only=True)
    status_display = serializers.CharField(read_only=True)
    
    class Meta:
        model = Estate
        fields = [
            'id',
            'name',
            'estate_type',
            'estate_type_display',
            'approximate_units',
            'unit_count_display',
            'fee_frequency',
            'fee_frequency_display',
            'is_active',
            'status_display',
            'description',
            'address',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class EstateCreateSerializer(serializers.ModelSerializer):
    """
    Serializer for creating Estate instances.
    
    Separates write operations with additional validation.
    """
    
    class Meta:
        model = Estate
        fields = [
            'id',
            'name',
            'estate_type',
            'approximate_units',
            'fee_frequency',
            'is_active',
            'description',
            'address',
        ]
        extra_kwargs = {
            'name': {'required': True},
            'estate_type': {'required': True},
            'fee_frequency': {'required': True},
        }
    def validate_name(self, value):
        """Validate estate name is not empty or whitespace."""
        if not value or not value.strip():
            raise serializers.ValidationError(
                "Estate name cannot be empty or contain only whitespace."
            )
        return value.strip()
    
    def validate_approximate_units(self, value):
        """Validate approximate units is positive if provided."""
        if value is not None and value < 1:
            raise serializers.ValidationError(
                "Number of units must be at least 1."
            )
        return value
    
    def validate(self, attrs):
        """Perform cross-field validation."""
        return attrs


class EstateUpdateSerializer(serializers.ModelSerializer):
    """
    Serializer for updating Estate instances.
    
    Allows partial updates with validation.
    """
    
    class Meta:
        model = Estate
        fields = [
            'id',
            'name',
            'estate_type',
            'approximate_units',
            'fee_frequency',
            'is_active',
            'description',
            'address',
        ]
    
    def validate_name(self, value):
        """Validate estate name is not empty or whitespace."""
        if not value or not value.strip():
            raise serializers.ValidationError(
                "Estate name cannot be empty or contain only whitespace."
            )
        return value.strip()
    
    def validate_approximate_units(self, value):
        """Validate approximate units is positive if provided."""
        if value is not None and value < 1:
            raise serializers.ValidationError(
                "Number of units must be at least 1."
            )
        return value


class EstateListSerializer(serializers.ModelSerializer):
    """
    Lightweight serializer for listing estates.
    
    Returns minimal fields for list views to improve performance.
    """
    
    estate_type_display = serializers.CharField(
        source='get_estate_type_display',
        read_only=True
    )
    status_display = serializers.CharField(read_only=True)
    
    class Meta:
        model = Estate
        fields = [
            'id',
            'name',
            'estate_type',
            'estate_type_display',
            'approximate_units',
            'is_active',
            'status_display',
            'created_at',
        ]
        read_only_fields = fields