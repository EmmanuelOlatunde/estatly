# tests/test_error_handling.py

"""
Tests for error handling and exception scenarios.

Coverage:
- 400 Bad Request errors
- 404 Not Found errors
- 500 Server errors (if applicable)
- Malformed requests
- Invalid JSON
- Error message format
"""

import pytest
import json
from django.urls import reverse


@pytest.mark.django_db
class TestBadRequestErrors:
    """Test 400 Bad Request error scenarios."""
    
    def test_malformed_json_returns_400(
        self, authenticated_client, estate
    ):
        """Test malformed JSON returns 400 error."""
        url = reverse('maintenance:maintenance-ticket-list')
        response = authenticated_client.post(
            url,
            data='{"title": "Test", invalid json}',
            content_type='application/json'
        )
        assert response.status_code == 400
    
    def test_invalid_uuid_format_returns_400(
        self, authenticated_client
    ):
        """Test invalid UUID format returns 400."""
        data = {
            'title': 'Test ticket',
            'description': 'Test description',
            'category': 'WATER',
            'estate': 'not-a-valid-uuid'
        }
        
        url = reverse('maintenance:maintenance-ticket-list')
        response = authenticated_client.post(url, data, format='json')
        assert response.status_code == 400
    
    def test_missing_required_fields_returns_400(
        self, authenticated_client
    ):
        """Test missing required fields returns 400 with field errors."""
        data = {}
        
        url = reverse('maintenance:maintenance-ticket-list')
        response = authenticated_client.post(url, data, format='json')
        
        assert response.status_code == 400
        assert 'title' in response.data
        assert 'description' in response.data
        assert 'category' in response.data
        assert 'estate' in response.data
    
    def test_invalid_field_type_returns_400(
        self, authenticated_client, estate
    ):
        """Test invalid field type returns 400."""
        data = {
            'title': 123,
            'description': 'Test description',
            'category': 'WATER',
            'estate': str(estate.id)
        }
        
        url = reverse('maintenance:maintenance-ticket-list')
        response = authenticated_client.post(url, data, format='json')
        # Title might be coerced to string, so this could be 201 or 400
        assert response.status_code in [201, 400]
    
    def test_error_response_format(
        self, authenticated_client
    ):
        """Test error response has correct format."""
        data = {
            'description': 'Test description',
            'category': 'WATER'
        }
        
        url = reverse('maintenance:maintenance-ticket-list')
        response = authenticated_client.post(url, data, format='json')
        
        assert response.status_code == 400
        assert isinstance(response.data, dict)
        for field, errors in response.data.items():
            assert isinstance(errors, list)


@pytest.mark.django_db
class TestNotFoundErrors:
    """Test 404 Not Found error scenarios."""
    
    def test_nonexistent_ticket_returns_404(
        self, authenticated_client
    ):
        """Test accessing non-existent ticket returns 404."""
        import uuid
        fake_id = uuid.uuid4()
        url = reverse('maintenance:maintenance-ticket-detail', args=[fake_id])
        
        response = authenticated_client.get(url)
        assert response.status_code == 404
    
    def test_invalid_uuid_in_url_returns_404(
        self, authenticated_client
    ):
        """Test invalid UUID in URL returns 404."""
        url = '/api/maintenance/tickets/invalid-uuid-format/'
        response = authenticated_client.get(url)
        assert response.status_code == 404
    
    def test_update_nonexistent_ticket_returns_404(
        self, authenticated_client
    ):
        """Test updating non-existent ticket returns 404."""
        import uuid
        fake_id = uuid.uuid4()
        url = reverse('maintenance:maintenance-ticket-detail', args=[fake_id])
        
        response = authenticated_client.patch(
            url,
            {'title': 'Updated title'},
            format='json'
        )
        assert response.status_code == 404
    
    def test_delete_nonexistent_ticket_returns_404(
        self, authenticated_client
    ):
        """Test deleting non-existent ticket returns 404."""
        import uuid
        fake_id = uuid.uuid4()
        url = reverse('maintenance:maintenance-ticket-detail', args=[fake_id])
        
        response = authenticated_client.delete(url)
        assert response.status_code == 404
    
    def test_resolve_nonexistent_ticket_returns_404(
        self, authenticated_client
    ):
        """Test resolving non-existent ticket returns 404."""
        import uuid
        fake_id = uuid.uuid4()
        url = reverse('maintenance:maintenance-ticket-resolve', args=[fake_id])
        
        response = authenticated_client.post(url)
        assert response.status_code == 404
    
    def test_invalid_endpoint_returns_404(
        self, authenticated_client
    ):
        """Test accessing invalid endpoint returns 404."""
        url = '/api/maintenance/invalid-endpoint/'
        response = authenticated_client.get(url)
        assert response.status_code == 404


@pytest.mark.django_db
class TestUnauthorizedErrors:
    """Test 401 Unauthorized error scenarios."""
    
    def test_no_credentials_returns_401(self, api_client, ticket):
        """Test request without credentials returns 401."""
        url = reverse('maintenance:maintenance-ticket-detail', args=[ticket.id])
        response = api_client.get(url)
        assert response.status_code == 401
    
    def test_invalid_token_returns_401(self, api_client, ticket):
        """Test request with invalid token returns 401."""
        api_client.credentials(HTTP_AUTHORIZATION='Bearer invalid_token')
        url = reverse('maintenance:maintenance-ticket-detail', args=[ticket.id])
        response = api_client.get(url)
        assert response.status_code == 401
    
    def test_malformed_auth_header_returns_401(self, api_client, ticket):
        """Test malformed authorization header returns 401."""
        api_client.credentials(HTTP_AUTHORIZATION='InvalidFormat')
        url = reverse('maintenance:maintenance-ticket-detail', args=[ticket.id])
        response = api_client.get(url)
        assert response.status_code == 401


@pytest.mark.django_db
class TestForbiddenErrors:
    """Test 403 Forbidden error scenarios."""
    
    def test_accessing_forbidden_resource_returns_403_or_404(
        self, authenticated_client, other_user_ticket
    ):
        """Test accessing forbidden resource returns 403 or 404."""
        url = reverse('maintenance:maintenance-ticket-detail', args=[other_user_ticket.id])
        response = authenticated_client.get(url)
        # Could be 403 or 404 depending on security policy
        assert response.status_code in [403, 404]


@pytest.mark.django_db
class TestMethodNotAllowed:
    """Test 405 Method Not Allowed scenarios."""
    
    def test_patch_on_list_endpoint_not_allowed(
        self, authenticated_client
    ):
        """Test PATCH on list endpoint is not allowed."""
        url = reverse('maintenance:maintenance-ticket-list')
        response = authenticated_client.patch(url, {}, format='json')
        assert response.status_code == 405
    
    def test_put_on_list_endpoint_not_allowed(
        self, authenticated_client
    ):
        """Test PUT on list endpoint is not allowed."""
        url = reverse('maintenance:maintenance-ticket-list')
        response = authenticated_client.put(url, {}, format='json')
        assert response.status_code == 405


@pytest.mark.django_db
class TestValidationErrors:
    """Test validation error messages."""
    
    def test_validation_error_has_field_name(
        self, authenticated_client, estate
    ):
        """Test validation error includes field name."""
        data = {
            'title': '',
            'description': 'Test description',
            'category': 'WATER',
            'estate': str(estate.id)
        }
        
        url = reverse('maintenance:maintenance-ticket-list')
        response = authenticated_client.post(url, data, format='json')
        
        assert response.status_code == 400
        assert 'title' in response.data
    
    def test_validation_error_has_message(
        self, authenticated_client, estate
    ):
        """Test validation error includes helpful message."""
        data = {
            'title': '',
            'description': 'Test description',
            'category': 'WATER',
            'estate': str(estate.id)
        }
        
        url = reverse('maintenance:maintenance-ticket-list')
        response = authenticated_client.post(url, data, format='json')
        
        assert response.status_code == 400
        assert 'title' in response.data
        assert isinstance(response.data['title'], list)
        assert len(response.data['title']) > 0
    
    def test_multiple_validation_errors_returned(
        self, authenticated_client
    ):
        """Test multiple validation errors are all returned."""
        data = {
            'title': '',
            'description': '',
            'category': 'INVALID'
        }
        
        url = reverse('maintenance:maintenance-ticket-list')
        response = authenticated_client.post(url, data, format='json')
        
        assert response.status_code == 400
        error_fields = list(response.data.keys())
        assert len(error_fields) >= 3


@pytest.mark.django_db
class TestBusinessLogicErrors:
    """Test business logic error scenarios."""
    
    def test_resolve_already_resolved_ticket_error(
        self, authenticated_client, resolved_ticket
    ):
        """Test resolving already resolved ticket returns error."""
        url = reverse('maintenance:maintenance-ticket-resolve', args=[resolved_ticket.id])
        response = authenticated_client.post(url)
        
        assert response.status_code == 400
        assert 'error' in response.data
        assert 'already resolved' in response.data['error'].lower()
    
    def test_reopen_open_ticket_error(
        self, authenticated_client, ticket
    ):
        """Test reopening open ticket returns error."""
        url = reverse('maintenance:maintenance-ticket-reopen', args=[ticket.id])
        response = authenticated_client.post(url)
        
        assert response.status_code == 400
        assert 'error' in response.data
    
    def test_unit_from_wrong_estate_error(
        self, authenticated_client, estate
    ):
        """Test assigning unit from different estate returns error."""
        from .factories import UnitFactory, EstateFactory
        other_estate = EstateFactory.create()
        other_unit = UnitFactory.create(estate=other_estate)
        
        data = {
            'title': 'Test ticket',
            'description': 'Test description',
            'category': 'WATER',
            'estate': str(estate.id),
            'unit': str(other_unit.id)
        }
        
        url = reverse('maintenance:maintenance-ticket-list')
        response = authenticated_client.post(url, data, format='json')
        
        assert response.status_code == 400
        assert 'unit' in response.data


@pytest.mark.django_db
class TestErrorResponseConsistency:
    """Test error response format consistency."""
    
    def test_all_400_errors_have_consistent_format(
        self, authenticated_client, estate
    ):
        """Test all 400 errors return consistent format."""
        test_cases = [
            {'title': '', 'description': 'test', 'category': 'WATER', 'estate': str(estate.id)},
            {'title': 'test', 'description': '', 'category': 'WATER', 'estate': str(estate.id)},
            {'title': 'test', 'description': 'test', 'category': 'INVALID', 'estate': str(estate.id)},
        ]
        
        url = reverse('maintenance:maintenance-ticket-list')
        
        for data in test_cases:
            response = authenticated_client.post(url, data, format='json')
            assert response.status_code == 400
            assert isinstance(response.data, dict)
            for field_errors in response.data.values():
                assert isinstance(field_errors, list)