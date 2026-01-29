# tests/test_views_list.py
"""
Tests for documents list/search endpoints.

Coverage:
- Authentication requirements
- User-scoped results
- Empty results
- Pagination
- Basic filtering
"""

import pytest
from django.urls import reverse
from documents.models import DocumentStatus
from .factories import (
    DocumentFactory,
    CompletedDocumentFactory,
    PaymentReceiptFactory,
    AnnouncementDocumentFactory,
)
from .helpers import (
    assert_paginated_response,
    assert_document_response_structure,
)


@pytest.mark.django_db
class TestDocumentListEndpoint:
    """Test GET /documents/ endpoint."""
    
    def test_unauthenticated_user_cannot_list(self, api_client):
        """Unauthenticated requests return 401."""
        url = reverse('documents:document-list')
        response = api_client.get(url)
        
        assert response.status_code == 401
    
    def test_authenticated_user_can_list(self, authenticated_client, user):
        """Authenticated user can list their documents."""
        DocumentFactory.create_batch(3, related_user=user)
        
        url = reverse('documents:document-list')
        response = authenticated_client.get(url)
        
        assert response.status_code == 200
        assert_paginated_response(response.data, expected_count=3)
    
    def test_user_only_sees_own_documents(
        self, authenticated_client, user, other_user
    ):
        """Users only see their own documents."""
        DocumentFactory.create_batch(3, related_user=user)
        DocumentFactory.create_batch(2, related_user=other_user)
        
        url = reverse('documents:document-list')
        response = authenticated_client.get(url)
        
        assert response.status_code == 200
        assert_paginated_response(response.data, expected_count=3)
        
        for doc in response.data['results']:
            assert str(doc['related_user']) == str(user.id)
    
    def test_admin_sees_all_documents(
        self, admin_client, user, other_user
    ):
        """Admin users see all documents."""
        DocumentFactory.create_batch(3, related_user=user)
        DocumentFactory.create_batch(2, related_user=other_user)
        
        url = reverse('documents:document-list')
        response = admin_client.get(url)
        
        assert response.status_code == 200
        assert_paginated_response(response.data, expected_count=5)
    
    def test_empty_results(self, authenticated_client):
        """Empty queryset returns empty results array."""
        url = reverse('documents:document-list')
        response = authenticated_client.get(url)
        
        assert response.status_code == 200
        assert_paginated_response(response.data, expected_count=0)
        assert response.data['results'] == []
    
    def test_deleted_documents_excluded(self, authenticated_client, user):
        """Soft-deleted documents are excluded from list."""
        DocumentFactory.create_batch(2, related_user=user)
        DocumentFactory.create(related_user=user, is_deleted=True)
        
        url = reverse('documents:document-list')
        response = authenticated_client.get(url)
        
        assert response.status_code == 200
        assert_paginated_response(response.data, expected_count=2)
    
    def test_response_structure(self, authenticated_client, user):
        """Response items have correct structure."""
        CompletedDocumentFactory.create(related_user=user)
        
        url = reverse('documents:document-list')
        response = authenticated_client.get(url)
        
        assert response.status_code == 200
        assert len(response.data['results']) == 1
        
        assert_document_response_structure(
            response.data['results'][0],
            full=False
        )
    
    def test_ordering_by_created_at_desc(self, authenticated_client, user):
        """Documents are ordered by created_at descending by default."""
        doc1 = DocumentFactory.create(related_user=user, title="First")
        doc2 = DocumentFactory.create(related_user=user, title="Second")
        doc3 = DocumentFactory.create(related_user=user, title="Third")
        
        url = reverse('documents:document-list')
        response = authenticated_client.get(url)
        
        assert response.status_code == 200
        results = response.data['results']
        
        assert str(results[0]['id']) == str(doc3.id)
        assert str(results[1]['id']) == str(doc2.id)
        assert str(results[2]['id']) == str(doc1.id)
    
    def test_jwt_authentication(self, jwt_client, user):
        """JWT token authentication works."""
        DocumentFactory.create_batch(2, related_user=user)
        
        url = reverse('documents:document-list')
        response = jwt_client.get(url)
        
        assert response.status_code == 200
        assert_paginated_response(response.data, expected_count=2)


@pytest.mark.django_db
class TestDocumentDownloadListEndpoint:
    """Test GET /downloads/ endpoint."""
    
    def test_unauthenticated_user_cannot_list(self, api_client):
        """Unauthenticated requests return 401."""
        url = reverse('documents:document-download-list')
        response = api_client.get(url)
        
        assert response.status_code == 401
    
    def test_authenticated_user_can_list(self, authenticated_client, user):
        """Authenticated user can list downloads of their documents."""
        from .factories import DocumentDownloadFactory
        
        document = CompletedDocumentFactory.create(related_user=user)
        DocumentDownloadFactory.create_batch(3, document=document)
        
        url = reverse('documents:document-download-list')
        response = authenticated_client.get(url)
        
        assert response.status_code == 200
        assert_paginated_response(response.data, expected_count=3)
    
    def test_user_only_sees_own_document_downloads(
        self, authenticated_client, user, other_user
    ):
        """Users only see downloads of their own documents."""
        from .factories import DocumentDownloadFactory
        
        user_doc = CompletedDocumentFactory.create(related_user=user)
        other_doc = CompletedDocumentFactory.create(related_user=other_user)
        
        DocumentDownloadFactory.create_batch(2, document=user_doc)
        DocumentDownloadFactory.create_batch(3, document=other_doc)
        
        url = reverse('documents:document-download-list')
        response = authenticated_client.get(url)
        
        assert response.status_code == 200
        assert_paginated_response(response.data, expected_count=2)
    
    def test_admin_sees_all_downloads(self, admin_client, user, other_user):
        """Admin users see all download records."""
        from .factories import DocumentDownloadFactory
        
        user_doc = CompletedDocumentFactory.create(related_user=user)
        other_doc = CompletedDocumentFactory.create(related_user=other_user)
        
        DocumentDownloadFactory.create_batch(2, document=user_doc)
        DocumentDownloadFactory.create_batch(3, document=other_doc)
        
        url = reverse('documents:document-download-list')
        response = admin_client.get(url)
        
        assert response.status_code == 200
        assert_paginated_response(response.data, expected_count=5)
    
    def test_empty_results(self, authenticated_client):
        """Empty queryset returns empty results array."""
        url = reverse('documents:document-download-list')
        response = authenticated_client.get(url)
        
        assert response.status_code == 200
        assert_paginated_response(response.data, expected_count=0)
        assert response.data['results'] == []