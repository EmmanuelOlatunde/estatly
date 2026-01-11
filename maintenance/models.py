# maintenance/models.py

"""
Models for the maintenance app.

Defines the MaintenanceTicket model for tracking estate issues.
"""

import uuid
import logging
from django.db import models
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError

User = get_user_model()
logger = logging.getLogger(__name__)


class MaintenanceTicket(models.Model):
    """
    Represents a maintenance or issue ticket for an estate.
    
    Tracks problems reported within an estate such as water, electricity,
    security, waste management, and other maintenance concerns. Tickets can
    be created by estate managers on behalf of residents.
    """
    
    class CategoryChoices(models.TextChoices):
        """Available categories for maintenance tickets."""
        WATER = 'WATER', 'Water'
        ELECTRICITY = 'ELECTRICITY', 'Electricity'
        SECURITY = 'SECURITY', 'Security'
        WASTE = 'WASTE', 'Waste'
        OTHER = 'OTHER', 'Other'
    
    class StatusChoices(models.TextChoices):
        """Status options for maintenance tickets."""
        OPEN = 'OPEN', 'Open'
        RESOLVED = 'RESOLVED', 'Resolved'
    
    # Primary key
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False
    )
    
    # Basic ticket information
    title = models.CharField(
        max_length=255,
        help_text='Brief title describing the issue'
    )
    
    description = models.TextField(
        help_text='Detailed description of the maintenance issue'
    )
    
    category = models.CharField(
        max_length=20,
        choices=CategoryChoices.choices,
        default=CategoryChoices.OTHER,
        db_index=True,
        help_text='Category of the maintenance issue'
    )
    
    status = models.CharField(
        max_length=20,
        choices=StatusChoices.choices,
        default=StatusChoices.OPEN,
        db_index=True,
        help_text='Current status of the ticket'
    )
    
    # Relationships
    created_by = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        related_name='created_maintenance_tickets',
        help_text='Estate manager who created this ticket'
    )
    
    # Relationships
    unit = models.ForeignKey(
        'units.Unit',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='maintenance_tickets',
        help_text='Optional unit associated with this issue'
    )
    
    estate = models.ForeignKey(
        'estates.Estate',
        on_delete=models.PROTECT,
        related_name='maintenance_tickets',
        help_text='Estate where this issue is located'
    )
    
    # Timestamps
    created_at = models.DateTimeField(
        auto_now_add=True,
        db_index=True
    )
    
    updated_at = models.DateTimeField(
        auto_now=True
    )
    
    resolved_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text='Timestamp when ticket was resolved'
    )
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Maintenance Ticket'
        verbose_name_plural = 'Maintenance Tickets'
        indexes = [
            models.Index(fields=['estate', 'status']),
            models.Index(fields=['estate', 'category']),
            models.Index(fields=['created_by', 'status']),
        ]


    
    def __str__(self):
        return f"{self.title} ({self.get_status_display()})"
    
    def clean(self):
        """
        Model-level validation.
        
        Validates:
        - If unit is provided, it must belong to the associated estate
        - Title must not be empty or only whitespace
        
        Raises:
            ValidationError: If validation fails
        """
        super().clean()
        
        errors = {}
        
        # Validate title is not empty or whitespace
        if self.title and not self.title.strip():
            errors['title'] = 'Title cannot be empty or only whitespace'
        
        # Validate unit belongs to estate if both are provided
        if self.unit and self.estate:
            if self.unit.estate_id != self.estate_id:
                errors['unit'] = 'Unit must belong to the specified estate'
        
        if errors:
            logger.warning(
                f"Validation failed for MaintenanceTicket: {errors}"
            )
            raise ValidationError(errors)
    
    def save(self, *args, **kwargs):
        """
        Override save to run full_clean for validation.
        """
        self.full_clean()
        super().save(*args, **kwargs)
        logger.info(
            f"MaintenanceTicket {self.id} saved with status {self.status}"
        )