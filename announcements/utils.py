# announcements/utils.py

"""
Utility functions for announcements app.
"""

import logging
from typing import Optional
from documents.models import Document

logger = logging.getLogger(__name__)


def trigger_announcement_pdf_generation(announcement):
    from documents import services as doc_services

    try:
        document = doc_services.create_document(
            document_type='announcement',
            title=f"Announcement: {announcement.title}",
            related_user=announcement.created_by,
            related_announcement_id=announcement.id,
            metadata={
                'announcement_title': announcement.title,
                'content': announcement.message,
                'posted_by': announcement.created_by.email,
                'posted_date': announcement.created_at.strftime('%B %d, %Y at %I:%M %p'),
                'is_active': announcement.is_active,
            }
        )

        # 🚀 DO NOTHING ELSE
        # Signal will generate the PDF automatically

        return document

    except Exception as e:
        logger.error(
            f"Failed to trigger PDF generation for announcement {announcement.id}: {e}"
        )
        return None

def get_announcement_pdf(announcement) -> Optional[Document]:
    """
    Get the PDF document for an announcement.
    
    Args:
        announcement: Announcement instance
    
    Returns:
        Document instance if found and ready, None otherwise
    """
    from documents import services as doc_services
    from documents.models import DocumentStatus
    
    try:
        document = doc_services.get_announcement_document(
            announcement_id=announcement.id
        )
        
        if document and document.status == DocumentStatus.COMPLETED:
            return document
        
        return None
        
    except Exception as e:
        logger.error(
            f"Failed to get PDF for announcement {announcement.id}: {e}"
        )
        return None


def regenerate_announcement_pdf(announcement, force: bool = False) -> Optional[Document]:
    """
    Regenerate PDF for an announcement.
    
    Args:
        announcement: Announcement instance
        force: Force regeneration even if PDF already exists
    
    Returns:
        Document instance if successful, None otherwise
    """
    from documents import services as doc_services
    
    try:
        # Get existing document
        document = doc_services.get_announcement_document(
            announcement_id=announcement.id
        )
        
        if not document:
            # No document exists, create new one
            return trigger_announcement_pdf_generation(announcement)
        
        # Regenerate existing document
        document = doc_services.regenerate_document(
            document=document,
            force=force,
            metadata={
                'announcement_title': announcement.title,
                'content': announcement.message,
                'posted_by': announcement.created_by.email,
                'posted_date': announcement.created_at.strftime('%B %d, %Y at %I:%M %p'),
                'is_active': announcement.is_active,
            }
        )
        
        # Trigger PDF generation
        try:
            from documents.tasks import generate_document_pdf_task
            generate_document_pdf_task.delay(str(document.id))
            logger.info(f"PDF regeneration task queued for document {document.id}")
        except ImportError:
            from documents.generators import generate_document_pdf_content
            pdf_content = generate_document_pdf_content(document)
            doc_services.generate_document_pdf(
                document=document,
                pdf_content=pdf_content
            )
            logger.info(f"PDF regenerated synchronously for document {document.id}")
        
        return document
        
    except Exception as e:
        logger.error(
            f"Failed to regenerate PDF for announcement {announcement.id}: {e}"
        )
        return None