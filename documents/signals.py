"""
Django signals for documents app.

Handles automatic file cleanup and related operations.
"""
from django.db.models.signals import post_save, post_delete, pre_save
from django.dispatch import receiver
from .models import Document, DocumentStatus
from .generators import generate_document_pdf_content
from . import services
import logging

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





@receiver(post_save, sender=Document)
def auto_generate_pdf_on_create(sender, instance, created, **kwargs):
    """Generate PDF synchronously when document is created."""
    if created and instance.status == DocumentStatus.PENDING:
        logger.info(f"Generating PDF for document {instance.id}")
        try:
            # Generate PDF
            pdf_content = generate_document_pdf_content(instance)
            
            # Save PDF
            services.generate_document_pdf(
                document=instance,
                pdf_content=pdf_content,
            )
            logger.info(f"PDF generated for document {instance.id}")
        except Exception as e:
            logger.error(f"PDF generation failed: {e}")
            services.mark_document_generation_failed(
                document=instance,
                error_message=str(e)
            )