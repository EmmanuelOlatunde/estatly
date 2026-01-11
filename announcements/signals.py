# announcements/signals.py

"""
Signal handlers for announcements app.

Handles post-save and post-delete operations for announcements.
"""

import logging
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from .models import Announcement

logger = logging.getLogger(__name__)


@receiver(post_save, sender=Announcement)
def announcement_post_save(sender, instance, created, **kwargs):
    """
    Signal handler for when an announcement is saved.
    
    Logs the creation or update of announcements.
    Can be extended to send notifications, update caches, etc.
    
    Args:
        sender: The model class (Announcement)
        instance: The actual instance being saved
        created: Boolean indicating if this is a new instance
        **kwargs: Additional keyword arguments
    """
    if created:
        logger.info(
            f"New announcement created: {instance.id} - '{instance.title}' "
            f"by user {instance.created_by.id}"
        )
    else:
        logger.info(
            f"Announcement updated: {instance.id} - '{instance.title}' "
            f"by user {instance.created_by.id}"
        )


@receiver(post_delete, sender=Announcement)
def announcement_post_delete(sender, instance, **kwargs):
    """
    Signal handler for when an announcement is deleted.
    
    Logs the deletion of announcements.
    Can be extended to clean up related data, send notifications, etc.
    
    Args:
        sender: The model class (Announcement)
        instance: The actual instance being deleted
        **kwargs: Additional keyword arguments
    """
    logger.info(
        f"Announcement deleted: {instance.id} - '{instance.title}' "
        f"(originally created by user {instance.created_by.id})"
    )