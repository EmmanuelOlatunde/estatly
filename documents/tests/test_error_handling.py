# tests/test_error_handling.py
"""
Tests for error responses and exception handling.

Coverage:
- HTTP error status codes
- Error message formats
- Validation error structures
- Exception scenarios
"""

import pytest
from uuid import uuid4
from django.urls import reverse
from documents.models import DocumentType
from .factories import DocumentFactory, CompletedDocumentFactory


@pytest.mark.django_db
class TestErrorResponses:
    """Test error responses and status codes."""
    
    def test_404_for_non_existent_document(self, authenticated_client):
        """Non-existent document returns 404."""
        fake_id = uuid4()
        url = reverse('documents:document-detail', args=[fake_id])
        
        response = authenticated_client.get(url)
        
        assert response.status_code == 404
        assert 'detail' in response.data
    
    def test_401_for_unauthenticated_access(self, api_client):
        """Unauthenticated access returns 401."""
        url = reverse('documents:document-list')
        
        response = api_client.get(url)
        
        assert response.status_code == 401
    
    def test_403_or_404_for_unauthorized_access(
        self, authenticated_client, other_user
    ):
        """Unauthorized access returns 403 or 404."""
        document = DocumentFactory.create(related_user=other_user)
        url = reverse('documents:document-detail', args=[document.id])
        
        response = authenticated_client.get(url)
        
        assert response.status_code in [403, 404]
    
    def test_400_for_missing_required_field(self, authenticated_client, user):
        """Missing required field returns 400 with field error."""
        url = reverse('documents:document-list')
        data = {
            'document_type': DocumentType.PAYMENT_RECEIPT,
            'related_user': user.id,
            'related_payment_id': str(uuid4()),
        }
        
        response = authenticated_client.post(url, data, format='json')
        
        assert response.status_code == 400
        assert 'title' in response.data
    
    def test_400_for_invalid_field_type(self, authenticated_client, user):
        """Invalid field type returns 400."""
        url = reverse('documents:document-list')
        data = {
            'document_type': DocumentType.PAYMENT_RECEIPT,
            'title': 'Test',
            'related_user': user.id,
            'related_payment_id': 'not-a-uuid',
        }
        
        response = authenticated_client.post(url, data, format='json')
        
        assert response.status_code == 400
    
    def test_400_for_invalid_choice_field(self, authenticated_client, user):
        """Invalid choice value returns 400."""
        url = reverse('documents:document-list')
        data = {
            'document_type': 'invalid_type',
            'title': 'Test',
            'related_user': user.id,
        }
        
        response = authenticated_client.post(url, data, format='json')
        
        assert response.status_code == 400
        assert 'document_type' in response.data
    
    def test_400_for_validation_error(self, authenticated_client, user):
        """Business rule validation returns 400."""
        url = reverse('documents:document-list')
        data = {
            'document_type': DocumentType.PAYMENT_RECEIPT,
            'title': 'Test Receipt',
            'related_user': user.id,
        }
        
        response = authenticated_client.post(url, data, format='json')
        
        assert response.status_code == 400
        assert 'related_payment_id' in response.data
    
    def test_400_for_malformed_json(self, authenticated_client):
        """Malformed JSON returns 400."""
        url = reverse('documents:document-list')
        
        response = authenticated_client.post(
            url,
            data='{"invalid": json',
            content_type='application/json'
        )
        
        assert response.status_code == 400
    
    def test_405_for_unsupported_method(self, authenticated_client):
        """Unsupported HTTP method returns 405."""
        url = reverse('documents:document-list')
        
        response = authenticated_client.patch(url)
        
        assert response.status_code == 405
    
    def test_404_for_invalid_url(self, authenticated_client):
        """Invalid URL returns 404."""
        response = authenticated_client.get('/documents/invalid-endpoint/')
        
        assert response.status_code == 404
    
    def test_error_message_format(self, authenticated_client, user):
        """Error messages follow DRF format."""
        url = reverse('documents:document-list')
        data = {
            'document_type': DocumentType.PAYMENT_RECEIPT,
            'related_user': user.id,
        }
        
        response = authenticated_client.post(url, data, format='json')
        
        assert response.status_code == 400
        assert isinstance(response.data, dict)
        assert 'title' in response.data
        assert isinstance(response.data['title'], list)
    
    def test_multiple_validation_errors(self, authenticated_client):
        """Multiple validation errors are returned together."""
        url = reverse('documents:document-list')
        data = {}
        
        response = authenticated_client.post(url, data, format='json')
        
        assert response.status_code == 400
        assert 'document_type' in response.data or 'title' in response.data
    
    def test_no_sensitive_data_in_error(self, authenticated_client, user):
        """Error responses don't leak sensitive data."""
        url = reverse('documents:document-list')
        data = {
            'document_type': 'invalid',
            'title': 'Test',
        }
        
        response = authenticated_client.post(url, data, format='json')
        
        assert response.status_code == 400
        error_text = str(response.data).lower()
        assert 'password' not in error_text
        assert 'secret' not in error_text
        assert 'token' not in error_text
    
    def test_error_for_string_instead_of_object(
        self, authenticated_client, user
    ):
        """Passing string instead of object returns 400."""
        url = reverse('documents:document-list')
        
        response = authenticated_client.post(
            url,
            data='"just a string"',
            content_type='application/json'
        )
        
        assert response.status_code == 400
    
    def test_error_for_array_instead_of_object(
        self, authenticated_client, user
    ):
        """Passing array instead of object returns 400."""
        url = reverse('documents:document-list')
        
        response = authenticated_client.post(
            url,
            data='["array", "data"]',
            content_type='application/json'
        )
        
        assert response.status_code == 400
    
    def test_regenerate_generating_document_error(
        self, authenticated_client, user
    ):
        """Regenerating generating document returns clear error."""
        from documents.models import DocumentStatus
        
        document = DocumentFactory.create(
            related_user=user,
            status=DocumentStatus.GENERATING
        )
        url = reverse('documents:document-regenerate', args=[document.id])
        data = {'force': True}
        
        response = authenticated_client.post(url, data, format='json')
        
        assert response.status_code == 400
        assert 'error' in response.data or 'non_field_errors' in response.data
    
    def test_download_incomplete_document_error(
        self, authenticated_client, user
    ):
        """Downloading incomplete document returns clear error."""
        from documents.models import DocumentStatus
        
        document = DocumentFactory.create(
            related_user=user,
            status=DocumentStatus.PENDING
        )
        url = reverse('documents:document-download', args=[document.id])
        
        response = authenticated_client.get(url)
        
        assert response.status_code == 404
        assert 'not ready' in str(response.data).lower() or 'detail' in response.data
    
    def test_invalid_page_number_error(self, authenticated_client, user):
        """Invalid page number returns 404."""
        DocumentFactory.create_batch(5, related_user=user)
        
        url = reverse('documents:document-list')
        response = authenticated_client.get(url, {'page': 999})
        
        assert response.status_code == 404
    
    def test_invalid_ordering_field_handled_gracefully(
        self, authenticated_client, user
    ):
        """Invalid ordering field doesn't crash."""
        DocumentFactory.create_batch(3, related_user=user)
        
        url = reverse('documents:document-list')
        response = authenticated_client.get(
            url,
            {'ordering': 'nonexistent_field'}
        )
        
        assert response.status_code == 200