# tests/test_views_update.py
"""
Tests for document update endpoints (PUT/PATCH).

Coverage:
- Authentication/authorization
- Full vs partial updates
- Field validation
- Database side effects
- Immutable fields
"""

import pytest
from uuid import uuid4
from django.urls import reverse
from documents.models import Document
from .factories import DocumentFactory


@pytest.mark.django_db
class TestDocumentUpdateEndpoint:
    """Test PUT/PATCH /documents/<id>/ endpoint."""
    
    def test_unauthenticated_user_cannot_update(self, api_client, user):
        """Unauthenticated requests return 401."""
        document = DocumentFactory.create(related_user=user)
        url = reverse('documents:document-detail', args=[document.id])
        data = {'title': 'Updated Title'}
        
        response = api_client.patch(url, data, format='json')
        
        assert response.status_code == 401
    
    def test_owner_can_update_own_document(self, authenticated_client, user):
        """User can update their own document."""
        document = DocumentFactory.create(
            related_user=user,
            title='Original Title'
        )
        url = reverse('documents:document-detail', args=[document.id])
        data = {'title': 'Updated Title'}
        
        response = authenticated_client.patch(url, data, format='json')
        
        assert response.status_code == 200
        assert response.data['title'] == 'Updated Title'
        
        document.refresh_from_db()
        assert document.title == 'Updated Title'
    
    def test_non_owner_cannot_update_document(
        self, authenticated_client, other_user
    ):
        """User cannot update another user's document."""
        document = DocumentFactory.create(related_user=other_user)
        url = reverse('documents:document-detail', args=[document.id])
        data = {'title': 'Hacked Title'}
        
        response = authenticated_client.patch(url, data, format='json')
        
        assert response.status_code == 404
        
        document.refresh_from_db()
        assert document.title != 'Hacked Title'
    
    def test_admin_can_update_any_document(self, admin_client, other_user):
        """Admin can update any user's document."""
        document = DocumentFactory.create(related_user=other_user)
        url = reverse('documents:document-detail', args=[document.id])
        data = {'title': 'Admin Updated'}
        
        response = admin_client.patch(url, data, format='json')
        
        assert response.status_code == 200
        assert response.data['title'] == 'Admin Updated'
    
    def test_patch_updates_only_provided_fields(
        self, authenticated_client, user
    ):
        """PATCH updates only the fields provided."""
        document = DocumentFactory.create(
            related_user=user,
            title='Original Title',
            metadata={'key': 'value'}
        )
        url = reverse('documents:document-detail', args=[document.id])
        data = {'title': 'Updated Title'}
        
        response = authenticated_client.patch(url, data, format='json')
        
        assert response.status_code == 200
        assert response.data['title'] == 'Updated Title'
        assert response.data['metadata'] == {'key': 'value'}
    
    def test_put_full_update(self, authenticated_client, user):
        """PUT performs full update."""
        document = DocumentFactory.create(related_user=user)
        url = reverse('documents:document-detail', args=[document.id])
        data = {
            'title': 'Completely New Title',
            'metadata': {'new': 'metadata'},
        }
        
        response = authenticated_client.put(url, data, format='json')
        
        assert response.status_code == 200
        assert response.data['title'] == 'Completely New Title'
        assert response.data['metadata'] == {'new': 'metadata'}
    
    def test_update_metadata(self, authenticated_client, user):
        """Metadata can be updated."""
        document = DocumentFactory.create(
            related_user=user,
            metadata={'old': 'data'}
        )
        url = reverse('documents:document-detail', args=[document.id])
        new_metadata = {'new': 'data', 'additional': 'info'}
        data = {'metadata': new_metadata}
        
        response = authenticated_client.patch(url, data, format='json')
        
        assert response.status_code == 200
        assert response.data['metadata'] == new_metadata
        
        document.refresh_from_db()
        assert document.metadata == new_metadata
    
    def test_empty_title_fails(self, authenticated_client, user):
        """Updating to empty title fails."""
        document = DocumentFactory.create(related_user=user)
        url = reverse('documents:document-detail', args=[document.id])
        data = {'title': ''}
        
        response = authenticated_client.patch(url, data, format='json')
        
        assert response.status_code == 400
        assert 'title' in response.data
    
    def test_title_too_long_fails(self, authenticated_client, user):
        """Title exceeding max_length fails."""
        document = DocumentFactory.create(related_user=user)
        url = reverse('documents:document-detail', args=[document.id])
        data = {'title': 'A' * 256}
        
        response = authenticated_client.patch(url, data, format='json')
        
        assert response.status_code == 400
        assert 'title' in response.data
    
    def test_non_existent_document_returns_404(self, authenticated_client):
        """Updating non-existent document returns 404."""
        fake_id = uuid4()
        url = reverse('documents:document-detail', args=[fake_id])
        data = {'title': 'New Title'}
        
        response = authenticated_client.patch(url, data, format='json')
        
        assert response.status_code == 404
    
    def test_deleted_document_returns_404(self, authenticated_client, user):
        """Updating soft-deleted document returns 404."""
        document = DocumentFactory.create(
            related_user=user,
            is_deleted=True
        )
        url = reverse('documents:document-detail', args=[document.id])
        data = {'title': 'New Title'}
        
        response = authenticated_client.patch(url, data, format='json')
        
        assert response.status_code == 404
    
    def test_updated_at_changes(self, authenticated_client, user):
        """updated_at timestamp changes on update."""
        document = DocumentFactory.create(related_user=user)
        original_updated_at = document.updated_at
        
        url = reverse('documents:document-detail', args=[document.id])
        data = {'title': 'Updated Title'}
        
        response = authenticated_client.patch(url, data, format='json')
        
        assert response.status_code == 200
        
        document.refresh_from_db()
        assert document.updated_at > original_updated_at
    
    def test_readonly_fields_cannot_be_updated(
        self, authenticated_client, user
    ):
        """Readonly fields like status cannot be updated via API."""
        document = DocumentFactory.create(related_user=user)
        url = reverse('documents:document-detail', args=[document.id])
        data = {
            'title': 'New Title',
            'status': 'completed',
            'file_size': 99999,
        }
        
        response = authenticated_client.patch(url, data, format='json')
        
        assert response.status_code == 200
        
        document.refresh_from_db()
        assert document.title == 'New Title'
        assert document.status != 'completed'
        assert document.file_size != 99999
    
    def test_unicode_characters_in_title(self, authenticated_client, user):
        """Title can contain unicode characters."""
        document = DocumentFactory.create(related_user=user)
        url = reverse('documents:document-detail', args=[document.id])
        data = {'title': 'Документ №123 ✓'}
        
        response = authenticated_client.patch(url, data, format='json')
        
        assert response.status_code == 200
        assert response.data['title'] == 'Документ №123 ✓'
    
    def test_jwt_authentication(self, jwt_client, user):
        """JWT authentication works for update."""
        document = DocumentFactory.create(related_user=user)
        url = reverse('documents:document-detail', args=[document.id])
        data = {'title': 'JWT Updated'}
        
        response = jwt_client.patch(url, data, format='json')
        
        assert response.status_code == 200