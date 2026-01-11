

# tests/test_security.py
"""
Tests for security concerns.

Coverage:
- IDOR vulnerabilities
- Mass assignment protection
- Sensitive data exposure
- Input sanitization
"""

import pytest
from .helpers import get_estate_detail_url, get_estate_list_url
from .factories import EstateFactory
from estates.models import Estate



@pytest.mark.django_db
class TestEstateSecurity:
    """Test security aspects of estate endpoints."""
    
    def test_cannot_set_id_on_create(self, staff_client):
        """Test cannot manually set ID on creation."""
        import uuid
        custom_id = uuid.uuid4()
        
        url = get_estate_list_url()
        data = {
            'id': str(custom_id),
            'name': 'Test Estate',
            'estate_type': 'PRIVATE',
            'fee_frequency': 'MONTHLY'
        }
        
        response = staff_client.post(url, data, format='json')
        
        assert response.status_code == 201
        assert response.data['id'] != str(custom_id)
    
    def test_cannot_modify_created_at(self, staff_client, estate):
        """Test cannot modify created_at timestamp."""
        from django.utils import timezone
        
        original_created_at = estate.created_at
        future_date = timezone.now() + timezone.timedelta(days=30)
        
        url = get_estate_detail_url(estate.id)
        data = {'created_at': future_date.isoformat()}
        
        response = staff_client.patch(url, data, format='json')
        
        assert response.status_code == 200
        estate.refresh_from_db()
        assert estate.created_at == original_created_at
    
    def test_sql_injection_in_search(self, authenticated_client):
        """Test SQL injection attempts in search are sanitized."""
        EstateFactory.create(name="Normal Estate")
        
        url = get_estate_list_url()
        sql_injection = "'; DROP TABLE estates_estate; --"
        response = authenticated_client.get(url, {'search': sql_injection})
        
        assert response.status_code == 200
        assert Estate.objects.count() > 0
    
    def test_xss_in_name_field(self, staff_client):
        """Test XSS payload in name field is stored as-is."""
        xss_payload = "<script>alert('XSS')</script>"
        
        url = get_estate_list_url()
        data = {
            'name': xss_payload,
            'estate_type': 'PRIVATE',
            'fee_frequency': 'MONTHLY'
        }
        
        response = staff_client.post(url, data, format='json')
        
        assert response.status_code == 201
        assert response.data['name'] == xss_payload
    
    def test_mass_assignment_protection(self, staff_client, estate):
        """Test cannot mass assign protected fields."""
        url = get_estate_detail_url(estate.id)
        data = {
            'name': 'Updated',
            'created_at': '2020-01-01T00:00:00Z',
            'updated_at': '2020-01-01T00:00:00Z',
            'id': 'new-id'
        }
        
        original_id = estate.id
        original_created = estate.created_at
        
        response = staff_client.patch(url, data, format='json')
        
        assert response.status_code == 200
        estate.refresh_from_db()
        assert estate.id == original_id
        assert estate.created_at == original_created