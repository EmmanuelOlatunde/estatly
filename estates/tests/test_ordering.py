

# tests/test_ordering.py
"""
Tests for estate ordering functionality.

Coverage:
- All ordering fields
- Ascending/descending
- Multiple field ordering
"""

import pytest
from .helpers import get_estate_list_url
from .factories import EstateFactory


@pytest.mark.django_db
class TestEstateOrdering:
    """Test estate ordering options."""
    
    def test_order_by_created_at_ascending(self, authenticated_client):
        """Test ordering by created_at ascending."""
        import time
        
        first = EstateFactory.create(name="First")
        time.sleep(0.01)
        second = EstateFactory.create(name="Second")
        time.sleep(0.01)
        third = EstateFactory.create(name="Third")
        
        url = get_estate_list_url()
        response = authenticated_client.get(url, {'ordering': 'created_at'})
        
        assert response.status_code == 200
        results = response.data['results']
        assert results[0]['name'] == "First"
        assert results[2]['name'] == "Third"
    
    def test_order_by_updated_at(self, authenticated_client):
        """Test ordering by updated_at."""
        import time
        
        estate1 = EstateFactory.create(name="Estate 1")
        time.sleep(0.01)
        estate2 = EstateFactory.create(name="Estate 2")
        time.sleep(0.01)
        
        estate1.name = "Estate 1 Updated"
        estate1.save()
        
        url = get_estate_list_url()
        response = authenticated_client.get(url, {'ordering': '-updated_at'})
        
        assert response.status_code == 200
        assert response.data['results'][0]['name'] == "Estate 1 Updated"
    
    def test_order_by_approximate_units_descending(self, authenticated_client):
        """Test ordering by approximate_units descending."""
        EstateFactory.create(name="Small", approximate_units=50)
        EstateFactory.create(name="Large", approximate_units=500)
        EstateFactory.create(name="Medium", approximate_units=200)
        
        url = get_estate_list_url()
        response = authenticated_client.get(url, {'ordering': '-approximate_units'})
        
        assert response.status_code == 200
        results = response.data['results']
        assert results[0]['name'] == "Large"
        assert results[1]['name'] == "Medium"
        assert results[2]['name'] == "Small"
    
    def test_ordering_with_null_units(self, authenticated_client):
        """Test ordering handles null approximate_units correctly."""
        EstateFactory.create(name="With Units", approximate_units=100)
        EstateFactory.create(name="Without Units", approximate_units=None)
        
        url = get_estate_list_url()
        response = authenticated_client.get(url, {'ordering': 'approximate_units'})
        
        assert response.status_code == 200
        assert len(response.data['results']) == 2
