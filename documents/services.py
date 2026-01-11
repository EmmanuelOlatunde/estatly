"""
Business logic for documents app.

All domain logic for document generation, management, and download tracking.
"""

import logging
from typing import Optional, Dict, Any
from uuid import UUID

from django.contrib.auth import get_user_model
from django.core.files.base import ContentFile
from django.db import transaction, models
from django.utils import timezone
from django.core.exceptions import ValidationError

from .models import Document, DocumentDownload, DocumentType, DocumentStatus

User = get_user_model()
logger = logging.getLogger(__name__)


def create_document(
    *,
    document_type: str,
    title: str,
    related_user,
    related_payment_id: Optional[UUID] = None,
    related_announcement_id: Optional[UUID] = None,
    metadata: Optional[Dict[str, Any]] = None,
) -> Document:
    """
    Create a new document record and initiate generation.
    
    Args:
        document_type: Type of document (payment_receipt or announcement)
        title: Document title
        related_user: User the document is for (optional)
        related_payment_id: Related payment UUID for receipts
        related_announcement_id: Related announcement UUID for announcements
        metadata: Additional metadata for document generation
    
    Returns:
        The created Document instance
    
    Raises:
        ValueError: If validation fails
    """
    logger.info(
        f"Creating document: type={document_type}, title={title}, "
        f"user={related_user.id if related_user else None}"
    )
    
    if not metadata:
        metadata = {}
    
    try:
        document = Document(
            document_type=document_type,
            title=title,
            related_user=related_user,
            related_payment_id=related_payment_id,
            related_announcement_id=related_announcement_id,
            metadata=metadata,
            status=DocumentStatus.PENDING,
        )
        document.full_clean()
        document.save()
        
        logger.info(f"Document created successfully: {document.id}")
        return document
        
    except ValidationError as e:
        logger.error(f"Document creation validation failed: {e}")
        raise ValueError(f"Document validation failed: {e}")
    except Exception as e:
        logger.error(f"Document creation failed: {e}")
        raise


def update_document(
    *,
    document: Document,
    title: Optional[str] = None,
    metadata: Optional[Dict[str, Any]] = None,
) -> Document:
    """
    Update document details.
    
    Args:
        document: Document instance to update
        title: New title (optional)
        metadata: Updated metadata (optional)
    
    Returns:
        The updated Document instance
    
    Raises:
        ValueError: If validation fails
    """
    logger.info(f"Updating document: {document.id}")
    
    try:
        if title is not None:
            document.title = title
        
        if metadata is not None:
            document.metadata = metadata
        
        document.full_clean()
        document.save(update_fields=['title', 'metadata', 'updated_at'])
        
        logger.info(f"Document updated successfully: {document.id}")
        return document
        
    except ValidationError as e:
        logger.error(f"Document update validation failed: {e}")
        raise ValueError(f"Document validation failed: {e}")
    except Exception as e:
        logger.error(f"Document update failed: {e}")
        raise


@transaction.atomic
def generate_document_pdf(
    *,
    document: Document,
    pdf_content: bytes,
    file_name: Optional[str] = None,
) -> Document:
    """
    Save generated PDF content to document.
    
    Args:
        document: Document instance to attach PDF to
        pdf_content: Raw PDF bytes
        file_name: Optional filename (auto-generated if not provided)
    
    Returns:
        The updated Document instance with attached PDF
    
    Raises:
        ValueError: If document is not in correct state
    """
    logger.info(f"Saving PDF for document: {document.id}")
    
    if document.status == DocumentStatus.COMPLETED and document.file:
        logger.warning(f"Document {document.id} already has a file")
        raise ValueError("Document already has a generated file")
    
    if not file_name:
        timestamp = timezone.now().strftime('%Y%m%d_%H%M%S')
        file_name = f"{document.document_type}_{document.id}_{timestamp}.pdf"
    
    try:
        document.status = DocumentStatus.GENERATING
        document.save(update_fields=['status', 'updated_at'])
        
        pdf_file = ContentFile(pdf_content, name=file_name)
        document.file.save(file_name, pdf_file, save=False)
        document.file_size = len(pdf_content)
        document.status = DocumentStatus.COMPLETED
        document.generated_at = timezone.now()
        document.error_message = ''
        
        document.save(update_fields=[
            'file',
            'file_size',
            'status',
            'generated_at',
            'error_message',
            'updated_at'
        ])
        
        logger.info(f"PDF saved successfully for document: {document.id}")
        return document
        
    except Exception as e:
        logger.error(f"PDF generation failed for document {document.id}: {e}")
        document.status = DocumentStatus.FAILED
        document.error_message = str(e)
        document.save(update_fields=['status', 'error_message', 'updated_at'])
        raise


def mark_document_generation_failed(
    *,
    document: Document,
    error_message: str,
) -> Document:
    """
    Mark document generation as failed.
    
    Args:
        document: Document instance
        error_message: Error description
    
    Returns:
        The updated Document instance
    """
    logger.error(f"Marking document {document.id} as failed: {error_message}")
    
    document.status = DocumentStatus.FAILED
    document.error_message = error_message
    document.save(update_fields=['status', 'error_message', 'updated_at'])
    
    return document


def regenerate_document(
    *,
    document: Document,
    force: bool = False,
    metadata: Optional[Dict[str, Any]] = None,
) -> Document:
    """
    Regenerate an existing document.
    
    Args:
        document: Document instance to regenerate
        force: Force regeneration even if document already exists
        metadata: Updated metadata for regeneration
    
    Returns:
        The updated Document instance ready for regeneration
    
    Raises:
        ValueError: If document cannot be regenerated
    """
    logger.info(f"Regenerating document: {document.id}, force={force}")
    
    if document.status == DocumentStatus.GENERATING:
        logger.warning(f"Document {document.id} is already being generated")
        raise ValueError("Document is already being generated")
    
    if not force and document.status == DocumentStatus.COMPLETED and document.file:
        logger.warning(f"Document {document.id} already exists, use force=True")
        raise ValueError("Document already exists, use force=True to regenerate")
    
    if document.file:
        document.file.delete(save=False)
    
    if metadata:
        document.metadata = metadata
    
    document.status = DocumentStatus.PENDING
    document.file_size = None
    document.generated_at = None
    document.error_message = ''
    
    document.save(update_fields=[
        'status',
        'metadata',
        'file_size',
        'generated_at',
        'error_message',
        'updated_at'
    ])
    
    logger.info(f"Document {document.id} ready for regeneration")
    return document


@transaction.atomic
def soft_delete_document(*, document: Document) -> Document:
    """
    Soft delete a document.
    
    Args:
        document: Document instance to delete
    
    Returns:
        The soft-deleted Document instance
    """
    logger.info(f"Soft deleting document: {document.id}")
    
    document.is_deleted = True
    document.deleted_at = timezone.now()
    document.save(update_fields=['is_deleted', 'deleted_at', 'updated_at'])
    
    logger.info(f"Document soft deleted: {document.id}")
    return document


def record_document_download(
    *,
    document: Document,
    user,
    ip_address: Optional[str] = None,
    user_agent: Optional[str] = None,
) -> DocumentDownload:
    """
    Record a document download event.
    
    Args:
        document: Document that was downloaded
        user: User who downloaded (optional, may be anonymous)
        ip_address: IP address of downloader
        user_agent: Browser user agent string
    
    Returns:
        The created DocumentDownload instance
    
    Raises:
        ValueError: If document is not available for download
    """
    logger.info(
        f"Recording download for document: {document.id}, "
        f"user={user.id if user else 'anonymous'}"
    )
    
    if document.status != DocumentStatus.COMPLETED:
        logger.error(f"Document {document.id} is not ready for download")
        raise ValueError("Document is not ready for download")
    
    if not document.file:
        logger.error(f"Document {document.id} has no file")
        raise ValueError("Document file is not available")
    
    if document.is_deleted:
        logger.error(f"Document {document.id} has been deleted")
        raise ValueError("Document has been deleted")
    
    try:
        download = DocumentDownload.objects.create(
            document=document,
            user=user,
            ip_address=ip_address,
            user_agent=user_agent,
        )
        
        logger.info(f"Download recorded: {download.id}")
        return download
        
    except Exception as e:
        logger.error(f"Failed to record download: {e}")
        raise


def get_user_documents(
    *,
    user,
    document_type: Optional[str] = None,
    status: Optional[str] = None,
    include_deleted: bool = False,
):
    """
    Get documents for a specific user.
    
    Args:
        user: User to get documents for
        document_type: Filter by document type (optional)
        status: Filter by status (optional)
        include_deleted: Include soft-deleted documents
    
    Returns:
        QuerySet of Document instances
    """
    logger.debug(f"Getting documents for user: {user.id}")
    
    queryset = Document.objects.filter(related_user=user)
    
    if not include_deleted:
        queryset = queryset.filter(is_deleted=False)
    
    if document_type:
        queryset = queryset.filter(document_type=document_type)
    
    if status:
        queryset = queryset.filter(status=status)
    
    return queryset.select_related('related_user')


def get_payment_receipt(
    *,
    payment_id: UUID,
    user,
) -> Optional[Document]:
    """
    Get payment receipt document by payment ID.
    
    Args:
        payment_id: UUID of the payment
        user: Optional user filter for security
    
    Returns:
        Document instance or None if not found
    """
    logger.debug(f"Getting payment receipt for payment: {payment_id}")
    
    queryset = Document.objects.filter(
        document_type=DocumentType.PAYMENT_RECEIPT,
        related_payment_id=payment_id,
        is_deleted=False,
    )
    
    if user:
        queryset = queryset.filter(related_user=user)
    
    return queryset.select_related('related_user').first()


def get_announcement_document(
    *,
    announcement_id: UUID,
) -> Optional[Document]:
    """
    Get announcement document by announcement ID.
    
    Args:
        announcement_id: UUID of the announcement
    
    Returns:
        Document instance or None if not found
    """
    logger.debug(f"Getting announcement document for: {announcement_id}")
    
    return Document.objects.filter(
        document_type=DocumentType.ANNOUNCEMENT,
        related_announcement_id=announcement_id,
        is_deleted=False,
    ).first()


def get_document_download_stats(*, document: Document) -> Dict[str, Any]:
    """
    Get download statistics for a document.
    
    Args:
        document: Document to get stats for
    
    Returns:
        Dictionary with download statistics
    """
    logger.debug(f"Getting download stats for document: {document.id}")
    
    downloads = document.downloads.all()
    
    return {
        'total_downloads': downloads.count(),
        'unique_users': downloads.values('user').distinct().count(),
        'last_downloaded': downloads.first().downloaded_at if downloads.exists() else None,
        'downloads_by_date': list(
            downloads.values('downloaded_at__date')
            .annotate(count=models.Count('id'))
            .order_by('-downloaded_at__date')
        ),
    }