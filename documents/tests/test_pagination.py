# tests/test_pagination.py
"""
Tests for pagination functionality.

Coverage:
- Page navigation
- Page size control
- Edge cases (empty, single page, etc.)
"""

import pytest
from django.urls import reverse
from .factories import DocumentFactory


@pytest.mark.django_db
class TestDocumentPagination:
    """Test pagination on document list endpoint."""
    
    def test_default_page_size(self, authenticated_client, user):
        """Default page size is 20."""
        DocumentFactory.create_batch(25, related_user=user)
        
        url = reverse('documents:document-list')
        response = authenticated_client.get(url)
        
        assert response.status_code == 200
        assert len(response.data['results']) == 20
        assert response.data['count'] == 25
    
    def test_first_page_has_next(self, authenticated_client, user):
        """First page includes next link when more pages exist."""
        DocumentFactory.create_batch(25, related_user=user)
        
        url = reverse('documents:document-list')
        response = authenticated_client.get(url)
        
        assert response.status_code == 200
        assert response.data['next'] is not None
        assert response.data['previous'] is None
    
    def test_second_page_navigation(self, authenticated_client, user):
        """Second page has both next and previous links."""
        DocumentFactory.create_batch(50, related_user=user)
        
        url = reverse('documents:document-list')
        response = authenticated_client.get(url, {'page': 2})
        
        assert response.status_code == 200
        assert len(response.data['results']) == 20
        assert response.data['next'] is not None
        assert response.data['previous'] is not None
    
    def test_last_page_no_next(self, authenticated_client, user):
        """Last page has no next link."""
        DocumentFactory.create_batch(25, related_user=user)
        
        url = reverse('documents:document-list')
        response = authenticated_client.get(url, {'page': 2})
        
        assert response.status_code == 200
        assert len(response.data['results']) == 5
        assert response.data['next'] is None
        assert response.data['previous'] is not None
    
    def test_custom_page_size(self, authenticated_client, user):
        """Custom page_size parameter works."""
        DocumentFactory.create_batch(15, related_user=user)
        
        url = reverse('documents:document-list')
        response = authenticated_client.get(url, {'page_size': 5})
        
        assert response.status_code == 200
        assert len(response.data['results']) == 5
        assert response.data['count'] == 15
    
    def test_page_size_maximum_limit(self, authenticated_client, user):
        """Page size cannot exceed maximum of 100."""
        DocumentFactory.create_batch(150, related_user=user)
        
        url = reverse('documents:document-list')
        response = authenticated_client.get(url, {'page_size': 200})
        
        assert response.status_code == 200
        assert len(response.data['results']) <= 100
    
    def test_invalid_page_number(self, authenticated_client, user):
        """Invalid page number returns 404."""
        DocumentFactory.create_batch(10, related_user=user)
        
        url = reverse('documents:document-list')
        response = authenticated_client.get(url, {'page': 999})
        
        assert response.status_code == 404
    
    def test_page_zero_invalid(self, authenticated_client, user):
        """Page 0 is invalid."""
        DocumentFactory.create_batch(10, related_user=user)
        
        url = reverse('documents:document-list')
        response = authenticated_client.get(url, {'page': 0})
        
        assert response.status_code == 404
    
    def test_negative_page_invalid(self, authenticated_client, user):
        """Negative page numbers are invalid."""
        DocumentFactory.create_batch(10, related_user=user)
        
        url = reverse('documents:document-list')
        response = authenticated_client.get(url, {'page': -1})
        
        assert response.status_code == 404
    
    def test_non_numeric_page_invalid(self, authenticated_client, user):
        """Non-numeric page values are invalid."""
        DocumentFactory.create_batch(10, related_user=user)
        
        url = reverse('documents:document-list')
        response = authenticated_client.get(url, {'page': 'invalid'})
        
        assert response.status_code == 404
    
    def test_single_page_results(self, authenticated_client, user):
        """Single page has no next or previous."""
        DocumentFactory.create_batch(5, related_user=user)
        
        url = reverse('documents:document-list')
        response = authenticated_client.get(url)
        
        assert response.status_code == 200
        assert len(response.data['results']) == 5
        assert response.data['next'] is None
        assert response.data['previous'] is None
    
    def test_empty_page(self, authenticated_client):
        """Empty results return properly paginated response."""
        url = reverse('documents:document-list')
        response = authenticated_client.get(url)
        
        assert response.status_code == 200
        assert response.data['count'] == 0
        assert len(response.data['results']) == 0
        assert response.data['next'] is None
        assert response.data['previous'] is None
    
    def test_page_size_one(self, authenticated_client, user):
        """Page size of 1 works correctly."""
        DocumentFactory.create_batch(3, related_user=user)
        
        url = reverse('documents:document-list')
        response = authenticated_client.get(url, {'page_size': 1})
        
        assert response.status_code == 200
        assert len(response.data['results']) == 1
        assert response.data['count'] == 3
    
    def test_pagination_count_accurate(self, authenticated_client, user):
        """Count field accurately reflects total results."""
        DocumentFactory.create_batch(37, related_user=user)
        
        url = reverse('documents:document-list')
        response = authenticated_client.get(url)
        
        assert response.status_code == 200
        assert response.data['count'] == 37
    
    def test_pagination_with_filters(self, authenticated_client, user):
        """Pagination works with filters applied."""
        from documents.models import DocumentStatus
        
        DocumentFactory.create_batch(
            15,
            related_user=user,
            status=DocumentStatus.COMPLETED
        )
        DocumentFactory.create_batch(
            10,
            related_user=user,
            status=DocumentStatus.PENDING
        )
        
        url = reverse('documents:document-list')
        response = authenticated_client.get(
            url,
            {'status': 'completed', 'page_size': 10}
        )
        
        assert response.status_code == 200
        assert len(response.data['results']) == 10
        assert response.data['count'] == 15