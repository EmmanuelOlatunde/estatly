# tests/test_views_create.py
"""
Tests for document creation endpoints.

Coverage:
- Authentication requirements
- Validation of required fields
- Different document types
- Database side effects
- Error responses
"""

import pytest
from uuid import uuid4
from django.urls import reverse
from documents.models import Document, DocumentType, DocumentStatus
from .factories import UserFactory


@pytest.mark.django_db
class TestDocumentCreateEndpoint:
    """Test POST /documents/ endpoint."""
    
    def test_unauthenticated_user_cannot_create(self, api_client):
        """Unauthenticated requests return 401."""
        url = reverse('documents:document-list')
        data = {
            'document_type': DocumentType.PAYMENT_RECEIPT,
            'title': 'Test Receipt',
            'related_payment_id': str(uuid4()),
        }
        
        response = api_client.post(url, data, format='json')
        
        assert response.status_code == 401
    
    def test_create_payment_receipt(self, authenticated_client, user):
        """User can create a payment receipt document."""
        payment_id = uuid4()
        url = reverse('documents:document-list')
        data = {
            'document_type': DocumentType.PAYMENT_RECEIPT,
            'title': 'Payment Receipt #123',
            'related_user': user.id,
            'related_payment_id': str(payment_id),
            'metadata': {'amount': 1000, 'currency': 'USD'},
        }
        
        response = authenticated_client.post(url, data, format='json')
        
        assert response.status_code == 201
        assert 'id' in response.data
        assert response.data['title'] == 'Payment Receipt #123'
        assert response.data['document_type'] == DocumentType.PAYMENT_RECEIPT
        assert response.data['status'] == DocumentStatus.PENDING
        
        document = Document.objects.get(id=response.data['id'])
        assert document.title == 'Payment Receipt #123'
        assert document.related_payment_id == payment_id
        assert document.metadata == {'amount': 1000, 'currency': 'USD'}
        assert document.created_at is not None
    
    def test_create_announcement_document(self, authenticated_client, user):
        """User can create an announcement document."""
        announcement_id = uuid4()
        url = reverse('documents:document-list')
        data = {
            'document_type': DocumentType.ANNOUNCEMENT,
            'title': 'Community Announcement',
            'related_user': user.id,
            'related_announcement_id': str(announcement_id),
            'metadata': {},
        }
        
        response = authenticated_client.post(url, data, format='json')
        
        assert response.status_code == 201
        assert response.data['document_type'] == DocumentType.ANNOUNCEMENT
        
        document = Document.objects.get(id=response.data['id'])
        assert document.related_announcement_id == announcement_id
    
    def test_missing_title_fails(self, authenticated_client, user):
        """Creating document without title fails with 400."""
        url = reverse('documents:document-list')
        data = {
            'document_type': DocumentType.PAYMENT_RECEIPT,
            'related_user': user.id,
            'related_payment_id': str(uuid4()),
        }
        
        response = authenticated_client.post(url, data, format='json')
        
        assert response.status_code == 400
        assert 'title' in response.data
    
    def test_missing_document_type_fails(self, authenticated_client, user):
        """Creating document without type fails with 400."""
        url = reverse('documents:document-list')
        data = {
            'title': 'Test Document',
            'related_user': user.id,
            'related_payment_id': str(uuid4()),
        }
        
        response = authenticated_client.post(url, data, format='json')
        
        assert response.status_code == 400
        assert 'document_type' in response.data
    
    def test_payment_receipt_without_payment_id_fails(
        self, authenticated_client, user
    ):
        """Payment receipt requires related_payment_id."""
        url = reverse('documents:document-list')
        data = {
            'document_type': DocumentType.PAYMENT_RECEIPT,
            'title': 'Payment Receipt',
            'related_user': user.id,
        }
        
        response = authenticated_client.post(url, data, format='json')
        
        assert response.status_code == 400
        assert 'related_payment_id' in response.data
    
    def test_announcement_without_announcement_id_fails(
        self, authenticated_client, user
    ):
        """Announcement requires related_announcement_id."""
        url = reverse('documents:document-list')
        data = {
            'document_type': DocumentType.ANNOUNCEMENT,
            'title': 'Announcement',
            'related_user': user.id,
        }
        
        response = authenticated_client.post(url, data, format='json')
        
        assert response.status_code == 400
        assert 'related_announcement_id' in response.data
    
    def test_invalid_document_type_fails(self, authenticated_client, user):
        """Invalid document type fails validation."""
        url = reverse('documents:document-list')
        data = {
            'document_type': 'invalid_type',
            'title': 'Test Document',
            'related_user': user.id,
        }
        
        response = authenticated_client.post(url, data, format='json')
        
        assert response.status_code == 400
        assert 'document_type' in response.data
    
    def test_invalid_uuid_fails(self, authenticated_client, user):
        """Invalid UUID format fails validation."""
        url = reverse('documents:document-list')
        data = {
            'document_type': DocumentType.PAYMENT_RECEIPT,
            'title': 'Test Receipt',
            'related_user': user.id,
            'related_payment_id': 'not-a-uuid',
        }
        
        response = authenticated_client.post(url, data, format='json')
        
        assert response.status_code == 400
    
    def test_empty_title_fails(self, authenticated_client, user):
        """Empty string for title fails validation."""
        url = reverse('documents:document-list')
        data = {
            'document_type': DocumentType.PAYMENT_RECEIPT,
            'title': '',
            'related_user': user.id,
            'related_payment_id': str(uuid4()),
        }
        
        response = authenticated_client.post(url, data, format='json')
        
        assert response.status_code == 400
        assert 'title' in response.data
    
    def test_very_long_title(self, authenticated_client, user):
        """Very long title near max_length works."""
        long_title = 'A' * 255
        url = reverse('documents:document-list')
        data = {
            'document_type': DocumentType.PAYMENT_RECEIPT,
            'title': long_title,
            'related_user': user.id,
            'related_payment_id': str(uuid4()),
        }
        
        response = authenticated_client.post(url, data, format='json')
        
        assert response.status_code == 201
        assert response.data['title'] == long_title
    
    def test_title_exceeding_max_length_fails(
        self, authenticated_client, user
    ):
        """Title exceeding max_length fails validation."""
        too_long_title = 'A' * 256
        url = reverse('documents:document-list')
        data = {
            'document_type': DocumentType.PAYMENT_RECEIPT,
            'title': too_long_title,
            'related_user': user.id,
            'related_payment_id': str(uuid4()),
        }
        
        response = authenticated_client.post(url, data, format='json')
        
        assert response.status_code == 400
        assert 'title' in response.data
    
    def test_metadata_can_be_empty_dict(self, authenticated_client, user):
        """Metadata can be empty dictionary."""
        url = reverse('documents:document-list')
        data = {
            'document_type': DocumentType.PAYMENT_RECEIPT,
            'title': 'Test',
            'related_user': user.id,
            'related_payment_id': str(uuid4()),
            'metadata': {},
        }
        
        response = authenticated_client.post(url, data, format='json')
        
        assert response.status_code == 201
        assert response.data['metadata'] == {}
    
    def test_metadata_with_nested_structure(self, authenticated_client, user):
        """Metadata can contain nested structures."""
        url = reverse('documents:document-list')
        metadata = {
            'payment': {
                'amount': 1000,
                'items': ['item1', 'item2'],
            },
            'user_info': {'name': 'Test User'},
        }
        data = {
            'document_type': DocumentType.PAYMENT_RECEIPT,
            'title': 'Test',
            'related_user': user.id,
            'related_payment_id': str(uuid4()),
            'metadata': metadata,
        }
        
        response = authenticated_client.post(url, data, format='json')
        
        assert response.status_code == 201
        assert response.data['metadata'] == metadata
    
    def test_malformed_json_fails(self, authenticated_client):
        """Malformed JSON returns 400."""
        url = reverse('documents:document-list')
        
        response = authenticated_client.post(
            url,
            data='{"invalid json',
            content_type='application/json'
        )
        
        assert response.status_code == 400
    
    def test_jwt_authentication(self, jwt_client, user):
        """JWT authentication works for create."""
        url = reverse('documents:document-list')
        data = {
            'document_type': DocumentType.PAYMENT_RECEIPT,
            'title': 'Test Receipt',
            'related_user': user.id,
            'related_payment_id': str(uuid4()),
        }
        
        response = jwt_client.post(url, data, format='json')
        
        assert response.status_code == 201
    
    def test_document_count_increases(self, authenticated_client, user):
        """Creating document increases database count."""
        initial_count = Document.objects.count()
        
        url = reverse('documents:document-list')
        data = {
            'document_type': DocumentType.PAYMENT_RECEIPT,
            'title': 'Test Receipt',
            'related_user': user.id,
            'related_payment_id': str(uuid4()),
        }
        
        response = authenticated_client.post(url, data, format='json')
        
        assert response.status_code == 201
        assert Document.objects.count() == initial_count + 1