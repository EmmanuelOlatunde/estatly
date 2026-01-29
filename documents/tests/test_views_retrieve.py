# tests/test_views_retrieve.py
"""
Tests for document detail/retrieve endpoints.

Coverage:
- Authentication requirements
- Authorization (owner vs non-owner)
- 404 for non-existent resources
- Response structure
"""

import pytest
from uuid import uuid4
from django.urls import reverse
from .factories import (
    DocumentFactory,
    CompletedDocumentFactory,
    DocumentDownloadFactory,
)
from .helpers import (
    assert_document_response_structure,
    assert_download_response_structure,
)


@pytest.mark.django_db
class TestDocumentRetrieveEndpoint:
    """Test GET /documents/<id>/ endpoint."""
    
    def test_unauthenticated_user_cannot_retrieve(self, api_client, user):
        """Unauthenticated requests return 401."""
        document = DocumentFactory.create(related_user=user)
        url = reverse('documents:document-detail', args=[document.id])
        
        response = api_client.get(url)
        
        assert response.status_code == 401
    
    def test_owner_can_retrieve_own_document(self, authenticated_client, user):
        """User can retrieve their own document."""
        document = CompletedDocumentFactory.create(related_user=user)
        url = reverse('documents:document-detail', args=[document.id])
        
        response = authenticated_client.get(url)
        
        assert response.status_code == 200
        assert str(response.data['id']) == str(document.id)
        assert response.data['title'] == document.title
        assert_document_response_structure(response.data, full=True)
    
    def test_non_owner_cannot_retrieve_document(
        self, authenticated_client, other_user
    ):
        """User cannot retrieve another user's document."""
        document = DocumentFactory.create(related_user=other_user)
        url = reverse('documents:document-detail', args=[document.id])
        
        response = authenticated_client.get(url)
        
        assert response.status_code == 404
    
    def test_admin_can_retrieve_any_document(self, admin_client, other_user):
        """Admin can retrieve any user's document."""
        document = DocumentFactory.create(related_user=other_user)
        url = reverse('documents:document-detail', args=[document.id])
        
        response = admin_client.get(url)
        
        assert response.status_code == 200
        assert str(response.data['id']) == str(document.id)
    
    def test_non_existent_document_returns_404(self, authenticated_client):
        """Request for non-existent document returns 404."""
        fake_id = uuid4()
        url = reverse('documents:document-detail', args=[fake_id])
        
        response = authenticated_client.get(url)
        
        assert response.status_code == 404
    
    def test_deleted_document_returns_404(self, authenticated_client, user):
        """Soft-deleted documents return 404."""
        document = DocumentFactory.create(
            related_user=user,
            is_deleted=True
        )
        url = reverse('documents:document-detail', args=[document.id])
        
        response = authenticated_client.get(url)
        
        assert response.status_code == 404
    
    def test_response_includes_download_count(
        self, authenticated_client, user
    ):
        """Response includes computed download count."""
        document = CompletedDocumentFactory.create(related_user=user)
        DocumentDownloadFactory.create_batch(5, document=document)
        
        url = reverse('documents:document-detail', args=[document.id])
        response = authenticated_client.get(url)
        
        assert response.status_code == 200
        assert response.data['download_count'] == 5
    
    def test_response_includes_file_url(self, authenticated_client, user):
        """Response includes file URL for completed documents."""
        document = CompletedDocumentFactory.create(related_user=user)
        url = reverse('documents:document-detail', args=[document.id])
        
        response = authenticated_client.get(url)
        
        assert response.status_code == 200
        assert response.data['file_url'] is not None
        assert 'http' in response.data['file_url']
    
    def test_response_excludes_password_fields(
        self, authenticated_client, user
    ):
        """Response does not include sensitive fields."""
        document = DocumentFactory.create(related_user=user)
        url = reverse('documents:document-detail', args=[document.id])
        
        response = authenticated_client.get(url)
        
        assert response.status_code == 200
        assert 'password' not in response.data
    
    def test_jwt_authentication(self, jwt_client, user):
        """JWT authentication works for retrieve."""
        document = DocumentFactory.create(related_user=user)
        url = reverse('documents:document-detail', args=[document.id])
        
        response = jwt_client.get(url)
        
        assert response.status_code == 200


@pytest.mark.django_db
class TestDocumentDownloadRetrieveEndpoint:
    """Test GET /downloads/<id>/ endpoint."""
    
    def test_unauthenticated_user_cannot_retrieve(self, api_client, user):
        """Unauthenticated requests return 401."""
        document = CompletedDocumentFactory.create(related_user=user)
        download = DocumentDownloadFactory.create(document=document)
        url = reverse('documents:document-download-detail', args=[download.id])
        
        response = api_client.get(url)
        
        assert response.status_code == 401
    
    def test_document_owner_can_retrieve_download(
        self, authenticated_client, user
    ):
        """User can retrieve download records of their documents."""
        document = CompletedDocumentFactory.create(related_user=user)
        download = DocumentDownloadFactory.create(document=document)
        url = reverse('documents:document-download-detail', args=[download.id])
        
        response = authenticated_client.get(url)
        
        assert response.status_code == 200
        assert str(response.data['id']) == str(download.id)
        assert_download_response_structure(response.data)
    
    def test_non_owner_cannot_retrieve_download(
        self, authenticated_client, other_user
    ):
        """User cannot retrieve downloads of other users' documents."""
        document = CompletedDocumentFactory.create(related_user=other_user)
        download = DocumentDownloadFactory.create(document=document)
        url = reverse('documents:document-download-detail', args=[download.id])
        
        response = authenticated_client.get(url)
        
        assert response.status_code == 404
    
    def test_admin_can_retrieve_any_download(self, admin_client, other_user):
        """Admin can retrieve any download record."""
        document = CompletedDocumentFactory.create(related_user=other_user)
        download = DocumentDownloadFactory.create(document=document)
        url = reverse('documents:document-download-detail', args=[download.id])
        
        response = admin_client.get(url)
        
        assert response.status_code == 200
        assert str(response.data['id']) == str(download.id)
    
    def test_non_existent_download_returns_404(self, authenticated_client):
        """Request for non-existent download returns 404."""
        fake_id = uuid4()
        url = reverse('documents:document-download-detail', args=[fake_id])
        
        response = authenticated_client.get(url)
        
        assert response.status_code == 404