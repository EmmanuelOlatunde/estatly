# estate/signals.py
"""
Signal handlers for estate app.
"""

from django.db.models.signals import post_save, pre_delete
from django.dispatch import receiver
import logging

from .models import Estate

logger = logging.getLogger(__name__)


@receiver(post_save, sender=Estate)
def estate_post_save(sender, instance, created, **kwargs):
    """
    Handle post-save operations for Estate model.
    
    Args:
        sender: The model class
        instance: The Estate instance being saved
        created: Boolean indicating if this is a new instance
        **kwargs: Additional keyword arguments
    """
    if created:
        logger.info(
            f"New estate created: {instance.name} (ID: {instance.id})"
        )
    else:
        logger.info(
            f"Estate updated: {instance.name} (ID: {instance.id})"
        )


@receiver(pre_delete, sender=Estate)
def estate_pre_delete(sender, instance, **kwargs):
    """
    Handle pre-delete operations for Estate model.
    
    Args:
        sender: The model class
        instance: The Estate instance being deleted
        **kwargs: Additional keyword arguments
    """
    logger.warning(
        f"Estate being deleted: {instance.name} (ID: {instance.id})"
    )

    # Additional cleanup logic can be added here