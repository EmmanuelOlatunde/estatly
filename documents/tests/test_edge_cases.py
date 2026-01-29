# tests/test_edge_cases.py
"""
Tests for edge cases and boundary conditions.

Coverage:
- Null vs empty values
- Boundary values
- Unicode handling
- Concurrent operations
- Timezone handling
"""

import pytest
from uuid import uuid4
from django.urls import reverse
from django.utils import timezone
from datetime import timedelta
from documents.models import Document, DocumentType
from .factories import DocumentFactory, CompletedDocumentFactory, UserFactory


@pytest.mark.django_db
class TestEdgeCases:
    """Test edge cases and boundary conditions."""
    
    def test_document_with_null_related_user(self, admin_client):
        """Document with null related_user can be created by admin."""
        url = reverse('documents:document-list')
        data = {
            'document_type': DocumentType.PAYMENT_RECEIPT,
            'title': 'System Generated',
            'related_payment_id': str(uuid4()),
        }
        
        response = admin_client.post(url, data, format='json')
        
        assert response.status_code == 201
        assert response.data['related_user'] is None
    
    def test_empty_metadata(self, authenticated_client, user):
        """Empty metadata dictionary is valid."""
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
    
    def test_very_large_metadata_object(self, authenticated_client, user):
        """Large metadata object is accepted."""
        large_metadata = {f"key_{i}": f"value_{i}" for i in range(100)}
        
        url = reverse('documents:document-list')
        data = {
            'document_type': DocumentType.PAYMENT_RECEIPT,
            'title': 'Test',
            'related_user': user.id,
            'related_payment_id': str(uuid4()),
            'metadata': large_metadata,
        }
        
        response = authenticated_client.post(url, data, format='json')
        
        assert response.status_code == 201
        assert len(response.data['metadata']) == 100
    
    def test_title_with_special_characters(self, authenticated_client, user):
        """Title with special characters is valid."""
        special_title = "Receipt #123 <Test> & 'Quotes' \"Double\" @#$%"
        
        url = reverse('documents:document-list')
        data = {
            'document_type': DocumentType.PAYMENT_RECEIPT,
            'title': special_title,
            'related_user': user.id,
            'related_payment_id': str(uuid4()),
        }
        
        response = authenticated_client.post(url, data, format='json')
        
        assert response.status_code == 201
        assert response.data['title'] == special_title
    
    def test_title_with_newlines(self, authenticated_client, user):
        """Title with newlines is accepted."""
        title_with_newlines = "Line 1\nLine 2\nLine 3"
        
        url = reverse('documents:document-list')
        data = {
            'document_type': DocumentType.PAYMENT_RECEIPT,
            'title': title_with_newlines,
            'related_user': user.id,
            'related_payment_id': str(uuid4()),
        }
        
        response = authenticated_client.post(url, data, format='json')
        
        assert response.status_code == 201
    
    def test_title_with_emoji(self, authenticated_client, user):
        """Title with emoji characters is valid."""
        emoji_title = "Payment Receipt 💰✓🎉"
        
        url = reverse('documents:document-list')
        data = {
            'document_type': DocumentType.PAYMENT_RECEIPT,
            'title': emoji_title,
            'related_user': user.id,
            'related_payment_id': str(uuid4()),
        }
        
        response = authenticated_client.post(url, data, format='json')
        
        assert response.status_code == 201
        assert response.data['title'] == emoji_title
    
    def test_title_with_rtl_text(self, authenticated_client, user):
        """Title with right-to-left text is valid."""
        rtl_title = "وثيقة الدفع"
        
        url = reverse('documents:document-list')
        data = {
            'document_type': DocumentType.PAYMENT_RECEIPT,
            'title': rtl_title,
            'related_user': user.id,
            'related_payment_id': str(uuid4()),
        }
        
        response = authenticated_client.post(url, data, format='json')
        
        assert response.status_code == 201
        assert response.data['title'] == rtl_title
    
    def test_title_at_max_length(self, authenticated_client, user):
        """Title at exactly max_length (255) is valid."""
        max_title = 'A' * 255
        
        url = reverse('documents:document-list')
        data = {
            'document_type': DocumentType.PAYMENT_RECEIPT,
            'title': max_title,
            'related_user': user.id,
            'related_payment_id': str(uuid4()),
        }
        
        response = authenticated_client.post(url, data, format='json')
        
        assert response.status_code == 201
        assert len(response.data['title']) == 255
    
    def test_single_character_title(self, authenticated_client, user):
        """Single character title is valid."""
        url = reverse('documents:document-list')
        data = {
            'document_type': DocumentType.PAYMENT_RECEIPT,
            'title': 'X',
            'related_user': user.id,
            'related_payment_id': str(uuid4()),
        }
        
        response = authenticated_client.post(url, data, format='json')
        
        assert response.status_code == 201
        assert response.data['title'] == 'X'
    
    def test_whitespace_only_title_trimmed(self, authenticated_client, user):
        """Whitespace-only title fails validation."""
        url = reverse('documents:document-list')
        data = {
            'document_type': DocumentType.PAYMENT_RECEIPT,
            'title': '   ',
            'related_user': user.id,
            'related_payment_id': str(uuid4()),
        }
        
        response = authenticated_client.post(url, data, format='json')
        
        assert response.status_code == 400
    
    def test_multiple_documents_same_payment_id(
        self, authenticated_client, user
    ):
        """Multiple documents can reference same payment ID."""
        payment_id = uuid4()
        
        url = reverse('documents:document-list')
        data1 = {
            'document_type': DocumentType.PAYMENT_RECEIPT,
            'title': 'Receipt 1',
            'related_user': user.id,
            'related_payment_id': str(payment_id),
        }
        data2 = {
            'document_type': DocumentType.PAYMENT_RECEIPT,
            'title': 'Receipt 2',
            'related_user': user.id,
            'related_payment_id': str(payment_id),
        }
        
        response1 = authenticated_client.post(url, data1, format='json')
        response2 = authenticated_client.post(url, data2, format='json')
        
        assert response1.status_code == 201
        assert response2.status_code == 201
    
    def test_no_results_returns_empty_array(self, authenticated_client):
        """Query with no results returns empty array, not null."""
        url = reverse('documents:document-list')
        response = authenticated_client.get(url)
        
        assert response.status_code == 200
        assert response.data['results'] == []
        assert response.data['count'] == 0
    
    def test_future_created_at_allowed(self, authenticated_client, user):
        """Documents can be created (edge case for system time issues)."""
        document = DocumentFactory.create(
            related_user=user,
            created_at=timezone.now() + timedelta(days=1)
        )
        
        url = reverse('documents:document-detail', args=[document.id])
        response = authenticated_client.get(url)
        
        assert response.status_code == 200
    
    def test_very_old_document(self, authenticated_client, user):
        """Very old documents can be retrieved."""
        document = DocumentFactory.create(
            related_user=user,
            created_at=timezone.now() - timedelta(days=3650)
        )
        
        url = reverse('documents:document-detail', args=[document.id])
        response = authenticated_client.get(url)
        
        assert response.status_code == 200
    
    def test_user_with_many_documents(self, authenticated_client, user):
        """User can have large number of documents."""
        DocumentFactory.create_batch(100, related_user=user)
        
        url = reverse('documents:document-list')
        response = authenticated_client.get(url)
        
        assert response.status_code == 200
        assert response.data['count'] == 100
    
    def test_metadata_with_nested_arrays(self, authenticated_client, user):
        """Metadata can contain nested arrays."""
        url = reverse('documents:document-list')
        data = {
            'document_type': DocumentType.PAYMENT_RECEIPT,
            'title': 'Test',
            'related_user': user.id,
            'related_payment_id': str(uuid4()),
            'metadata': {
                'items': [
                    {'name': 'Item 1', 'price': 100},
                    {'name': 'Item 2', 'price': 200},
                ],
                'tags': ['tag1', 'tag2', 'tag3'],
            },
        }
        
        response = authenticated_client.post(url, data, format='json')
        
        assert response.status_code == 201
        assert 'items' in response.data['metadata']
        assert len(response.data['metadata']['items']) == 2
    
    def test_metadata_with_boolean_values(self, authenticated_client, user):
        """Metadata can contain boolean values."""
        url = reverse('documents:document-list')
        data = {
            'document_type': DocumentType.PAYMENT_RECEIPT,
            'title': 'Test',
            'related_user': user.id,
            'related_payment_id': str(uuid4()),
            'metadata': {
                'is_paid': True,
                'is_refunded': False,
                'has_discount': True,
            },
        }
        
        response = authenticated_client.post(url, data, format='json')
        
        assert response.status_code == 201
        assert response.data['metadata']['is_paid'] is True
        assert response.data['metadata']['is_refunded'] is False
    
    def test_metadata_with_null_values(self, authenticated_client, user):
        """Metadata can contain null values."""
        url = reverse('documents:document-list')
        data = {
            'document_type': DocumentType.PAYMENT_RECEIPT,
            'title': 'Test',
            'related_user': user.id,
            'related_payment_id': str(uuid4()),
            'metadata': {
                'optional_field': None,
                'another_field': 'value',
            },
        }
        
        response = authenticated_client.post(url, data, format='json')
        
        assert response.status_code == 201
        assert response.data['metadata']['optional_field'] is None
    
    def test_case_sensitive_uuid_lookup(self, authenticated_client, user):
        """UUID lookup is case-insensitive."""
        document = DocumentFactory.create(related_user=user)
        doc_id_upper = str(document.id).upper()
        
        url = reverse('documents:document-detail', args=[doc_id_upper])
        response = authenticated_client.get(url)
        
        assert response.status_code == 200
        assert str(response.data['id']) == str(document.id)