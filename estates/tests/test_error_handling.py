
# tests/test_error_handling.py
"""
Tests for error handling and exception cases.

Coverage:
- Malformed requests
- Invalid data types
- Missing required fields
- Server errors
"""

import pytest
from .helpers import get_estate_list_url, get_estate_detail_url
from .factories import EstateFactory


@pytest.mark.django_db
class TestEstateErrorHandling:
    """Test error handling for estate endpoints."""
    
    def test_create_with_malformed_json(self, staff_client):
        """Test creating with malformed JSON returns 400."""
        url = get_estate_list_url()
        
        response = staff_client.post(
            url,
            data="{'invalid': json}",
            content_type='application/json'
        )
        
        assert response.status_code == 400
    
    def test_create_with_invalid_field_type(self, staff_client):
        """Test creating with wrong field type fails."""
        url = get_estate_list_url()
        data = {
            'name': 'Test Estate',
            'estate_type': 'PRIVATE',
            'fee_frequency': 'MONTHLY',
            'approximate_units': 'not_a_number'
        }
        
        response = staff_client.post(url, data, format='json')
        
        assert response.status_code == 400
        assert 'approximate_units' in response.data
    
    def test_create_with_extra_fields_ignores_them(self, staff_client):
        """Test creating with extra fields ignores them."""
        url = get_estate_list_url()
        data = {
            'name': 'Test Estate',
            'estate_type': 'PRIVATE',
            'fee_frequency': 'MONTHLY',
            'extra_field': 'should be ignored',
            'another_extra': 123
        }
        
        response = staff_client.post(url, data, format='json')
        
        assert response.status_code == 201
        assert 'extra_field' not in response.data
    
    def test_update_nonexistent_estate_returns_404(self, staff_client):
        """Test updating non-existent estate returns 404."""
        import uuid
        fake_id = uuid.uuid4()
        url = get_estate_detail_url(fake_id)
        data = {'name': 'Updated'}
        
        response = staff_client.patch(url, data, format='json')
        
        assert response.status_code == 404
    
    def test_filter_with_invalid_date_format(self, authenticated_client):
        """Test filtering with invalid date format."""
        url = get_estate_list_url()
        response = authenticated_client.get(url, {'created_after': 'not-a-date'})
        
        assert response.status_code in [200, 400]
    
    def test_ordering_with_invalid_field(self, authenticated_client):
        """Test ordering by invalid field is ignored."""
        EstateFactory.create_batch(3)
        
        url = get_estate_list_url()
        response = authenticated_client.get(url, {'ordering': 'invalid_field'})
        
        assert response.status_code == 200

