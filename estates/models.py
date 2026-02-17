# estate/models.py
"""
Models for estate app.
"""

import uuid
from django.db import models
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
from django.conf import settings


class Estate(models.Model):
    """
    Represents a real estate property or estate complex.
    
    Defines the estate context for all data in the system.
    Can be either government-owned or privately-owned.
    """
    
    class EstateType(models.TextChoices):
        """Types of estate ownership."""
        GOVERNMENT = 'GOVERNMENT', _('Government')
        PRIVATE = 'PRIVATE', _('Private')
    
    class FeeFrequency(models.TextChoices):
        """Fee payment frequency options."""
        MONTHLY = 'MONTHLY', _('Monthly')
        YEARLY = 'YEARLY', _('Yearly')
    
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False
    )
    name = models.CharField(
        max_length=255,
        help_text=_('Name of the estate')
    )
    estate_type = models.CharField(
        max_length=20,
        choices=EstateType.choices,
        default=EstateType.PRIVATE,
        help_text=_('Ownership type of the estate (informational only in MVP)')
    )
    approximate_units = models.PositiveIntegerField(
        help_text=_('Approximate number of units in the estate'),
        null=True,
        blank=True
    )
    fee_frequency = models.CharField(
        max_length=20,
        choices=FeeFrequency.choices,
        default=FeeFrequency.MONTHLY,
        help_text=_('How often estate fees are collected')
    )
    is_active = models.BooleanField(
        default=True,
        help_text=_('Whether the estate is currently active')
    )
    description = models.TextField(
        blank=True,
        null=True,
        help_text=_('Optional description of the estate')
    )
    address = models.TextField(
        blank=True,
        null=True,
        help_text=_('Physical address of the estate')
    )
    manager = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="managed_estates",
        help_text=_("Estate manager responsible for this estate"),
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = _('Estate')
        verbose_name_plural = _('Estates')
        indexes = [
            models.Index(fields=['is_active', '-created_at']),
            models.Index(fields=['estate_type']),
        ]
    
    def __str__(self):
        return self.name
    
    def clean(self):
        """Validate model fields."""
        super().clean()
        
        if self.approximate_units is not None and self.approximate_units < 1:
            raise ValidationError({
                'approximate_units': _('Number of units must be at least 1.')
            })
        
        if not self.name or not self.name.strip():
            raise ValidationError({
                'name': _('Estate name cannot be empty.')
            })
    
    def save(self, *args, **kwargs):
        """Override save to call full_clean."""
        self.full_clean()
        super().save(*args, **kwargs)
    
    @property
    def unit_count_display(self):
        """Return a friendly display of unit count."""
        if self.approximate_units:
            return f"~{self.approximate_units} units"
        return "Unit count not specified"
    
    @property
    def status_display(self):
        """Return a friendly status display."""
        return "Active" if self.is_active else "Inactive"


    @property
    def total_units(self):
        """Total units in this estate."""
        return self.units.count()

    @property
    def active_units(self):
        """Active units in this estate."""
        return self.units.filter(is_active=True).count()

    @property
    def occupied_units(self):
        """Units currently occupied."""
        return self.units.filter(is_occupied=True).count()
