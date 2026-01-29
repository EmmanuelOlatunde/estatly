# tests/test_custom_actions.py
"""
Tests for custom @action decorated endpoints.

Coverage:
- download action
- regenerate action
- my_documents action
- stats action
"""

import pytest
from uuid import uuid4
from django.urls import reverse
from documents.models import DocumentStatus
from .factories import (
    DocumentFactory,
    CompletedDocumentFactory,
    FailedDocumentFactory,
    PaymentReceiptFactory,
    AnnouncementDocumentFactory,
    DocumentDownloadFactory,
)


@pytest.mark.django_db
class TestDocumentDownloadAction:
    """Test GET /documents/<id>/download/ endpoint."""
    
    def test_unauthenticated_user_cannot_download(self, api_client, user):
        """Unauthenticated requests return 401."""
        document = CompletedDocumentFactory.create(related_user=user)
        url = reverse('documents:document-download', args=[document.id])
        
        response = api_client.get(url)
        
        assert response.status_code == 401
    
    def test_owner_can_download_completed_document(
        self, authenticated_client, user
    ):
        """User can download their completed document."""
        document = CompletedDocumentFactory.create(related_user=user)
        url = reverse('documents:document-download', args=[document.id])
        
        response = authenticated_client.get(url)
        
        assert response.status_code == 200
        assert response['Content-Type'] == 'application/pdf'
        assert 'attachment' in response['Content-Disposition']
    
    def test_non_owner_cannot_download(
        self, authenticated_client, other_user
    ):
        """User cannot download another user's document."""
        document = CompletedDocumentFactory.create(related_user=other_user)
        url = reverse('documents:document-download', args=[document.id])
        
        response = authenticated_client.get(url)
        
        assert response.status_code == 404
    
    def test_admin_can_download_any_document(self, admin_client, other_user):
        """Admin can download any user's document."""
        document = CompletedDocumentFactory.create(related_user=other_user)
        url = reverse('documents:document-download', args=[document.id])
        
        response = admin_client.get(url)
        
        assert response.status_code == 200
        assert response['Content-Type'] == 'application/pdf'
    
    def test_cannot_download_pending_document(
        self, authenticated_client, user
    ):
        """Cannot download document that is still pending."""
        document = DocumentFactory.create(
            related_user=user,
            status=DocumentStatus.PENDING
        )
        url = reverse('documents:document-download', args=[document.id])
        
        response = authenticated_client.get(url)
        
        assert response.status_code == 404
        assert 'not ready' in str(response.data).lower()
    
    def test_cannot_download_generating_document(
        self, authenticated_client, user
    ):
        """Cannot download document that is being generated."""
        document = DocumentFactory.create(
            related_user=user,
            status=DocumentStatus.GENERATING
        )
        url = reverse('documents:document-download', args=[document.id])
        
        response = authenticated_client.get(url)
        
        assert response.status_code == 404
    
    def test_cannot_download_failed_document(
        self, authenticated_client, user
    ):
        """Cannot download document with failed generation."""
        document = FailedDocumentFactory.create(related_user=user)
        url = reverse('documents:document-download', args=[document.id])
        
        response = authenticated_client.get(url)
        
        assert response.status_code == 404
    
    def test_cannot_download_document_without_file(
        self, authenticated_client, user
    ):
        """Cannot download document with no file attached."""
        document = DocumentFactory.create(
            related_user=user,
            status=DocumentStatus.COMPLETED,
            file=None
        )
        url = reverse('documents:document-download', args=[document.id])
        
        response = authenticated_client.get(url)
        
        assert response.status_code == 404
    
    def test_cannot_download_deleted_document(
        self, authenticated_client, user
    ):
        """Cannot download soft-deleted documents."""
        document = CompletedDocumentFactory.create(
            related_user=user,
            is_deleted=True
        )
        url = reverse('documents:document-download', args=[document.id])
        
        response = authenticated_client.get(url)
        
        assert response.status_code == 404
    
    def test_download_creates_download_record(
        self, authenticated_client, user
    ):
        """Downloading creates a DocumentDownload record."""
        document = CompletedDocumentFactory.create(related_user=user)
        initial_count = document.downloads.count()
        
        url = reverse('documents:document-download', args=[document.id])
        response = authenticated_client.get(url)
        
        assert response.status_code == 200
        assert document.downloads.count() == initial_count + 1
        
        download = document.downloads.latest('downloaded_at')
        assert download.user == user
        assert download.ip_address is not None
    
    def test_multiple_downloads_create_multiple_records(
        self, authenticated_client, user
    ):
        """Each download creates a new record."""
        document = CompletedDocumentFactory.create(related_user=user)
        url = reverse('documents:document-download', args=[document.id])
        
        authenticated_client.get(url)
        authenticated_client.get(url)
        authenticated_client.get(url)
        
        assert document.downloads.count() == 3


@pytest.mark.django_db
class TestDocumentRegenerateAction:
    """Test POST /documents/<id>/regenerate/ endpoint."""
    
    def test_unauthenticated_user_cannot_regenerate(self, api_client, user):
        """Unauthenticated requests return 401."""
        document = CompletedDocumentFactory.create(related_user=user)
        url = reverse('documents:document-regenerate', args=[document.id])
        
        response = api_client.post(url, {}, format='json')
        
        assert response.status_code == 401
    
    def test_owner_can_regenerate_with_force(
        self, authenticated_client, user
    ):
        """User can regenerate their document with force=True."""
        document = CompletedDocumentFactory.create(related_user=user)
        url = reverse('documents:document-regenerate', args=[document.id])
        data = {'force': True}
        
        response = authenticated_client.post(url, data, format='json')
        
        assert response.status_code == 200
        assert response.data['status'] == DocumentStatus.PENDING
        
        document.refresh_from_db()
        assert document.status == DocumentStatus.PENDING
        assert not document.file
    
    def test_regenerate_without_force_on_completed_fails(
        self, authenticated_client, user
    ):
        """Regenerating completed document without force fails."""
        document = CompletedDocumentFactory.create(related_user=user)
        url = reverse('documents:document-regenerate', args=[document.id])
        data = {'force': False}
        
        response = authenticated_client.post(url, data, format='json')
        
        assert response.status_code == 400
        assert 'already exists' in str(response.data).lower()
    
    def test_regenerate_failed_document(self, authenticated_client, user):
        """Failed document can be regenerated without force."""
        document = FailedDocumentFactory.create(related_user=user)
        url = reverse('documents:document-regenerate', args=[document.id])
        data = {}
        
        response = authenticated_client.post(url, data, format='json')
        
        assert response.status_code == 200
        
        document.refresh_from_db()
        assert document.status == DocumentStatus.PENDING
        assert document.error_message == ''
    
    def test_regenerate_with_updated_metadata(
        self, authenticated_client, user
    ):
        """Metadata can be updated during regeneration."""
        document = FailedDocumentFactory.create(
            related_user=user,
            metadata={'old': 'value'}
        )
        url = reverse('documents:document-regenerate', args=[document.id])
        data = {
            'force': True,
            'metadata': {'new': 'value', 'updated': True}
        }
        
        response = authenticated_client.post(url, data, format='json')
        
        assert response.status_code == 200
        
        document.refresh_from_db()
        assert document.metadata == {'new': 'value', 'updated': True}
    
    def test_cannot_regenerate_generating_document(
        self, authenticated_client, user
    ):
        """Cannot regenerate document that is being generated."""
        document = DocumentFactory.create(
            related_user=user,
            status=DocumentStatus.GENERATING
        )
        url = reverse('documents:document-regenerate', args=[document.id])
        data = {'force': True}
        
        response = authenticated_client.post(url, data, format='json')
        
        assert response.status_code == 400
        assert 'already being generated' in str(response.data).lower()
    
    def test_non_owner_cannot_regenerate(
        self, authenticated_client, other_user
    ):
        """User cannot regenerate another user's document."""
        document = FailedDocumentFactory.create(related_user=other_user)
        url = reverse('documents:document-regenerate', args=[document.id])
        data = {'force': True}
        
        response = authenticated_client.post(url, data, format='json')
        
        assert response.status_code == 404
    
    def test_admin_can_regenerate_any_document(
        self, admin_client, other_user
    ):
        """Admin can regenerate any user's document."""
        document = FailedDocumentFactory.create(related_user=other_user)
        url = reverse('documents:document-regenerate', args=[document.id])
        data = {'force': True}
        
        response = admin_client.post(url, data, format='json')
        
        assert response.status_code == 200


@pytest.mark.django_db
class TestMyDocumentsAction:
    """Test GET /documents/my_documents/ endpoint."""
    
    def test_unauthenticated_user_cannot_access(self, api_client):
        """Unauthenticated requests return 401."""
        url = reverse('documents:document-my-documents')
        
        response = api_client.get(url)
        
        assert response.status_code == 401
    
    def test_returns_only_users_documents(
        self, authenticated_client, user, other_user
    ):
        """Returns only current user's documents."""
        DocumentFactory.create_batch(3, related_user=user)
        DocumentFactory.create_batch(2, related_user=other_user)
        
        url = reverse('documents:document-my-documents')
        response = authenticated_client.get(url)
        
        assert response.status_code == 200
        assert response.data['count'] == 3
    
    def test_filter_by_document_type(self, authenticated_client, user):
        """Can filter by document type."""
        PaymentReceiptFactory.create_batch(2, related_user=user)
        AnnouncementDocumentFactory.create_batch(3, related_user=user)
        
        url = reverse('documents:document-my-documents')
        response = authenticated_client.get(
            url,
            {'document_type': 'payment_receipt'}
        )
        
        assert response.status_code == 200
        assert response.data['count'] == 2
    
    def test_filter_by_status(self, authenticated_client, user):
        """Can filter by status."""
        CompletedDocumentFactory.create_batch(2, related_user=user)
        DocumentFactory.create_batch(
            3,
            related_user=user,
            status=DocumentStatus.PENDING
        )
        
        url = reverse('documents:document-my-documents')
        response = authenticated_client.get(url, {'status': 'completed'})
        
        assert response.status_code == 200
        assert response.data['count'] == 2
    
    def test_paginated_results(self, authenticated_client, user):
        """Results are paginated."""
        DocumentFactory.create_batch(25, related_user=user)
        
        url = reverse('documents:document-my-documents')
        response = authenticated_client.get(url)
        
        assert response.status_code == 200
        assert 'count' in response.data
        assert 'next' in response.data
        assert 'results' in response.data
        assert len(response.data['results']) == 20
    
    def test_excludes_deleted_documents(self, authenticated_client, user):
        """Deleted documents are excluded."""
        DocumentFactory.create_batch(2, related_user=user)
        DocumentFactory.create(related_user=user, is_deleted=True)
        
        url = reverse('documents:document-my-documents')
        response = authenticated_client.get(url)
        
        assert response.status_code == 200
        assert response.data['count'] == 2


@pytest.mark.django_db
class TestDocumentStatsAction:
    """Test GET /documents/<id>/stats/ endpoint."""
    
    def test_unauthenticated_user_cannot_access(self, api_client, user):
        """Unauthenticated requests return 401."""
        document = CompletedDocumentFactory.create(related_user=user)
        url = reverse('documents:document-stats', args=[document.id])
        
        response = api_client.get(url)
        
        assert response.status_code == 401
    
    def test_owner_can_view_stats(self, authenticated_client, user):
        """User can view stats for their document."""
        document = CompletedDocumentFactory.create(related_user=user)
        DocumentDownloadFactory.create_batch(5, document=document)
        
        url = reverse('documents:document-stats', args=[document.id])
        response = authenticated_client.get(url)
        
        assert response.status_code == 200
        assert 'total_downloads' in response.data
        assert response.data['total_downloads'] == 5
        assert 'unique_users' in response.data
        assert 'last_downloaded' in response.data
    
    def test_non_owner_cannot_view_stats(
        self, authenticated_client, other_user
    ):
        """User cannot view stats of another user's document."""
        document = CompletedDocumentFactory.create(related_user=other_user)
        url = reverse('documents:document-stats', args=[document.id])
        
        response = authenticated_client.get(url)
        
        assert response.status_code == 404
    
    def test_admin_can_view_any_stats(self, admin_client, other_user):
        """Admin can view stats for any document."""
        document = CompletedDocumentFactory.create(related_user=other_user)
        DocumentDownloadFactory.create_batch(3, document=document)
        
        url = reverse('documents:document-stats', args=[document.id])
        response = admin_client.get(url)
        
        assert response.status_code == 200
        assert response.data['total_downloads'] == 3
    
    def test_stats_for_document_with_no_downloads(
        self, authenticated_client, user
    ):
        """Stats work for documents with no downloads."""
        document = CompletedDocumentFactory.create(related_user=user)
        url = reverse('documents:document-stats', args=[document.id])
        
        response = authenticated_client.get(url)
        
        assert response.status_code == 200
        assert response.data['total_downloads'] == 0
        assert response.data['unique_users'] == 0
        assert response.data['last_downloaded'] is None