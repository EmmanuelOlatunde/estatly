

# tests/test_views_list.py
"""
Tests for estate list endpoint.

Coverage:
- Authentication/authorization
- Success paths
- Filtering
- Searching
- Ordering
- Pagination
"""

import pytest
from .helpers import get_estate_list_url
from .factories import EstateFactory
from estates.models import Estate


@pytest.mark.django_db
class TestEstateListEndpoint:
    """Test estate list endpoint GET /estates/."""
    
    def test_unauthenticated_user_can_access_list(self, api_client, estates):
        """Test unauthenticated users can view estate list (read-only)."""
        url = get_estate_list_url()
        response = api_client.get(url)
        
        assert response.status_code == 200
    
    def test_authenticated_user_can_access_list(self, authenticated_client, estates):
        """Test authenticated users can view estate list."""
        url = get_estate_list_url()
        response = authenticated_client.get(url)
        
        assert response.status_code == 200
        assert 'results' in response.data
    
    def test_list_returns_only_active_estates_by_default(self, authenticated_client):
        """Test list endpoint returns only active estates by default."""
        active_estates = EstateFactory.create_batch(3, is_active=True)  # noqa: F841
        inactive_estates = EstateFactory.create_batch(2, is_active=False)  # noqa: F841
        
        url = get_estate_list_url()
        response = authenticated_client.get(url)
        
        assert response.status_code == 200
        assert len(response.data['results']) == 3
    
    def test_list_includes_inactive_when_filtered(self, authenticated_client):
        """Test list includes inactive estates when explicitly filtered."""
        EstateFactory.create_batch(2, is_active=True)
        inactive = EstateFactory.create(is_active=False)
        
        url = get_estate_list_url()
        response = authenticated_client.get(url, {'is_active': 'false'})
        
        assert response.status_code == 200
        assert len(response.data['results']) == 1
        assert response.data['results'][0]['id'] == str(inactive.id)
    
    def test_list_empty_when_no_estates_exist(self, authenticated_client):
        """Test list returns empty array when no estates exist."""
        url = get_estate_list_url()
        response = authenticated_client.get(url)
        
        assert response.status_code == 200
        assert response.data['results'] == []
        assert response.data['count'] == 0
    
    def test_list_response_structure(self, authenticated_client, estate):
        """Test list response has correct structure."""
        url = get_estate_list_url()
        response = authenticated_client.get(url)
        
        assert response.status_code == 200
        assert 'count' in response.data
        assert 'next' in response.data
        assert 'previous' in response.data
        assert 'results' in response.data
        assert isinstance(response.data['results'], list)
    
    def test_list_estate_fields(self, authenticated_client, estate):
        """Test list response contains expected estate fields."""
        url = get_estate_list_url()
        response = authenticated_client.get(url)
        
        assert response.status_code == 200
        estate_data = response.data['results'][0]
        
        expected_fields = {
            'id', 'name', 'estate_type', 'estate_type_display',
            'approximate_units', 'is_active', 'status_display', 'created_at'
        }
        
        assert set(estate_data.keys()) == expected_fields


@pytest.mark.django_db
class TestEstateListFiltering:
    """Test estate list filtering capabilities."""
    
    def test_filter_by_name_contains(self, authenticated_client):
        """Test filtering estates by name (case-insensitive contains)."""
        estate1 = EstateFactory.create(name="Sunshine Estate")
        estate2 = EstateFactory.create(name="Moonlight Estate")
        estate3 = EstateFactory.create(name="Star Complex")
        
        url = get_estate_list_url()
        response = authenticated_client.get(url, {'name': 'estate'})
        
        assert response.status_code == 200
        assert len(response.data['results']) == 2
    
    def test_filter_by_estate_type(self, authenticated_client):
        """Test filtering estates by type."""
        private_estates = EstateFactory.create_batch(2, estate_type=Estate.EstateType.PRIVATE)
        gov_estates = EstateFactory.create_batch(3, estate_type=Estate.EstateType.GOVERNMENT)
        
        url = get_estate_list_url()
        response = authenticated_client.get(url, {'estate_type': 'PRIVATE'})
        
        assert response.status_code == 200
        assert len(response.data['results']) == 2
    
    def test_filter_by_fee_frequency(self, authenticated_client):
        """Test filtering estates by fee frequency."""
        monthly = EstateFactory.create_batch(2, fee_frequency=Estate.FeeFrequency.MONTHLY)
        yearly = EstateFactory.create(fee_frequency=Estate.FeeFrequency.YEARLY)
        
        url = get_estate_list_url()
        response = authenticated_client.get(url, {'fee_frequency': 'MONTHLY'})
        
        assert response.status_code == 200
        assert len(response.data['results']) == 2
    
    def test_filter_by_min_units(self, authenticated_client):
        """Test filtering estates by minimum units."""
        estate1 = EstateFactory.create(approximate_units=50)
        estate2 = EstateFactory.create(approximate_units=100)
        estate3 = EstateFactory.create(approximate_units=150)
        
        url = get_estate_list_url()
        response = authenticated_client.get(url, {'min_units': '100'})
        
        assert response.status_code == 200
        assert len(response.data['results']) == 2
    
    def test_filter_by_max_units(self, authenticated_client):
        """Test filtering estates by maximum units."""
        estate1 = EstateFactory.create(approximate_units=50)
        estate2 = EstateFactory.create(approximate_units=100)
        estate3 = EstateFactory.create(approximate_units=150)
        
        url = get_estate_list_url()
        response = authenticated_client.get(url, {'max_units': '100'})
        
        assert response.status_code == 200
        assert len(response.data['results']) == 2
    
    def test_filter_by_multiple_parameters(self, authenticated_client):
        """Test filtering with multiple parameters combined."""
        estate1 = EstateFactory.create(
            estate_type=Estate.EstateType.PRIVATE,
            fee_frequency=Estate.FeeFrequency.MONTHLY,
            is_active=True
        )
        estate2 = EstateFactory.create(
            estate_type=Estate.EstateType.PRIVATE,
            fee_frequency=Estate.FeeFrequency.YEARLY,
            is_active=True
        )
        estate3 = EstateFactory.create(
            estate_type=Estate.EstateType.GOVERNMENT,
            fee_frequency=Estate.FeeFrequency.MONTHLY,
            is_active=True
        )
        
        url = get_estate_list_url()
        response = authenticated_client.get(url, {
            'estate_type': 'PRIVATE',
            'fee_frequency': 'MONTHLY'
        })
        
        assert response.status_code == 200
        assert len(response.data['results']) == 1
        assert response.data['results'][0]['id'] == str(estate1.id)


@pytest.mark.django_db
class TestEstateListSearch:
    """Test estate list search functionality."""
    
    def test_search_by_name(self, authenticated_client):
        """Test searching estates by name."""
        estate1 = EstateFactory.create(name="Paradise Gardens")
        estate2 = EstateFactory.create(name="Garden View Estate")
        estate3 = EstateFactory.create(name="Mountain Heights")
        
        url = get_estate_list_url()
        response = authenticated_client.get(url, {'search': 'garden'})
        
        assert response.status_code == 200
        assert len(response.data['results']) == 2
    
    def test_search_by_description(self, authenticated_client):
        """Test searching estates by description."""
        estate1 = EstateFactory.create(
            name="Estate A",
            description="Luxury living with pool"
        )
        estate2 = EstateFactory.create(
            name="Estate B",
            description="Affordable housing"
        )
        
        url = get_estate_list_url()
        response = authenticated_client.get(url, {'search': 'luxury'})
        
        assert response.status_code == 200
        assert len(response.data['results']) == 1
        assert response.data['results'][0]['id'] == str(estate1.id)
    
    def test_search_by_address(self, authenticated_client):
        """Test searching estates by address."""
        estate1 = EstateFactory.create(
            name="Estate A",
            address="123 Main Street, Lagos"
        )
        estate2 = EstateFactory.create(
            name="Estate B",
            address="456 Beach Road, Abuja"
        )
        
        url = get_estate_list_url()
        response = authenticated_client.get(url, {'search': 'lagos'})
        
        assert response.status_code == 200
        assert len(response.data['results']) == 1
        assert response.data['results'][0]['id'] == str(estate1.id)
    
    def test_search_case_insensitive(self, authenticated_client):
        """Test search is case-insensitive."""
        estate = EstateFactory.create(name="Paradise Estate")
        
        url = get_estate_list_url()
        response1 = authenticated_client.get(url, {'search': 'PARADISE'})
        response2 = authenticated_client.get(url, {'search': 'paradise'})
        response3 = authenticated_client.get(url, {'search': 'Paradise'})
        
        assert response1.status_code == 200
        assert response2.status_code == 200
        assert response3.status_code == 200
        assert len(response1.data['results']) == 1
        assert len(response2.data['results']) == 1
        assert len(response3.data['results']) == 1


@pytest.mark.django_db
class TestEstateListOrdering:
    """Test estate list ordering functionality."""
    
    def test_default_ordering_by_created_at_desc(self, authenticated_client):
        """Test default ordering is by created_at descending."""
        import time
        
        estate1 = EstateFactory.create(name="First")
        time.sleep(0.01)
        estate2 = EstateFactory.create(name="Second")
        time.sleep(0.01)
        estate3 = EstateFactory.create(name="Third")
        
        url = get_estate_list_url()
        response = authenticated_client.get(url)
        
        assert response.status_code == 200
        results = response.data['results']
        assert results[0]['name'] == "Third"
        assert results[1]['name'] == "Second"
        assert results[2]['name'] == "First"
    
    def test_ordering_by_name_ascending(self, authenticated_client):
        """Test ordering by name ascending."""
        EstateFactory.create(name="Zebra Estate")
        EstateFactory.create(name="Apple Estate")
        EstateFactory.create(name="Mountain Estate")
        
        url = get_estate_list_url()
        response = authenticated_client.get(url, {'ordering': 'name'})
        
        assert response.status_code == 200
        results = response.data['results']
        assert results[0]['name'] == "Apple Estate"
        assert results[1]['name'] == "Mountain Estate"
        assert results[2]['name'] == "Zebra Estate"
    
    def test_ordering_by_name_descending(self, authenticated_client):
        """Test ordering by name descending."""
        EstateFactory.create(name="Zebra Estate")
        EstateFactory.create(name="Apple Estate")
        EstateFactory.create(name="Mountain Estate")
        
        url = get_estate_list_url()
        response = authenticated_client.get(url, {'ordering': '-name'})
        
        assert response.status_code == 200
        results = response.data['results']
        assert results[0]['name'] == "Zebra Estate"
        assert results[1]['name'] == "Mountain Estate"
        assert results[2]['name'] == "Apple Estate"
    
    def test_ordering_by_approximate_units(self, authenticated_client):
        """Test ordering by approximate_units."""
        EstateFactory.create(name="Large", approximate_units=500)
        EstateFactory.create(name="Small", approximate_units=50)
        EstateFactory.create(name="Medium", approximate_units=200)
        
        url = get_estate_list_url()
        response = authenticated_client.get(url, {'ordering': 'approximate_units'})
        
        assert response.status_code == 200
        results = response.data['results']
        assert results[0]['name'] == "Small"
        assert results[1]['name'] == "Medium"
        assert results[2]['name'] == "Large"





