
# tests/test_views_retrieve.py
"""
Tests for estate retrieve endpoint.

Coverage:
- Authentication/authorization
- Success paths
- Error cases (404)
- Response structure
"""

import pytest
import uuid
from .helpers import get_estate_detail_url
from .factories import EstateFactory


@pytest.mark.django_db
class TestEstateRetrieveEndpoint:
    """Test estate retrieve endpoint GET /estates/{id}/."""
    
    def test_unauthenticated_user_can_retrieve_estate(self, api_client, estate):
        """Test unauthenticated users can retrieve estate details."""
        url = get_estate_detail_url(estate.id)
        response = api_client.get(url)
        
        assert response.status_code == 200
        assert response.data['id'] == str(estate.id)
    
    def test_authenticated_user_can_retrieve_estate(self, authenticated_client, estate, api_client):
        """Test authenticated users can retrieve estate details."""
        url = get_estate_detail_url(estate.id)
        response = api_client.get(url)
        
        assert response.status_code == 200
        assert response.data['id'] == str(estate.id)
    
    def test_retrieve_returns_full_estate_details(self, authenticated_client, estate):
        """Test retrieve endpoint returns all estate fields."""
        url = get_estate_detail_url(estate.id)
        response = authenticated_client.get(url)
        
        assert response.status_code == 200
        
        expected_fields = {
            'id', 'name', 'estate_type', 'estate_type_display',
            'approximate_units', 'unit_count_display', 'fee_frequency',
            'fee_frequency_display', 'is_active', 'status_display',
            'description', 'address', 'created_at', 'updated_at'
        }
        
        assert set(response.data.keys()) == expected_fields
    
    def test_retrieve_inactive_estate(self, authenticated_client, inactive_estate):
        """Test retrieving inactive estate returns full details."""
        url = get_estate_detail_url(inactive_estate.id)
        response = authenticated_client.get(url)
        
        assert response.status_code == 200
        assert response.data['is_active'] is False
    
    def test_retrieve_nonexistent_estate_returns_404(self, authenticated_client):
        """Test retrieving non-existent estate returns 404."""
        fake_id = uuid.uuid4()
        url = get_estate_detail_url(fake_id)
        response = authenticated_client.get(url)
        
        assert response.status_code == 404
    
    def test_retrieve_with_invalid_uuid_returns_404(self, authenticated_client):
        """Test retrieving with invalid UUID returns 404."""
        url = get_estate_detail_url("invalid-uuid")
        response = authenticated_client.get(url)
        
        assert response.status_code == 404
    
    def test_retrieve_displays_computed_fields(self, authenticated_client):
        """Test retrieve displays computed/property fields correctly."""
        from estates.models import Estate
        
        estate = EstateFactory.create(
            estate_type=Estate.EstateType.GOVERNMENT,
            fee_frequency=Estate.FeeFrequency.YEARLY,
            approximate_units=100,
            is_active=True
        )
        
        url = get_estate_detail_url(estate.id)
        response = authenticated_client.get(url)
        
        assert response.status_code == 200
        assert response.data['estate_type_display'] == 'Government'
        assert response.data['fee_frequency_display'] == 'Yearly'
        assert response.data['unit_count_display'] == '~100 units'
        assert response.data['status_display'] == 'Active'

