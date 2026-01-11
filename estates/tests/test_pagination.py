
# tests/test_pagination.py
"""
Tests for estate pagination.

Coverage:
- Default pagination
- Page size limits
- Page navigation
- Edge cases
"""

import pytest
from .helpers import get_estate_list_url
from .factories import EstateFactory
from estates.models import Estate


@pytest.mark.django_db
class TestEstatePagination:
    """Test estate list pagination."""
    
    def test_pagination_response_structure(self, authenticated_client):
        """Test pagination includes required fields."""
        EstateFactory.create_batch(5)
        
        url = get_estate_list_url()
        response = authenticated_client.get(url)
        
        assert response.status_code == 200
        assert 'count' in response.data
        assert 'next' in response.data
        assert 'previous' in response.data
        assert 'results' in response.data
    
    def test_pagination_count_correct(self, authenticated_client):
        """Test pagination count matches total estates."""
        EstateFactory.create_batch(15)
        
        url = get_estate_list_url()
        response = authenticated_client.get(url)
        
        assert response.status_code == 200
        assert response.data['count'] == 15
    
    def test_pagination_first_page(self, authenticated_client):
        """Test first page pagination."""
        EstateFactory.create_batch(25)
        
        url = get_estate_list_url()
        response = authenticated_client.get(url, {'page': '1'})
        
        assert response.status_code == 200
        assert response.data['previous'] is None
        assert response.data['next'] is not None
    
    def test_pagination_last_page(self, authenticated_client):
        """Test last page pagination."""
        EstateFactory.create_batch(25)
        
        url = get_estate_list_url()
        response = authenticated_client.get(url, {'page': '3'})
        
        assert response.status_code == 200
        assert response.data['next'] is None
        assert response.data['previous'] is not None
    
    def test_pagination_invalid_page(self, authenticated_client):
        """Test invalid page number returns 404."""
        EstateFactory.create_batch(10)
        
        url = get_estate_list_url()
        response = authenticated_client.get(url, {'page': '999'})
        
        assert response.status_code == 404
    
    def test_pagination_with_filters(self, authenticated_client):
        """Test pagination works with filters."""
        EstateFactory.create_batch(30, estate_type=Estate.EstateType.PRIVATE)
        
        url = get_estate_list_url()
        response = authenticated_client.get(url, {
            'estate_type': 'PRIVATE',
            'page': '1'
        })
        
        assert response.status_code == 200
        assert response.data['count'] == 30
