# tests/test_views_delete.py
"""
Tests for document deletion endpoints.

Coverage:
- Authentication/authorization
- Soft delete behavior
- Database side effects
- Cascading effects
"""

import pytest
from uuid import uuid4
from django.urls import reverse
from documents.models import Document
from .factories import DocumentFactory, CompletedDocumentFactory


@pytest.mark.django_db
class TestDocumentDeleteEndpoint:
    """Test DELETE /documents/<id>/ endpoint."""
    
    def test_unauthenticated_user_cannot_delete(self, api_client, user):
        """Unauthenticated requests return 401."""
        document = DocumentFactory.create(related_user=user)
        url = reverse('documents:document-detail', args=[document.id])
        
        response = api_client.delete(url)
        
        assert response.status_code == 401
        assert Document.objects.filter(id=document.id).exists()
    
    def test_owner_can_delete_own_document(self, authenticated_client, user):
        """User can delete their own document."""
        document = DocumentFactory.create(related_user=user)
        url = reverse('documents:document-detail', args=[document.id])
        
        response = authenticated_client.delete(url)
        
        assert response.status_code == 204
        
        document.refresh_from_db()
        assert document.is_deleted is True
        assert document.deleted_at is not None
    
    def test_non_owner_cannot_delete_document(
        self, authenticated_client, other_user
    ):
        """User cannot delete another user's document."""
        document = DocumentFactory.create(related_user=other_user)
        url = reverse('documents:document-detail', args=[document.id])
        
        response = authenticated_client.delete(url)
        
        assert response.status_code == 404
        
        document.refresh_from_db()
        assert document.is_deleted is False
    
    def test_admin_can_delete_any_document(self, admin_client, other_user):
        """Admin can delete any user's document."""
        document = DocumentFactory.create(related_user=other_user)
        url = reverse('documents:document-detail', args=[document.id])
        
        response = admin_client.delete(url)
        
        assert response.status_code == 204
        
        document.refresh_from_db()
        assert document.is_deleted is True
    
    def test_soft_delete_preserves_data(self, authenticated_client, user):
        """Soft delete preserves document data."""
        document = CompletedDocumentFactory.create(
            related_user=user,
            title='Important Document',
            metadata={'critical': 'data'}
        )
        original_title = document.title
        original_metadata = document.metadata
        
        url = reverse('documents:document-detail', args=[document.id])
        response = authenticated_client.delete(url)
        
        assert response.status_code == 204
        
        document.refresh_from_db()
        assert document.title == original_title
        assert document.metadata == original_metadata
        assert document.file.name is not None
    
    def test_deleted_document_not_in_list(self, authenticated_client, user):
        """Deleted documents don't appear in list endpoint."""
        document = DocumentFactory.create(related_user=user)
        
        delete_url = reverse('documents:document-detail', args=[document.id])
        authenticated_client.delete(delete_url)
        
        list_url = reverse('documents:document-list')
        response = authenticated_client.get(list_url)
        
        assert response.status_code == 200
        assert response.data['count'] == 0
        assert len(response.data['results']) == 0
    
    def test_deleted_document_cannot_be_retrieved(
        self, authenticated_client, user
    ):
        """Deleted documents return 404 on retrieve."""
        document = DocumentFactory.create(related_user=user)
        url = reverse('documents:document-detail', args=[document.id])
        
        authenticated_client.delete(url)
        
        response = authenticated_client.get(url)
        assert response.status_code == 404
    
    def test_delete_non_existent_document_returns_404(
        self, authenticated_client
    ):
        """Deleting non-existent document returns 404."""
        fake_id = uuid4()
        url = reverse('documents:document-detail', args=[fake_id])
        
        response = authenticated_client.delete(url)
        
        assert response.status_code == 404
    
    def test_delete_already_deleted_document(
        self, authenticated_client, user
    ):
        """Deleting already deleted document returns 404."""
        document = DocumentFactory.create(
            related_user=user,
            is_deleted=True
        )
        url = reverse('documents:document-detail', args=[document.id])
        
        response = authenticated_client.delete(url)
        
        assert response.status_code == 404
    
    def test_response_has_no_content(self, authenticated_client, user):
        """Successful delete returns 204 with no content."""
        document = DocumentFactory.create(related_user=user)
        url = reverse('documents:document-detail', args=[document.id])
        
        response = authenticated_client.delete(url)
        
        assert response.status_code == 204
        assert not response.data
    
    def test_delete_does_not_remove_from_database(
        self, authenticated_client, user
    ):
        """Soft delete does not remove record from database."""
        document = DocumentFactory.create(related_user=user)
        document_id = document.id
        
        url = reverse('documents:document-detail', args=[document.id])
        authenticated_client.delete(url)
        
        assert Document.objects.filter(id=document_id).exists()
        assert Document.objects.get(id=document_id).is_deleted is True
    
    def test_jwt_authentication(self, jwt_client, user):
        """JWT authentication works for delete."""
        document = DocumentFactory.create(related_user=user)
        url = reverse('documents:document-detail', args=[document.id])
        
        response = jwt_client.delete(url)
        
        assert response.status_code == 204
    
    def test_multiple_deletes_idempotent(self, authenticated_client, user):
        """Attempting to delete twice is idempotent (404 second time)."""
        document = DocumentFactory.create(related_user=user)
        url = reverse('documents:document-detail', args=[document.id])
        
        first_response = authenticated_client.delete(url)
        assert first_response.status_code == 204
        
        second_response = authenticated_client.delete(url)
        assert second_response.status_code == 404