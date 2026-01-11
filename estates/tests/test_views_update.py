

# tests/test_views_update.py
"""
Tests for estate update endpoints.

Coverage:
- Authentication/authorization
- PUT (full update)
- PATCH (partial update)
- Validation errors
"""

import pytest
from .helpers import get_estate_detail_url


@pytest.mark.django_db
class TestEstateUpdateEndpoint:
    """Test estate update endpoints PUT/PATCH /estates/{id}/."""
    
    def test_unauthenticated_user_cannot_update_estate(self, api_client, estate):
        """Test unauthenticated users cannot update estates."""
        url = get_estate_detail_url(estate.id)
        data = {'name': 'Updated Name'}
        
        response = api_client.patch(url, data, format='json')
        assert response.status_code == 401
    
    def test_non_staff_user_cannot_update_estate(self, authenticated_client, estate):
        """Test non-staff users cannot update estates."""
        url = get_estate_detail_url(estate.id)
        data = {'name': 'Updated Name'}
        
        response = authenticated_client.patch(url, data, format='json')
        assert response.status_code == 403
    
    def test_staff_user_can_update_estate(self, staff_client, estate):
        """Test staff users can update estates."""
        url = get_estate_detail_url(estate.id)
        data = {'name': 'Updated Estate Name'}
        
        response = staff_client.patch(url, data, format='json')
        
        assert response.status_code == 200
        assert response.data['name'] == 'Updated Estate Name'
    
    def test_admin_user_can_update_estate(self, admin_client, estate):
        """Test admin users can update estates."""
        url = get_estate_detail_url(estate.id)
        data = {'name': 'Admin Updated'}
        
        response = admin_client.patch(url, data, format='json')
        
        assert response.status_code == 200
        assert response.data['name'] == 'Admin Updated'
    
    def test_partial_update_single_field(self, staff_client, estate):
        """Test PATCH updates only specified fields."""
        original_type = estate.estate_type
        original_frequency = estate.fee_frequency
        
        url = get_estate_detail_url(estate.id)
        data = {'name': 'Partially Updated'}
        
        response = staff_client.patch(url, data, format='json')
        
        assert response.status_code == 200
        estate.refresh_from_db()
        assert estate.name == 'Partially Updated'
        assert estate.estate_type == original_type
        assert estate.fee_frequency == original_frequency
    
    def test_partial_update_multiple_fields(self, staff_client, estate):
        """Test PATCH can update multiple fields."""
        url = get_estate_detail_url(estate.id)
        data = {
            'name': 'Multi Update',
            'approximate_units': 250,
            'description': 'New description'
        }
        
        response = staff_client.patch(url, data, format='json')
        
        assert response.status_code == 200
        estate.refresh_from_db()
        assert estate.name == 'Multi Update'
        assert estate.approximate_units == 250
        assert estate.description == 'New description'
    
    def test_full_update_with_put(self, staff_client, estate):
        """Test PUT requires all fields."""
        url = get_estate_detail_url(estate.id)
        data = {
            'name': 'Full Update',
            'estate_type': 'GOVERNMENT',
            'fee_frequency': 'YEARLY',
            'approximate_units': 300,
            'is_active': True,
            'description': 'Updated description',
            'address': 'Updated address'
        }
        
        response = staff_client.put(url, data, format='json')
        
        assert response.status_code == 200
        estate.refresh_from_db()
        assert estate.name == 'Full Update'
        assert estate.estate_type == 'GOVERNMENT'
    
    def test_update_saves_to_database(self, staff_client, estate):
        """Test update actually persists to database."""
        url = get_estate_detail_url(estate.id)
        data = {'name': 'Persisted Update'}
        
        response = staff_client.patch(url, data, format='json')
        
        assert response.status_code == 200
        estate.refresh_from_db()
        assert estate.name == 'Persisted Update'
    
    def test_update_updates_timestamp(self, staff_client, estate):
        """Test update modifies updated_at timestamp."""
        import time
        
        original_updated_at = estate.updated_at
        time.sleep(0.01)
        
        url = get_estate_detail_url(estate.id)
        data = {'name': 'Timestamp Test'}
        
        response = staff_client.patch(url, data, format='json')
        
        assert response.status_code == 200
        estate.refresh_from_db()
        assert estate.updated_at > original_updated_at


@pytest.mark.django_db
class TestEstateUpdateValidation:
    """Test validation rules for estate updates."""
    
    def test_update_with_empty_name_fails(self, staff_client, estate):
        """Test updating with empty name fails."""
        url = get_estate_detail_url(estate.id)
        data = {'name': ''}
        
        response = staff_client.patch(url, data, format='json')
        
        assert response.status_code == 400
        assert 'name' in response.data
    
    def test_update_with_whitespace_name_fails(self, staff_client, estate):
        """Test updating with whitespace-only name fails."""
        url = get_estate_detail_url(estate.id)
        data = {'name': '   '}
        
        response = staff_client.patch(url, data, format='json')
        
        assert response.status_code == 400
        assert 'name' in response.data
    
    def test_update_with_invalid_estate_type_fails(self, staff_client, estate):
        """Test updating with invalid estate_type fails."""
        url = get_estate_detail_url(estate.id)
        data = {'estate_type': 'INVALID'}
        
        response = staff_client.patch(url, data, format='json')
        
        assert response.status_code == 400
        assert 'estate_type' in response.data
    
    def test_update_with_invalid_fee_frequency_fails(self, staff_client, estate):
        """Test updating with invalid fee_frequency fails."""
        url = get_estate_detail_url(estate.id)
        data = {'fee_frequency': 'WEEKLY'}
        
        response = staff_client.patch(url, data, format='json')
        
        assert response.status_code == 400
        assert 'fee_frequency' in response.data
    
    def test_update_with_zero_units_fails(self, staff_client, estate):
        """Test updating with zero units fails."""
        url = get_estate_detail_url(estate.id)
        data = {'approximate_units': 0}
        
        response = staff_client.patch(url, data, format='json')
        
        assert response.status_code == 400
        assert 'approximate_units' in response.data
    
    def test_update_with_negative_units_fails(self, staff_client, estate):
        """Test updating with negative units fails."""
        url = get_estate_detail_url(estate.id)
        data = {'approximate_units': -50}
        
        response = staff_client.patch(url, data, format='json')
        
        assert response.status_code == 400
        assert 'approximate_units' in response.data
    
    def test_update_name_strips_whitespace(self, staff_client, estate):
        """Test name update strips whitespace."""
        url = get_estate_detail_url(estate.id)
        data = {'name': '  Trimmed Update  '}
        
        response = staff_client.patch(url, data, format='json')
        
        assert response.status_code == 200
        estate.refresh_from_db()
        assert estate.name == 'Trimmed Update'
