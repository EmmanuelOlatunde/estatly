# announcements/serializers.py

"""
Serializers for announcements app.

Handles serialization and validation of announcement data.
"""

from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import Announcement
from estates.models import Estate
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from django.contrib.auth.models import AbstractBaseUser

User = get_user_model()


class AnnouncementCreatorSerializer(serializers.ModelSerializer):
    """
    Nested serializer for announcement creator information.
    
    Provides read-only user details for announcement listings.
    """
    
    full_name = serializers.SerializerMethodField()
    
    class Meta:
        model = User
        fields = ['id', 'email', 'full_name']
        read_only_fields = ['id', 'email', 'full_name']
    
    def get_full_name(self, obj) -> str:
        """
        Get the full name of the user.
        
        Args:
            obj: User instance
            
        Returns:
            Full name or email if name not available
        """
        if hasattr(obj, 'first_name') and hasattr(obj, 'last_name'):
            full_name = f"{obj.first_name} {obj.last_name}".strip()
            return full_name if full_name else obj.email
        return obj.email


class AnnouncementSerializer(serializers.ModelSerializer):
    """
    Main serializer for reading announcement data.
    
    Includes nested creator information and computed fields.
    """
    
    created_by = AnnouncementCreatorSerializer(read_only=True)
    preview = serializers.SerializerMethodField()
    estate_name = serializers.CharField(source='estate.name', read_only=True)
    
    class Meta:
        model = Announcement
        fields = [
            'id',
            'estate',
            'estate_name',
            'title',
            'message',
            'preview',
            'created_by',
            'is_active',
            'created_at',
            'updated_at',
        ]
        read_only_fields = [
            'id',
            'created_by',
            'created_at',
            'updated_at',
        ]
    
    def get_preview(self, obj: Announcement) -> str:
        """
        Get a preview of the message (first 100 characters).
        
        Args:
            obj: Announcement instance
            
        Returns:
            Truncated message preview
        """
        if len(obj.message) <= 100:
            return obj.message
        return f"{obj.message[:97]}..."


class AnnouncementCreateSerializer(serializers.ModelSerializer):
    """
    Serializer for creating new announcements.
    """

    estate = serializers.PrimaryKeyRelatedField(
        queryset=Estate.objects.all(),
        required=True
    )
    is_active = serializers.BooleanField(
        required=False,
        default=True
    )

    class Meta:
        model = Announcement
        fields = [
            'estate',
            'title',
            'message',
            'is_active',
        ]

    def validate_estate(self, value):
        """
        Ensure non-superusers can only create for their estate.
        
        Args:
            value: Estate instance
            
        Returns:
            Validated estate
            
        Raises:
            ValidationError: If estate is invalid for this user
        """
        request = self.context.get('request')
        if request and request.user:
            if not request.user.is_superuser:
                # Check if user has an estate
                if not hasattr(request.user, 'estate') or not request.user.estate:
                    raise serializers.ValidationError(
                        "You must be assigned to an estate to create announcements"
                    )
                
                # Check if estate matches user's estate
                if value.id != request.user.estate.id:
                    raise serializers.ValidationError(
                        f"You can only create announcements for your assigned estate: {request.user.estate.name}"
                    )
        return value

    def validate_title(self, value: str) -> str:
        """
        Validate the title field.
        
        Args:
            value: Title value to validate
            
        Returns:
            Cleaned title value
            
        Raises:
            ValidationError: If title is invalid
        """
        if not value or len(value.strip()) == 0:
            raise serializers.ValidationError(
                "Title cannot be empty or contain only whitespace."
            )

        if len(value.strip()) < 3:
            raise serializers.ValidationError(
                "Title must be at least 3 characters long."
            )

        return value.strip()

    def validate_message(self, value: str) -> str:
        """
        Validate the message field.
        
        Args:
            value: Message value to validate
            
        Returns:
            Cleaned message value
            
        Raises:
            ValidationError: If message is invalid
        """
        if not value or len(value.strip()) == 0:
            raise serializers.ValidationError(
                "Message cannot be empty or contain only whitespace."
            )

        if len(value.strip()) < 10:
            raise serializers.ValidationError(
                "Message must be at least 10 characters long."
            )

        return value.strip()


class AnnouncementUpdateSerializer(serializers.ModelSerializer):
    """
    Serializer for updating existing announcements.
    
    Allows partial updates of announcement fields.
    Note: Estate cannot be changed after creation.
    """
    
    class Meta:
        model = Announcement
        fields = [
            'title',
            'message',
            'is_active',
        ]
    
    def validate_title(self, value: str) -> str:
        """
        Validate the title field.
        
        Args:
            value: Title value to validate
            
        Returns:
            Cleaned title value
            
        Raises:
            ValidationError: If title is invalid
        """
        if value is not None:
            if len(value.strip()) == 0:
                raise serializers.ValidationError(
                    "Title cannot be empty or contain only whitespace."
                )
            
            if len(value.strip()) < 3:
                raise serializers.ValidationError(
                    "Title must be at least 3 characters long."
                )
            
            return value.strip()
        return value
    
    def validate_message(self, value: str) -> str:
        """
        Validate the message field.
        
        Args:
            value: Message value to validate
            
        Returns:
            Cleaned message value
            
        Raises:
            ValidationError: If message is invalid
        """
        if value is not None:
            if len(value.strip()) == 0:
                raise serializers.ValidationError(
                    "Message cannot be empty or contain only whitespace."
                )
            
            if len(value.strip()) < 10:
                raise serializers.ValidationError(
                    "Message must be at least 10 characters long."
                )
            
            return value.strip()
        return value