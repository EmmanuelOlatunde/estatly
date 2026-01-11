"""
Serializers for the units app.

Handles serialization and validation of Unit model data.
"""

from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import Unit
from estates.models import Estate
User = get_user_model()


class UnitSerializer(serializers.ModelSerializer):
    """
    Serializer for Unit model (read operations).
    
    Includes computed fields and owner information.
    """

    owner_email = serializers.EmailField(source='owner.email', read_only=True)
    has_occupant_info = serializers.BooleanField(read_only=True)
    unit_type_display = serializers.CharField(
        source='get_unit_type_display',
        read_only=True
    )
    
    class Meta:
        model = Unit
        fields = [
            'id',
            'identifier',
            'unit_type',
            'unit_type_display',
            'owner',
            'owner_email',
            'occupant_name',
            'occupant_phone',
            'description',
            'is_occupied',
            'is_active',
            'has_occupant_info',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']



class UnitListSerializer(serializers.ModelSerializer):
    """
    Lightweight serializer for listing units.
    
    Optimized for list views with minimal fields.
    """
    
    unit_type_display = serializers.CharField(
        source='get_unit_type_display',
        read_only=True
    )
    
    class Meta:
        model = Unit
        fields = [
            'id',
            
            'identifier',
            'unit_type',
            'unit_type_display',
            'occupant_name',
            'is_occupied',
            'is_active',
            'created_at',
        ]
        read_only_fields = ['id', 'created_at']

class UnitCreateSerializer(serializers.ModelSerializer):
    """
    Serializer for creating new units.
    
    Excludes owner field as it will be set from request.user.
    Estate field is required.
    """
    estate = serializers.PrimaryKeyRelatedField(
        queryset=Estate.objects.all(),
        required=True,
        help_text="The estate this unit belongs to"
    )
    unit_type = serializers.ChoiceField(
        choices=Unit.UnitType.choices,
        required=True,  # Make sure this is explicitly set
        allow_null=False
    )

    class Meta:
        model = Unit
        fields = [
            'estate',          
            'identifier',
            'unit_type',
            'occupant_name',
            'occupant_phone',
            'description',
            'is_occupied',
            'is_active',
        ]
    
    def validate_identifier(self, value):
        """
        Validate that identifier is not empty and properly formatted.
        
        Args:
            value: The identifier string to validate
            
        Returns:
            The cleaned identifier value
            
        Raises:
            ValidationError: If identifier is invalid
        """
        if not value or not value.strip():
            raise serializers.ValidationError('Identifier cannot be empty.')
        value = value.strip()
        if len(value) > 255:  # increase limit for emojis/unicode
            raise serializers.ValidationError('Identifier must be 255 characters or less.')
        return value
    
    def validate(self, data):
        """
        Cross-field validation for unit data.
        
        Args:
            data: Dictionary of validated field data
            
        Returns:
            The validated data dictionary
            
        Raises:
            ValidationError: If validation fails
        """
        is_occupied = data.get('is_occupied', False)
        occupant_name = data.get('occupant_name')
        occupant_phone = data.get('occupant_phone')
        
        # Validate occupancy consistency
        if (occupant_name or occupant_phone) and not is_occupied:
            raise serializers.ValidationError(
                'Unit must be marked as occupied if occupant information is provided.'
            )
        
        return data



class UnitUpdateSerializer(serializers.ModelSerializer):
    """
    Serializer for updating existing units.
    
    Allows partial updates and excludes owner changes.
    """
    
    class Meta:
        model = Unit
        fields = [
            'identifier',
            'unit_type',
            'occupant_name',
            'occupant_phone',
            'description',
            'is_occupied',
            'is_active',
        ]
    
    def validate_identifier(self, value):
        """
        Validate identifier for updates.
        
        Args:
            value: The identifier string to validate
            
        Returns:
            The cleaned identifier value
            
        Raises:
            ValidationError: If identifier is invalid
        """
        if not value or not value.strip():
            raise serializers.ValidationError('Identifier cannot be empty.')
        value = value.strip()
        if len(value) > 255:  # increase limit for emojis/unicode
            raise serializers.ValidationError('Identifier must be 255 characters or less.')
        return value
    
    def validate(self, data):
        """
        Cross-field validation for unit updates.
        
        Args:
            data: Dictionary of validated field data
            
        Returns:
            The validated data dictionary
            
        Raises:
            ValidationError: If validation fails
        """
        # Get current values for fields not being updated
        instance = self.instance
        is_occupied = data.get('is_occupied', instance.is_occupied)
        occupant_name = data.get('occupant_name', instance.occupant_name)
        occupant_phone = data.get('occupant_phone', instance.occupant_phone)
        
        # Validate occupancy consistency
        if (occupant_name or occupant_phone) and not is_occupied:
            raise serializers.ValidationError(
                'Unit must be marked as occupied if occupant information is provided.'
            )
        
        return data


class UnitOccupancySerializer(serializers.ModelSerializer):
    """
    Serializer for updating a Unit's occupancy status.
    Enforces occupancy consistency:
      - Cannot have occupant info if unoccupied
      - Must have at least one occupant field if occupied
    """

    occupant_name = serializers.CharField(required=False, allow_null=True, allow_blank=True)
    occupant_phone = serializers.CharField(required=False, allow_null=True, allow_blank=True)

    class Meta:
        model = Unit
        fields = ["is_occupied", "occupant_name", "occupant_phone"]

    def validate(self, attrs):
        is_occupied = attrs.get("is_occupied", getattr(self.instance, "is_occupied", False))
        
        # Only check fields explicitly provided in the request, not instance values
        name = attrs.get("occupant_name")  # ← Just get from attrs, no fallback
        phone = attrs.get("occupant_phone")  # ← Just get from attrs, no fallback

        # Only validate if user is explicitly providing occupant info in this request
        if not is_occupied and (name or phone):
            raise serializers.ValidationError(
                "Cannot provide occupant info when marking unit as unoccupied."
            )

        return attrs

    def update(self, instance, validated_data):
        # Automatically clear occupant info if marking unoccupied
        if validated_data.get("is_occupied") is False:
            validated_data["occupant_name"] = None
            validated_data["occupant_phone"] = None
        return super().update(instance, validated_data)
