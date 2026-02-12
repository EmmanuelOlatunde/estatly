# announcements/signals.py

"""
Signal handlers for announcements app.

Handles post-save and post-delete operations for announcements.
Integrates with documents app for PDF generation.
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
    Triggers PDF generation for new announcements using documents app.
    
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
        
        # Trigger PDF generation using documents app
        from documents import services as doc_services
        try:
            document = doc_services.create_document(
                document_type='announcement',
                title=f"Announcement: {instance.title}",
                related_user=instance.created_by,
                related_announcement_id=instance.id,
                metadata={
                    'announcement_title': instance.title,
                    'content': instance.message,
                    'posted_by': instance.created_by.email,
                    'posted_date': instance.created_at.strftime('%B %d, %Y at %I:%M %p'),
                    'is_active': instance.is_active,
                }
            )
            logger.info(
                f"PDF document created for announcement {instance.id}: "
                f"document_id={document.id}"
            )
        except Exception as e:
            logger.error(
                f"Failed to create PDF document for announcement {instance.id}: {e}"
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
    
    Logs the deletion and soft-deletes associated PDF document.
    
    Args:
        sender: The model class (Announcement)
        instance: The actual instance being deleted
        **kwargs: Additional keyword arguments
    """
    logger.info(
        f"Announcement deleted: {instance.id} - '{instance.title}' "
        f"(originally created by user {instance.created_by.id})"
    )
    
    # Soft delete associated document
    from documents import services as doc_services
    try:
        document = doc_services.get_announcement_document(
            announcement_id=instance.id
        )
        if document:
            doc_services.soft_delete_document(document=document)
            logger.info(
                f"Associated PDF document soft-deleted for announcement {instance.id}"
            )
    except Exception as e:
        logger.error(
            f"Failed to soft-delete document for announcement {instance.id}: {e}"
        )