
# tests/test_edge_cases.py
"""
Tests for edge cases and boundary conditions.

Coverage:
- Boundary values
- Special characters
- Unicode handling
- Concurrent operations
"""

import pytest
from .helpers import get_estate_list_url, get_estate_detail_url
from .factories import EstateFactory
# from estates.models import Estate


@pytest.mark.django_db
class TestEstateEdgeCases:
    """Test edge cases for estate operations."""
    
    def test_create_with_very_long_name(self, staff_client):
        """Test creating estate with name near max_length."""
        long_name = "A" * 255
        
        url = get_estate_list_url()
        data = {
            'name': long_name,
            'estate_type': 'PRIVATE',
            'fee_frequency': 'MONTHLY'
        }
        
        response = staff_client.post(url, data, format='json')
        
        assert response.status_code == 201
        assert len(response.data['name']) == 255
    
    def test_create_with_name_exceeding_max_length(self, staff_client):
        """Test creating estate with name exceeding max_length fails."""
        too_long_name = "A" * 256
        
        url = get_estate_list_url()
        data = {
            'name': too_long_name,
            'estate_type': 'PRIVATE',
            'fee_frequency': 'MONTHLY'
        }
        
        response = staff_client.post(url, data, format='json')
        
        assert response.status_code == 400
        assert 'name' in response.data
    
    def test_create_with_unicode_characters(self, staff_client):
        """Test creating estate with unicode characters in name."""
        unicode_name = "Estate 测试 العقارات"
        
        url = get_estate_list_url()
        data = {
            'name': unicode_name,
            'estate_type': 'PRIVATE',
            'fee_frequency': 'MONTHLY'
        }
        
        response = staff_client.post(url, data, format='json')
        
        assert response.status_code == 201
        assert response.data['name'] == unicode_name
    
    def test_create_with_special_characters(self, staff_client):
        """Test creating estate with special characters."""
        special_name = "Estate & Co. (2024) - #1 Choice!"
        
        url = get_estate_list_url()
        data = {
            'name': special_name,
            'estate_type': 'PRIVATE',
            'fee_frequency': 'MONTHLY'
        }
        
        response = staff_client.post(url, data, format='json')
        
        assert response.status_code == 201
        assert response.data['name'] == special_name
    
    def test_create_with_max_integer_units(self, staff_client):
        """Test creating estate with very large unit count."""
        url = get_estate_list_url()
        data = {
            'name': 'Large Estate',
            'estate_type': 'PRIVATE',
            'fee_frequency': 'MONTHLY',
            'approximate_units': 2147483647
        }
        
        response = staff_client.post(url, data, format='json')
        
        assert response.status_code == 201
    
    def test_search_with_empty_string(self, authenticated_client):
        """Test searching with empty string returns all."""
        EstateFactory.create_batch(5)
        
        url = get_estate_list_url()
        response = authenticated_client.get(url, {'search': ''})
        
        assert response.status_code == 200
        assert len(response.data['results']) == 5
    
    def test_filter_with_invalid_boolean(self, authenticated_client):
        """Test filtering with invalid boolean value."""
        EstateFactory.create_batch(3)
        
        url = get_estate_list_url()
        response = authenticated_client.get(url, {'is_active': 'invalid'})
        
        assert response.status_code == 200
    
    def test_retrieve_with_trailing_slash(self, authenticated_client, estate):
        """Test retrieve works with and without trailing slash."""
        url_with_slash = get_estate_detail_url(estate.id)
        url_without_slash = url_with_slash.rstrip('/')
        
        response1 = authenticated_client.get(url_with_slash)
        response2 = authenticated_client.get(url_without_slash)
        
        assert response1.status_code == 200
        assert response2.status_code in [200, 301]

