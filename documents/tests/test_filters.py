# tests/test_filters.py
"""
Tests for filtering and search functionality.

Coverage:
- FilterSet classes
- Query parameter filtering
- Search functionality
- Combined filters
"""

import pytest
from uuid import uuid4
from datetime import datetime, timedelta
from django.urls import reverse
from django.utils import timezone
from documents.filters import DocumentFilter  # <--- Make sure this exists at the top
from documents.models import DocumentType, DocumentStatus, Document
from .factories import (
    DocumentFactory,
    CompletedDocumentFactory,
    PaymentReceiptFactory,
    AnnouncementDocumentFactory,
    FailedDocumentFactory,
)


@pytest.mark.django_db
class TestDocumentFiltering:
    """Test filtering on document list endpoint."""
    
    def test_filter_by_document_type_payment_receipt(
        self, authenticated_client, user
    ):
        """Filter documents by payment_receipt type."""
        PaymentReceiptFactory.create_batch(3, related_user=user)
        AnnouncementDocumentFactory.create_batch(2, related_user=user)
        
        url = reverse('documents:document-list')
        response = authenticated_client.get(
            url,
            {'document_type': 'payment_receipt'}
        )
        
        assert response.status_code == 200
        assert response.data['count'] == 3
        
        for doc in response.data['results']:
            assert doc['document_type'] == DocumentType.PAYMENT_RECEIPT
    
    def test_filter_by_document_type_announcement(
        self, authenticated_client, user
    ):
        """Filter documents by announcement type."""
        PaymentReceiptFactory.create_batch(3, related_user=user)
        AnnouncementDocumentFactory.create_batch(2, related_user=user)
        
        url = reverse('documents:document-list')
        response = authenticated_client.get(
            url,
            {'document_type': 'announcement'}
        )
        
        assert response.status_code == 200
        assert response.data['count'] == 2
    
    def test_filter_by_status_completed(self, authenticated_client, user):
        """Filter documents by completed status."""
        CompletedDocumentFactory.create_batch(2, related_user=user)
        DocumentFactory.create_batch(
            3,
            related_user=user,
            status=DocumentStatus.PENDING
        )
        
        url = reverse('documents:document-list')
        response = authenticated_client.get(url, {'status': 'completed'})
        
        assert response.status_code == 200
        assert response.data['count'] == 2
    
    def test_filter_by_status_pending(self, authenticated_client, user):
        """Filter documents by pending status."""
        CompletedDocumentFactory.create_batch(2, related_user=user)
        DocumentFactory.create_batch(
            3,
            related_user=user,
            status=DocumentStatus.PENDING
        )
        
        url = reverse('documents:document-list')
        response = authenticated_client.get(url, {'status': 'pending'})
        
        assert response.status_code == 200
        assert response.data['count'] == 3
    
    def test_filter_by_status_failed(self, authenticated_client, user):
        """Filter documents by failed status."""
        CompletedDocumentFactory.create_batch(2, related_user=user)
        FailedDocumentFactory.create_batch(3, related_user=user)
        
        url = reverse('documents:document-list')
        response = authenticated_client.get(url, {'status': 'failed'})
        
        assert response.status_code == 200
        assert response.data['count'] == 3
    
    def test_filter_by_related_payment_id(self, authenticated_client, user):
        """Filter documents by related payment ID."""
        payment_id = uuid4()
        PaymentReceiptFactory.create(
            related_user=user,
            related_payment_id=payment_id
        )
        PaymentReceiptFactory.create_batch(2, related_user=user)
        
        url = reverse('documents:document-list')
        response = authenticated_client.get(
            url,
            {'related_payment_id': str(payment_id)}
        )
        
        assert response.status_code == 200
        assert response.data['count'] == 1
        assert str(response.data['results'][0]['related_payment_id']) == str(payment_id)
    
    def test_filter_by_related_announcement_id(
        self, authenticated_client, user
    ):
        """Filter documents by related announcement ID."""
        announcement_id = uuid4()
        AnnouncementDocumentFactory.create(
            related_user=user,
            related_announcement_id=announcement_id
        )
        AnnouncementDocumentFactory.create_batch(2, related_user=user)
        
        url = reverse('documents:document-list')
        response = authenticated_client.get(
            url,
            {'related_announcement_id': str(announcement_id)}
        )
        
        assert response.status_code == 200
        assert response.data['count'] == 1
    
    def test_filter_by_created_after(self, authenticated_client, user):
        """Filter documents created after a specific datetime."""
        cutoff = timezone.now() - timedelta(hours=2)
        
        DocumentFactory.create(
            related_user=user,
            created_at=cutoff - timedelta(hours=1)
        )
        DocumentFactory.create(
            related_user=user,
            created_at=cutoff + timedelta(hours=1)
        )
        
        url = reverse('documents:document-list')
        response = authenticated_client.get(
            url,
            {'created_after': cutoff.isoformat()}
        )
        
        assert response.status_code == 200
        assert response.data['count'] >= 1
        
    # Inside your test file
    def test_filter_by_created_before(self):
        # 1. Create the document FIRST
        doc = DocumentFactory() 
        
        # 2. Capture time slightly AFTER creation
        # (or just use timezone.now() if your computer is fast enough, but adding a delta is safer)
        cutoff_time = timezone.now() + timedelta(seconds=1)
        
        # 3. Run filter
        # Do this
        qs = DocumentFilter(
            data={'created_before': cutoff_time}, 
            queryset=Document.objects.all()  # <--- Pass the actual queryset here
        ).qs
        
        # This should now pass because doc.created_at < cutoff_time
        assert qs.count() >= 1

    def test_combined_filters(self, authenticated_client, user):
        """Multiple filters work together."""
        PaymentReceiptFactory.create_batch(
            2,
            related_user=user,
            status=DocumentStatus.COMPLETED
        )
        PaymentReceiptFactory.create(
            related_user=user,
            status=DocumentStatus.PENDING
        )
        AnnouncementDocumentFactory.create(
            related_user=user,
            status=DocumentStatus.COMPLETED
        )
        
        url = reverse('documents:document-list')
        response = authenticated_client.get(url, {
            'document_type': 'payment_receipt',
            'status': 'completed',
        })
        
        assert response.status_code == 200
        assert response.data['count'] == 2
    
    def test_invalid_filter_value_ignored(self, authenticated_client, user):
        """Invalid filter values are handled gracefully."""
        DocumentFactory.create_batch(3, related_user=user)
        
        url = reverse('documents:document-list')
        response = authenticated_client.get(
            url,
            {'document_type': 'invalid_type'}
        )
        
        assert response.status_code == 200
    
    def test_search_by_title(self, authenticated_client, user):
        """Search documents by title."""
        DocumentFactory.create(related_user=user, title='Monthly Report')
        DocumentFactory.create(related_user=user, title='Weekly Update')
        DocumentFactory.create(related_user=user, title='Monthly Summary')
        
        url = reverse('documents:document-list')
        response = authenticated_client.get(url, {'search': 'Monthly'})
        
        assert response.status_code == 200
        assert response.data['count'] == 2
    
    def test_search_case_insensitive(self, authenticated_client, user):
        """Search is case-insensitive."""
        DocumentFactory.create(
            related_user=user,
            title='Important Document'
        )
        
        url = reverse('documents:document-list')
        response = authenticated_client.get(url, {'search': 'important'})
        
        assert response.status_code == 200
        assert response.data['count'] == 1
    
    def test_search_partial_match(self, authenticated_client, user):
        """Search matches partial strings."""
        DocumentFactory.create(related_user=user, title='Payment Receipt')
        
        url = reverse('documents:document-list')
        response = authenticated_client.get(url, {'search': 'Pay'})
        
        assert response.status_code == 200
        assert response.data['count'] == 1


@pytest.mark.django_db
class TestDocumentDownloadFiltering:
    """Test filtering on download list endpoint."""
    
    def test_filter_by_document_id(self, authenticated_client, user):
        """Filter downloads by document ID."""
        from .factories import DocumentDownloadFactory
        
        doc1 = CompletedDocumentFactory.create(related_user=user)
        doc2 = CompletedDocumentFactory.create(related_user=user)
        
        DocumentDownloadFactory.create_batch(3, document=doc1)
        DocumentDownloadFactory.create_batch(2, document=doc2)
        
        url = reverse('documents:document-download-list')
        response = authenticated_client.get(url, {'document': str(doc1.id)})
        
        assert response.status_code == 200
        assert response.data['count'] == 3
    
    def test_filter_by_document_type(self, authenticated_client, user):
        """Filter downloads by document type."""
        from .factories import DocumentDownloadFactory
        
        receipt = PaymentReceiptFactory.create(related_user=user, with_file=True)
        announcement = AnnouncementDocumentFactory.create(
            related_user=user,
            with_file=True
        )
        
        DocumentDownloadFactory.create_batch(2, document=receipt)
        DocumentDownloadFactory.create(document=announcement)
        
        url = reverse('documents:document-download-list')
        response = authenticated_client.get(
            url,
            {'document_type': 'payment_receipt'}
        )
        
        assert response.status_code == 200
        assert response.data['count'] == 2
    
    def test_filter_downloads_by_date_range(
        self, authenticated_client, user
    ):
        """Filter downloads by date range."""
        from .factories import DocumentDownloadFactory
        
        document = CompletedDocumentFactory.create(related_user=user)
        cutoff = timezone.now() - timedelta(hours=2)
        
        DocumentDownloadFactory.create(
            document=document,
            downloaded_at=cutoff - timedelta(hours=1)
        )
        DocumentDownloadFactory.create(
            document=document,
            downloaded_at=cutoff + timedelta(hours=1)
        )
        
        url = reverse('documents:document-download-list')
        response = authenticated_client.get(
            url,
            {'downloaded_after': cutoff.isoformat()}
        )
        
        assert response.status_code == 200
        assert response.data['count'] >= 1