"""
Django signals for documents app.

Handles automatic file cleanup and related operations.
"""

import logging
from django.db.models.signals import post_delete, pre_save
from django.dispatch import receiver
from .models import Document

logger = logging.getLogger(__name__)


@receiver(post_delete, sender=Document)
def delete_document_file(sender, instance, **kwargs):
    """
    Delete physical file when Document is deleted.
    
    Automatically removes the PDF file from storage when the document
    record is deleted from the database.
    """
    if instance.file:
        try:
            instance.file.delete(save=False)
            logger.info(f"Deleted file for document {instance.id}")
        except Exception as e:
            logger.error(f"Failed to delete file for document {instance.id}: {e}")


@receiver(pre_save, sender=Document)
def delete_old_file_on_update(sender, instance, **kwargs):
    """
    Delete old file when a new file is uploaded.
    
    If a document's file is being replaced (e.g., during regeneration),
    remove the old file to prevent orphaned files in storage.
    """
    if not instance.pk:
        return
    
    try:
        old_instance = Document.objects.get(pk=instance.pk)
        
        if old_instance.file and instance.file and old_instance.file != instance.file:
            old_instance.file.delete(save=False)
            logger.info(f"Deleted old file for document {instance.id} during update")
            
    except Document.DoesNotExist:
        pass
    except Exception as e:
        logger.error(f"Failed to delete old file for document {instance.pk}: {e}")