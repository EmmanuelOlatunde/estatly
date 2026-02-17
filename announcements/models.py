# announcements/models.py

"""
Models for announcements app.

Provides data structures for estate announcements.
"""

import uuid
from django.db import models
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError

User = get_user_model()


class Announcement(models.Model):
    """
    Represents a one-way announcement from estate managers to tenants.
    
    Announcements are structured messages that provide an alternative to
    chaotic WhatsApp group messages. Managers can create announcements
    that can be viewed, printed, or copied for distribution.
    
    IMPORTANT: Each announcement belongs to a specific estate.
    Managers can only create/view announcements for their assigned estate.
    """
    
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False
    )
    estate = models.ForeignKey(
        'estates.Estate',
        on_delete=models.CASCADE,
        related_name='announcements',
        help_text="Estate this announcement belongs to"
    )
    title = models.CharField(
        max_length=200,
        help_text="Brief, descriptive title for the announcement"
    )
    message = models.TextField(
        help_text="Full announcement content"
    )
    created_by = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        related_name='announcements',
        help_text="Manager who created this announcement"
    )
    is_active = models.BooleanField(
        default=True,
        help_text="Whether this announcement is currently active"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Announcement'
        verbose_name_plural = 'Announcements'
        indexes = [
            models.Index(fields=['-created_at']),
            models.Index(fields=['estate', '-created_at']),
            models.Index(fields=['created_by', '-created_at']),
            models.Index(fields=['is_active', '-created_at']),
            models.Index(fields=['estate', 'is_active', '-created_at']),
        ]
    
    def __str__(self) -> str:
        """Return string representation of the announcement."""
        return f"{self.title} - {self.created_at.strftime('%Y-%m-%d')}"
    
    def clean(self) -> None:
        """
        Validate announcement data.
        
        Raises:
            ValidationError: If validation fails.
        """
        super().clean()
        
        if self.title and len(self.title.strip()) == 0:
            raise ValidationError({
                'title': 'Title cannot be empty or contain only whitespace.'
            })
        
        if self.message and len(self.message.strip()) == 0:
            raise ValidationError({
                'message': 'Message cannot be empty or contain only whitespace.'
            })
        
        # Validate that estate matches creator's estate (for non-superusers)
        # Use try/except to handle case where estate hasn't been set yet
        try:
            if self.created_by and self.estate_id:  # Use estate_id instead of estate
                if not self.created_by.is_superuser:
                    if hasattr(self.created_by, 'estate') and self.created_by.estate:
                        if self.estate_id != self.created_by.estate.id:
                            raise ValidationError({
                                'estate': f'You can only create announcements for your assigned estate ({self.created_by.estate}).'
                            })
        except Exception:
            # If estate_id is not set, it will fail in the required field validation
            pass
    
    def save(self, *args, **kwargs):
        """Override save to call full_clean."""
        self.full_clean()
        super().save(*args, **kwargs)