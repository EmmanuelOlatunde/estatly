# maintenance/serializers.py

"""
Serializers for the maintenance app.

Handles serialization and validation of maintenance ticket data.
"""

import logging
from typing import Dict, Any
from rest_framework import serializers
from django.utils import timezone
from .models import MaintenanceTicket

logger = logging.getLogger(__name__)


class MaintenanceTicketSerializer(serializers.ModelSerializer):
    """
    Serializer for reading maintenance ticket data.
    
    Includes computed fields and nested relationship data for read operations.
    """

    created_by_name = serializers.SerializerMethodField()
    identifier = serializers.SerializerMethodField()
    estate_name = serializers.SerializerMethodField()
    category_display = serializers.CharField(
        source='get_category_display',
        read_only=True
    )
    status_display = serializers.CharField(
        source='get_status_display',
        read_only=True
    )
    is_resolved = serializers.SerializerMethodField()
    days_open = serializers.SerializerMethodField()
    
    class Meta:
        model = MaintenanceTicket
        fields = [
            'id',
            'title',
            'description',
            'category',
            'category_display',
            'status',
            'status_display',
            'created_by',
            'created_by_name',
            'unit',
            'identifier',
            'estate',
            'estate_name',
            'created_at',
            'updated_at',
            'resolved_at',
            'is_resolved',
            'days_open',
        ]
        read_only_fields = [
            'id',
            'created_at',
            'updated_at',
            'resolved_at',
        ]

    def get_created_by_name(self, obj: MaintenanceTicket) -> str:
        """Get the full name of the user who created the ticket."""
        if hasattr(obj.created_by, 'get_full_name'):
            return obj.created_by.get_full_name() or obj.created_by.email
        return str(obj.created_by)
    
    def get_identifier(self, obj: MaintenanceTicket) -> str | None:
        """Get the name/number of the associated unit if exists."""
        if obj.unit:
            return getattr(obj.unit, 'unit_number', str(obj.unit))
        return None
    
    def get_estate_name(self, obj: MaintenanceTicket) -> str:
        """Get the name of the associated estate."""
        return getattr(obj.estate, 'name', str(obj.estate))
    
    def get_is_resolved(self, obj: MaintenanceTicket) -> bool:
        """Check if the ticket is resolved."""
        return obj.status == MaintenanceTicket.StatusChoices.RESOLVED
    
    def get_days_open(self, obj: MaintenanceTicket) -> int:
        """
        Calculate number of days the ticket has been/was open.
        
        For resolved tickets: days from creation to resolution
        For open tickets: days from creation (or last reopen) to now
        """
        # Use timezone-aware datetime
        now = timezone.now()
        
        if obj.status == MaintenanceTicket.StatusChoices.RESOLVED and obj.resolved_at:
            # Ticket is resolved - calculate from created_at to resolved_at
            delta = obj.resolved_at - obj.created_at
        else:
            # Ticket is still open - calculate from created_at to now
            delta = now - obj.created_at
        
        # Return total days (rounded up if there's any partial day)
        days = delta.days
        if delta.seconds > 0:
            days += 1
            
        return max(0, days)  # Ensure we never return negative days


class MaintenanceTicketCreateSerializer(serializers.ModelSerializer):
    """
    Serializer for creating maintenance tickets.
    
    Handles validation and creation logic for new tickets.
    """
    category = serializers.ChoiceField(
        choices=MaintenanceTicket.CategoryChoices.choices,
        required=True
    )
    class Meta:
        model = MaintenanceTicket
        fields = [
            'title',
            'description',
            'category',
            'estate',
            'unit',
        ]
    
    def validate_title(self, value: str) -> str:
        """
        Validate the title field.
        
        Args:
            value: The title value to validate
            
        Returns:
            The validated title
            
        Raises:
            ValidationError: If title is empty or only whitespace
        """
        if not value or not value.strip():
            logger.warning("Attempted to create ticket with empty title")
            raise serializers.ValidationError(
                "Title cannot be empty or only whitespace"
            )
        return value.strip()
    
    def validate_description(self, value: str) -> str:
        """
        Validate the description field.
        
        Args:
            value: The description value to validate
            
        Returns:
            The validated description
            
        Raises:
            ValidationError: If description is empty or only whitespace
        """
        if not value or not value.strip():
            logger.warning("Attempted to create ticket with empty description")
            raise serializers.ValidationError(
                "Description cannot be empty or only whitespace"
            )
        return value.strip()
    
    def validate(self, attrs: Dict[str, Any]) -> Dict[str, Any]:
        """
        Object-level validation.
        
        Validates:
        - If unit is provided, it must belong to the specified estate
        
        Args:
            attrs: Dictionary of field values
            
        Returns:
            Validated attributes
            
        Raises:
            ValidationError: If validation fails
        """
        unit = attrs.get('unit')
        estate = attrs.get('estate')
        
        if unit and estate:
            if unit.estate_id != estate.id:
                logger.warning(
                    f"Unit {unit.id} does not belong to estate {estate.id}"
                )
                raise serializers.ValidationError({
                    'unit': 'Unit must belong to the specified estate'
                })
        
        return attrs


class MaintenanceTicketUpdateSerializer(serializers.ModelSerializer):
    """
    Serializer for updating maintenance tickets.
    
    Allows updating specific fields while protecting others.
    """
    class Meta:
        model = MaintenanceTicket
        fields = [
            'title',
            'description',
            'category',
            'status',
            'unit',
        ]
    
    def validate_title(self, value: str) -> str:
        """Validate title is not empty or whitespace."""
        if not value or not value.strip():
            raise serializers.ValidationError(
                "Title cannot be empty or only whitespace"
            )
        return value.strip()
    
    def validate_description(self, value: str) -> str:
        """Validate description is not empty or whitespace."""
        if not value or not value.strip():
            raise serializers.ValidationError(
                "Description cannot be empty or only whitespace"
            )
        return value.strip()
    
    def validate(self, attrs: Dict[str, Any]) -> Dict[str, Any]:
        """
        Object-level validation for updates.
        
        Validates:
        - If unit is being changed, it must belong to the ticket's estate
        
        Args:
            attrs: Dictionary of field values to update
            
        Returns:
            Validated attributes
            
        Raises:
            ValidationError: If validation fails
        """
        unit = attrs.get('unit')
        
        if unit:
            estate = self.instance.estate
            if unit.estate_id != estate.id:
                logger.warning(
                    f"Attempted to assign unit {unit.id} from different estate"
                )
                raise serializers.ValidationError({
                    'unit': 'Unit must belong to the ticket\'s estate'
                })
        
        return attrs
    
    def update(self, instance: MaintenanceTicket, validated_data: Dict[str, Any]) -> MaintenanceTicket:
        """
        Update the ticket and set resolved_at timestamp if status changed to resolved.
        
        Args:
            instance: The ticket instance to update
            validated_data: Validated data to update
            
        Returns:
            Updated ticket instance
        """
        # Check if status is being changed to resolved
        new_status = validated_data.get('status')
        if (new_status == MaintenanceTicket.StatusChoices.RESOLVED and
            instance.status != MaintenanceTicket.StatusChoices.RESOLVED):
            validated_data['resolved_at'] = timezone.now()
            logger.info(f"Ticket {instance.id} marked as resolved")
        
        # Check if status is being changed from resolved to open
        if (new_status == MaintenanceTicket.StatusChoices.OPEN and
            instance.status == MaintenanceTicket.StatusChoices.RESOLVED):
            validated_data['resolved_at'] = None
            # When reopening, we update created_at to now for accurate days_open calculation
            validated_data['created_at'] = timezone.now()
            logger.info(f"Ticket {instance.id} reopened, created_at updated to {validated_data['created_at']}")
        
        return super().update(instance, validated_data)

class MaintenanceTicketListSerializer(serializers.ModelSerializer):
    """
    Lightweight serializer for listing maintenance tickets.
    
    Includes only essential fields for list views to optimize performance.
    """
    
    category_display = serializers.CharField(
        source='get_category_display',
        read_only=True
    )
    status_display = serializers.CharField(
        source='get_status_display',
        read_only=True
    )
    estate_name = serializers.CharField(
        source='estate.name',
        read_only=True
    )
    identifier = serializers.SerializerMethodField()
    is_resolved = serializers.SerializerMethodField()
    days_open = serializers.SerializerMethodField()
    created_by_name = serializers.SerializerMethodField()
    
    class Meta:
        model = MaintenanceTicket
        fields = [
            'id',
            'title',
            'description',
            'category',
            'category_display',
            'status',
            'status_display',
            'estate',
            'estate_name',
            'unit',
            'identifier',
            'created_by',
            'created_by_name',
            'is_resolved',
            'days_open',
            'created_at',
            'updated_at',
            'resolved_at',
        ]
        read_only_fields = fields
    
    def get_identifier(self, obj: MaintenanceTicket) -> str | None:
        """Get the name/number of the associated unit if exists."""
        if obj.unit:
            return getattr(obj.unit, 'unit_number', str(obj.unit))
        return None
    
    def get_is_resolved(self, obj: MaintenanceTicket) -> bool:
        """Check if the ticket is resolved."""
        return obj.status == MaintenanceTicket.StatusChoices.RESOLVED
    
    def get_days_open(self, obj: MaintenanceTicket) -> int:
        """
        Calculate number of days the ticket has been/was open.
        
        For resolved tickets: days from creation to resolution
        For open tickets: days from creation (or last reopen) to now
        """
        now = timezone.now()
        
        if obj.status == MaintenanceTicket.StatusChoices.RESOLVED and obj.resolved_at:
            delta = obj.resolved_at - obj.created_at
        else:
            delta = now - obj.created_at
        
        days = delta.days
        if delta.seconds > 0:
            days += 1
            
        return max(0, days)
    
    def get_created_by_name(self, obj: MaintenanceTicket) -> str:
        """Get the full name of the user who created the ticket."""
        if hasattr(obj.created_by, 'get_full_name'):
            return obj.created_by.get_full_name() or obj.created_by.email
        return str(obj.created_by)