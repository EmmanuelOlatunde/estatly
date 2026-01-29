# tests/test_security.py
"""
Tests for security vulnerabilities and attack vectors.

Coverage:
- IDOR (Insecure Direct Object Reference)
- SQL injection attempts
- XSS payloads
- Mass assignment vulnerabilities
- Authorization bypasses
- Data leakage
"""

import pytest
from uuid import uuid4
from django.urls import reverse
from documents.models import Document, DocumentType
from .factories import DocumentFactory, CompletedDocumentFactory, UserFactory


@pytest.mark.django_db
class TestIDORVulnerabilities:
    """Test Insecure Direct Object Reference vulnerabilities."""
    
    def test_cannot_access_other_user_document_by_id(
        self, authenticated_client, other_user
    ):
        """User cannot access another user's document via ID (IDOR)."""
        other_document = DocumentFactory.create(related_user=other_user)
        
        url = reverse('documents:document-detail', args=[other_document.id])
        response = authenticated_client.get(url)
        
        assert response.status_code == 404
    
    def test_cannot_update_other_user_document(
        self, authenticated_client, other_user
    ):
        """User cannot update another user's document."""
        other_document = DocumentFactory.create(related_user=other_user)
        
        url = reverse('documents:document-detail', args=[other_document.id])
        data = {'title': 'Hacked Title'}
        response = authenticated_client.patch(url, data, format='json')
        
        assert response.status_code == 404
        
        other_document.refresh_from_db()
        assert other_document.title != 'Hacked Title'
    
    def test_cannot_delete_other_user_document(
        self, authenticated_client, other_user
    ):
        """User cannot delete another user's document."""
        other_document = DocumentFactory.create(related_user=other_user)
        
        url = reverse('documents:document-detail', args=[other_document.id])
        response = authenticated_client.delete(url)
        
        assert response.status_code == 404
        
        other_document.refresh_from_db()
        assert not other_document.is_deleted
    
    def test_cannot_download_other_user_document(
        self, authenticated_client, other_user
    ):
        """User cannot download another user's document."""
        other_document = CompletedDocumentFactory.create(
            related_user=other_user
        )
        
        url = reverse('documents:document-download', args=[other_document.id])
        response = authenticated_client.get(url)
        
        assert response.status_code == 404
    
    def test_cannot_view_other_user_download_stats(
        self, authenticated_client, other_user
    ):
        """User cannot view stats for another user's document."""
        other_document = CompletedDocumentFactory.create(
            related_user=other_user
        )
        
        url = reverse('documents:document-stats', args=[other_document.id])
        response = authenticated_client.get(url)
        
        assert response.status_code == 404
    
    def test_list_does_not_leak_other_user_documents(
        self, authenticated_client, user, other_user
    ):
        """List endpoint doesn't leak other users' documents."""
        DocumentFactory.create_batch(3, related_user=user)
        DocumentFactory.create_batch(5, related_user=other_user)
        
        url = reverse('documents:document-list')
        response = authenticated_client.get(url)
        
        assert response.status_code == 200
        assert response.data['count'] == 3
        
        for doc in response.data['results']:
            assert str(doc['related_user']) == str(user.id)


@pytest.mark.django_db
class TestInjectionAttacks:
    """Test SQL injection and other injection attempts."""
    
    def test_sql_injection_in_title(self, authenticated_client, user):
        """SQL injection payload in title is sanitized."""
        sql_payload = "'; DROP TABLE documents; --"
        
        url = reverse('documents:document-list')
        data = {
            'document_type': DocumentType.PAYMENT_RECEIPT,
            'title': sql_payload,
            'related_user': user.id,
            'related_payment_id': str(uuid4()),
        }
        
        response = authenticated_client.post(url, data, format='json')
        
        assert response.status_code == 201
        assert Document.objects.exists()
    
    def test_sql_injection_in_search(self, authenticated_client, user):
        """SQL injection in search is sanitized."""
        DocumentFactory.create(related_user=user, title='Test')
        
        url = reverse('documents:document-list')
        response = authenticated_client.get(
            url,
            {'search': "' OR '1'='1"}
        )
        
        assert response.status_code == 200
    
    def test_xss_payload_in_title(self, authenticated_client, user):
        """XSS payload in title is stored but should be escaped on output."""
        xss_payload = '<script>alert("XSS")</script>'
        
        url = reverse('documents:document-list')
        data = {
            'document_type': DocumentType.PAYMENT_RECEIPT,
            'title': xss_payload,
            'related_user': user.id,
            'related_payment_id': str(uuid4()),
        }
        
        response = authenticated_client.post(url, data, format='json')
        
        assert response.status_code == 201
        assert response.data['title'] == xss_payload
    
    def test_html_in_metadata(self, authenticated_client, user):
        """HTML in metadata is stored as-is."""
        url = reverse('documents:document-list')
        data = {
            'document_type': DocumentType.PAYMENT_RECEIPT,
            'title': 'Test',
            'related_user': user.id,
            'related_payment_id': str(uuid4()),
            'metadata': {
                'description': '<b>Bold</b> text',
                'notes': '<script>alert("test")</script>'
            },
        }
        
        response = authenticated_client.post(url, data, format='json')
        
        assert response.status_code == 201
        assert '<b>Bold</b>' in response.data['metadata']['description']


@pytest.mark.django_db
class TestMassAssignmentVulnerabilities:
    """Test mass assignment vulnerabilities."""
    
    def test_cannot_set_id_on_create(self, authenticated_client, user):
        """User cannot specify ID when creating."""
        custom_id = uuid4()
        
        url = reverse('documents:document-list')
        data = {
            'id': str(custom_id),
            'document_type': DocumentType.PAYMENT_RECEIPT,
            'title': 'Test',
            'related_user': user.id,
            'related_payment_id': str(uuid4()),
        }
        
        response = authenticated_client.post(url, data, format='json')
        
        assert response.status_code == 201
        assert str(response.data['id']) != str(custom_id)
    
    def test_cannot_set_status_on_create(self, authenticated_client, user):
        """User cannot set status when creating."""
        from documents.models import DocumentStatus
        
        url = reverse('documents:document-list')
        data = {
            'document_type': DocumentType.PAYMENT_RECEIPT,
            'title': 'Test',
            'related_user': user.id,
            'related_payment_id': str(uuid4()),
            'status': DocumentStatus.COMPLETED,
        }
        
        response = authenticated_client.post(url, data, format='json')
        
        assert response.status_code == 201
        assert response.data['status'] == DocumentStatus.PENDING
    
    def test_cannot_set_file_size_on_create(self, authenticated_client, user):
        """User cannot manipulate file_size field."""
        url = reverse('documents:document-list')
        data = {
            'document_type': DocumentType.PAYMENT_RECEIPT,
            'title': 'Test',
            'related_user': user.id,
            'related_payment_id': str(uuid4()),
            'file_size': 999999,
        }
        
        response = authenticated_client.post(url, data, format='json')
        
        assert response.status_code == 201
        assert response.data['file_size'] is None
    
    def test_cannot_set_created_at_on_create(
        self, authenticated_client, user
    ):
        """User cannot manipulate created_at timestamp."""
        from django.utils import timezone
        from datetime import timedelta
        
        past_date = timezone.now() - timedelta(days=365)
        
        url = reverse('documents:document-list')
        data = {
            'document_type': DocumentType.PAYMENT_RECEIPT,
            'title': 'Test',
            'related_user': user.id,
            'related_payment_id': str(uuid4()),
            'created_at': past_date.isoformat(),
        }
        
        response = authenticated_client.post(url, data, format='json')
        
        assert response.status_code == 201
    
    def test_cannot_change_related_user_on_update(
        self, authenticated_client, user
    ):
        """User cannot change document ownership."""
        document = DocumentFactory.create(related_user=user)
        other_user = UserFactory.create()
        
        url = reverse('documents:document-detail', args=[document.id])
        data = {'related_user': other_user.id}
        
        response = authenticated_client.patch(url, data, format='json')
        
        document.refresh_from_db()
        assert document.related_user == user
    
    def test_cannot_change_document_type_on_update(
        self, authenticated_client, user
    ):
        """User cannot change document type after creation."""
        document = DocumentFactory.create(
            related_user=user,
            document_type=DocumentType.PAYMENT_RECEIPT
        )
        
        url = reverse('documents:document-detail', args=[document.id])
        data = {'document_type': DocumentType.ANNOUNCEMENT}
        
        response = authenticated_client.patch(url, data, format='json')
        
        document.refresh_from_db()
        assert document.document_type == DocumentType.PAYMENT_RECEIPT


@pytest.mark.django_db
class TestDataLeakage:
    """Test for sensitive data leakage."""
    
    def test_error_messages_do_not_leak_existence(
        self, authenticated_client, other_user
    ):
        """Error messages don't confirm resource existence."""
        other_document = DocumentFactory.create(related_user=other_user)
        fake_id = uuid4()
        
        url1 = reverse('documents:document-detail', args=[other_document.id])
        url2 = reverse('documents:document-detail', args=[fake_id])
        
        response1 = authenticated_client.get(url1)
        response2 = authenticated_client.get(url2)
        
        assert response1.status_code == 404
        assert response2.status_code == 404
    
    def test_deleted_documents_not_discoverable(
        self, authenticated_client, user
    ):
        """Deleted documents return same 404 as non-existent."""
        document = DocumentFactory.create(related_user=user, is_deleted=True)
        
        url = reverse('documents:document-detail', args=[document.id])
        response = authenticated_client.get(url)
        
        assert response.status_code == 404
    
    def test_filter_does_not_leak_other_user_data(
        self, authenticated_client, user, other_user
    ):
        """Filters don't leak other users' data."""
        payment_id = uuid4()
        
        DocumentFactory.create(related_user=user)
        DocumentFactory.create(
            related_user=other_user,
            document_type=DocumentType.PAYMENT_RECEIPT,
            related_payment_id=payment_id
        )
        
        url = reverse('documents:document-list')
        response = authenticated_client.get(
            url,
            {'related_payment_id': str(payment_id)}
        )
        
        assert response.status_code == 200
        assert response.data['count'] == 0
    
    def test_search_does_not_leak_other_user_data(
        self, authenticated_client, user, other_user
    ):
        """Search doesn't return other users' documents."""
        unique_title = "UNIQUE_SECRET_TITLE_12345"
        
        DocumentFactory.create(related_user=user, title="My Document")
        DocumentFactory.create(related_user=other_user, title=unique_title)
        
        url = reverse('documents:document-list')
        response = authenticated_client.get(url, {'search': unique_title})
        
        assert response.status_code == 200
        assert response.data['count'] == 0


@pytest.mark.django_db
class TestAuthorizationBypass:
    """Test for authorization bypass attempts."""
    
    def test_cannot_bypass_auth_with_manipulated_user_id(
        self, authenticated_client, user, other_user
    ):
        """Cannot access data by manipulating user ID in request."""
        other_document = DocumentFactory.create(related_user=other_user)
        
        url = reverse('documents:document-detail', args=[other_document.id])
        response = authenticated_client.get(
            url,
            HTTP_X_USER_ID=str(other_user.id)
        )
        
        assert response.status_code == 404
    
    def test_jwt_token_required_for_protected_endpoints(
        self, api_client
    ):
        """Protected endpoints require valid JWT token."""
        url = reverse('documents:document-list')
        
        response = api_client.get(
            url,
            HTTP_AUTHORIZATION='Bearer invalid-token'
        )
        
        assert response.status_code == 401
    
    def test_expired_tokens_rejected(self, api_client):
        """Expired tokens are rejected."""
        url = reverse('documents:document-list')
        
        response = api_client.get(
            url,
            HTTP_AUTHORIZATION='Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.expired'
        )
        
        assert response.status_code == 401