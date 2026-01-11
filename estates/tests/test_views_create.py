

# tests/test_views_create.py
"""
Tests for estate create endpoint.

Coverage:
- Authentication/authorization
- Success paths
- Validation errors
- Field requirements
"""

import pytest
from .helpers import get_estate_list_url
from estates.models import Estate


@pytest.mark.django_db
class TestEstateCreateEndpoint:
    """Test estate create endpoint POST /estates/."""
    
    def test_unauthenticated_user_cannot_create_estate(self, api_client):
        """Test unauthenticated users cannot create estates."""
        url = get_estate_list_url()
        data = {
            'name': 'Test Estate',
            'estate_type': 'PRIVATE',
            'fee_frequency': 'MONTHLY'
        }
        
        response = api_client.post(url, data, format='json')
        assert response.status_code == 401
    
    def test_non_staff_user_cannot_create_estate(self, authenticated_client):
        """Test non-staff authenticated users cannot create estates."""
        url = get_estate_list_url()
        data = {
            'name': 'Test Estate',
            'estate_type': 'PRIVATE',
            'fee_frequency': 'MONTHLY'
        }
        
        response = authenticated_client.post(url, data, format='json')
        assert response.status_code == 403
    
    def test_staff_user_can_create_estate(self, staff_client):
        """Test staff users can create estates."""
        url = get_estate_list_url()
        data = {
            'name': 'New Estate',
            'estate_type': 'PRIVATE',
            'approximate_units': 100,
            'fee_frequency': 'MONTHLY',
            'is_active': True,
            'description': 'A beautiful estate',
            'address': '123 Test Street'
        }
        
        response = staff_client.post(url, data, format='json')
        
        assert response.status_code == 201
        assert response.data['name'] == 'New Estate'
        assert response.data['estate_type'] == 'PRIVATE'
        assert response.data['approximate_units'] == 100
    
    def test_admin_user_can_create_estate(self, admin_client):
        """Test admin users can create estates."""
        url = get_estate_list_url()
        data = {
            'name': 'Admin Estate',
            'estate_type': 'GOVERNMENT',
            'fee_frequency': 'YEARLY'
        }
        
        response = admin_client.post(url, data, format='json')
        
        assert response.status_code == 201
        assert response.data['name'] == 'Admin Estate'
    
    def test_create_with_minimal_required_fields(self, staff_client):
        """Test creating estate with only required fields."""
        url = get_estate_list_url()
        data = {
            'name': 'Minimal Estate',
            'estate_type': 'PRIVATE',
            'fee_frequency': 'MONTHLY'
        }
        
        response = staff_client.post(url, data, format='json')
        
        assert response.status_code == 201
        assert Estate.objects.filter(name='Minimal Estate').exists()
    
    def test_create_estate_saved_in_database(self, staff_client):
        """Test created estate is actually saved in database."""
        url = get_estate_list_url()
        data = {
            'name': 'Database Test',
            'estate_type': 'GOVERNMENT',
            'fee_frequency': 'MONTHLY'
        }
        
        initial_count = Estate.objects.count()
        response = staff_client.post(url, data, format='json')
        
        assert response.status_code == 201
        assert Estate.objects.count() == initial_count + 1
        
        estate = Estate.objects.get(id=response.data['id'])
        assert estate.name == 'Database Test'
        assert estate.estate_type == 'GOVERNMENT'
    
    def test_create_sets_default_values(self, staff_client):
        """Test create sets appropriate default values."""
        url = get_estate_list_url()
        data = {
            'name': 'Default Test',
            'estate_type': 'PRIVATE',
            'fee_frequency': 'MONTHLY'
        }
        
        response = staff_client.post(url, data, format='json')
        
        assert response.status_code == 201
        estate = Estate.objects.get(id=response.data['id'])
        assert estate.is_active is True
        assert estate.created_at is not None
        assert estate.updated_at is not None


@pytest.mark.django_db
class TestEstateCreateValidation:
    """Test validation rules for estate creation."""
    
    def test_create_without_name_fails(self, staff_client):
        """Test creating estate without name fails."""
        url = get_estate_list_url()
        data = {
            'estate_type': 'PRIVATE',
            'fee_frequency': 'MONTHLY'
        }
        
        response = staff_client.post(url, data, format='json')
        
        assert response.status_code == 400
        assert 'name' in response.data
    
    def test_create_with_empty_name_fails(self, staff_client):
        """Test creating estate with empty name fails."""
        url = get_estate_list_url()
        data = {
            'name': '',
            'estate_type': 'PRIVATE',
            'fee_frequency': 'MONTHLY'
        }
        
        response = staff_client.post(url, data, format='json')
        
        assert response.status_code == 400
        assert 'name' in response.data
    
    def test_create_with_whitespace_name_fails(self, staff_client):
        """Test creating estate with whitespace-only name fails."""
        url = get_estate_list_url()
        data = {
            'name': '   ',
            'estate_type': 'PRIVATE',
            'fee_frequency': 'MONTHLY'
        }
        
        response = staff_client.post(url, data, format='json')
        
        assert response.status_code == 400
        assert 'name' in response.data
    
    def test_create_without_estate_type_fails(self, staff_client):
        """Test creating estate without estate_type fails."""
        url = get_estate_list_url()
        data = {
            'name': 'Test Estate',
            'fee_frequency': 'MONTHLY'
        }
        
        response = staff_client.post(url, data, format='json')
        
        assert response.status_code == 400
        assert 'estate_type' in response.data
    
    def test_create_with_invalid_estate_type_fails(self, staff_client):
        """Test creating estate with invalid estate_type fails."""
        url = get_estate_list_url()
        data = {
            'name': 'Test Estate',
            'estate_type': 'INVALID_TYPE',
            'fee_frequency': 'MONTHLY'
        }
        
        response = staff_client.post(url, data, format='json')
        
        assert response.status_code == 400
        assert 'estate_type' in response.data
    
    def test_create_without_fee_frequency_fails(self, staff_client):
        """Test creating estate without fee_frequency fails."""
        url = get_estate_list_url()
        data = {
            'name': 'Test Estate',
            'estate_type': 'PRIVATE'
        }
        
        response = staff_client.post(url, data, format='json')
        
        assert response.status_code == 400
        assert 'fee_frequency' in response.data
    
    def test_create_with_invalid_fee_frequency_fails(self, staff_client):
        """Test creating estate with invalid fee_frequency fails."""
        url = get_estate_list_url()
        data = {
            'name': 'Test Estate',
            'estate_type': 'PRIVATE',
            'fee_frequency': 'DAILY'
        }
        
        response = staff_client.post(url, data, format='json')
        
        assert response.status_code == 400
        assert 'fee_frequency' in response.data
    
    def test_create_with_zero_units_fails(self, staff_client):
        """Test creating estate with zero units fails."""
        url = get_estate_list_url()
        data = {
            'name': 'Test Estate',
            'estate_type': 'PRIVATE',
            'fee_frequency': 'MONTHLY',
            'approximate_units': 0
        }
        
        response = staff_client.post(url, data, format='json')
        
        assert response.status_code == 400
        assert 'approximate_units' in response.data
    
    def test_create_with_negative_units_fails(self, staff_client):
        """Test creating estate with negative units fails."""
        url = get_estate_list_url()
        data = {
            'name': 'Test Estate',
            'estate_type': 'PRIVATE',
            'fee_frequency': 'MONTHLY',
            'approximate_units': -10
        }
        
        response = staff_client.post(url, data, format='json')
        
        assert response.status_code == 400
        assert 'approximate_units' in response.data
    
    def test_create_name_strips_whitespace(self, staff_client):
        """Test name field strips leading/trailing whitespace."""
        url = get_estate_list_url()
        data = {
            'name': '  Trimmed Estate  ',
            'estate_type': 'PRIVATE',
            'fee_frequency': 'MONTHLY'
        }
        
        response = staff_client.post(url, data, format='json')
        
        assert response.status_code == 201
        estate = Estate.objects.get(id=response.data['id'])
        assert estate.name == 'Trimmed Estate'