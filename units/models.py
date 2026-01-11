"""
Models for the units app.

Defines the Unit model for managing physical property units.
"""

import uuid
from django.db import models
from estates.models import Estate
from django.contrib.auth import get_user_model
from django.core.validators import RegexValidator
from django.core.exceptions import ValidationError

User = get_user_model()


class Unit(models.Model):
    """
    Represents a physical property unit (house or flat).
    
    This is a lightweight model focusing on the physical unit itself,
    not on ownership or detailed occupancy tracking. It stores basic
    information about the unit and its current occupant if any.
    """
    
    class UnitType(models.TextChoices):
        """Types of property units."""
        HOUSE = 'HOUSE', 'House'
        FLAT = 'FLAT', 'Flat'
        APARTMENT = 'APARTMENT', 'Apartment'
        STUDIO = 'STUDIO', 'Studio'
        OTHER = 'OTHER', 'Other'
    
    # Primary identification
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False
    )
    
    # Unit identification
    identifier = models.CharField(
        max_length=100,
        help_text='Unit identifier (e.g., House 12, Flat B3, Unit 205)'
    )
    
    unit_type = models.CharField(
        max_length=20,
        choices=UnitType.choices,
        default=UnitType.FLAT,
        help_text='Type of property unit'
    )
    
    estate = models.ForeignKey(
        Estate,
        on_delete=models.CASCADE,
        related_name='units',
        help_text='Estate this unit belongs to'
    )

    # Ownership/Management
    owner = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        related_name='owned_units',
        help_text='User who owns or manages this unit'
    )
    
    # Occupant information (lightweight, optional)
    occupant_name = models.CharField(
        max_length=200,
        blank=True,
        null=True,
        help_text='Name of current occupant (free text)'
    )
    
    phone_regex = RegexValidator(
        regex=r'^\+?1?\d{9,15}$',
        message="Phone number must be entered in the format: '+999999999'. Up to 15 digits allowed."
    )
    
    occupant_phone = models.CharField(
        validators=[phone_regex],
        max_length=17,
        blank=True,
        null=True,
        help_text='Contact phone number for occupant'
    )
    
    # Additional information
    description = models.TextField(
        blank=True,
        null=True,
        help_text='Additional notes or description about the unit'
    )
    
    is_occupied = models.BooleanField(
        default=False,
        help_text='Whether the unit is currently occupied'
    )
    
    is_active = models.BooleanField(
        default=True,
        help_text='Whether the unit is active in the system'
    )
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    
    class Meta:
        ordering = ['identifier']
        verbose_name = 'Unit'
        verbose_name_plural = 'Units'
        indexes = [
            models.Index(fields=['owner', 'is_active']),
            models.Index(fields=['identifier']),
            models.Index(fields=['is_occupied']),
            models.Index(fields=['estate', 'is_active']),
            models.Index(fields=['estate', 'is_occupied']),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=['estate', 'identifier'],
                name='unique_unit_identifier_per_estate'
            )
        ]

    
    def __str__(self):
        return f"{self.get_unit_type_display()} - {self.identifier}"
    
    def clean(self):
        """
        Model-level validation.
        
        Raises:
            ValidationError: If validation fails
        """
        super().clean()
        
        # Validate occupant information consistency
        if self.occupant_name or self.occupant_phone:
            if not self.is_occupied:
                raise ValidationError(
                    'Unit must be marked as occupied if occupant information is provided.'
                )
        
        # Trim whitespace from identifier
        if self.identifier:
            self.identifier = self.identifier.strip()
    
    def save(self, *args, **kwargs):
        """Override save to call clean() before saving."""
        self.clean()
        super().save(*args, **kwargs)
    
    @property
    def has_occupant_info(self):
        """Check if unit has any occupant information."""
        return bool(self.occupant_name or self.occupant_phone)

    @property
    def unit_number(self):
        """
        Semantic alias for identifier.
        Used by serializers/tests expecting `unit_number`.
        """
        return self.identifier