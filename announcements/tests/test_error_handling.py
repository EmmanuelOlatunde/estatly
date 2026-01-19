# tests/test_error_handling.py

"""
Tests for error handling and exception scenarios.

Coverage:
- HTTP error responses
- Validation error formats
- Server error handling
- Invalid data formats
- Missing required fields
"""

import pytest
from django.urls import reverse
import json


@pytest.mark.django_db
class TestErrorResponses:
    """Test error response formats and status codes."""
    
    def setup_method(self):
        """Set up test data."""
        self.list_url = reverse('announcements:announcement-list')
    
    def test_401_unauthorized_format(self, api_client):
        """Test 401 response has correct format."""
        response = api_client.get(self.list_url)
        
        assert response.status_code == 401
        assert 'detail' in response.data
    
    def test_403_forbidden_format(
        self, regular_client
    ):
        """Test 403 response has correct format."""
        data = {
            'title': 'Test Announcement',
            'message': 'Message content here.',
            'is_active': True
        }
        response = regular_client.post(self.list_url, data)
        
        assert response.status_code == 403
        assert 'detail' in response.data
    
    def test_404_not_found_format(
        self, authenticated_client
    ):
        """Test 404 response has correct format."""
        import uuid
        fake_id = uuid.uuid4()
        url = reverse('announcements:announcement-detail', args=[fake_id])
        
        response = authenticated_client.get(url)
        
        assert response.status_code == 404
        assert 'detail' in response.data
    
    def test_400_validation_error_format(
        self, authenticated_client
    ):
        """Test 400 validation error has correct format."""
        data = {
            'title': '',
            'message': '',
            'is_active': True
        }
        response = authenticated_client.post(self.list_url, data)
        
        assert response.status_code == 400
        assert isinstance(response.data, dict)
        assert 'title' in response.data or 'message' in response.data
    
    def test_validation_error_contains_field_names(
        self, authenticated_client
    ):
        """Test validation errors include field names."""
        data = {
            'title': 'AB',
            'message': 'Short',
            'is_active': True
        }
        response = authenticated_client.post(self.list_url, data)
        
        assert response.status_code == 400
        assert 'title' in response.data
        assert 'message' in response.data
    
    def test_validation_error_messages_are_strings(
        self, authenticated_client
    ):
        """Test validation error messages are strings or arrays."""
        data = {
            'title': '',
            'message': 'Valid message here.',
            'is_active': True
        }
        response = authenticated_client.post(self.list_url, data)
        
        assert response.status_code == 400
        assert 'title' in response.data
        assert isinstance(response.data['title'], (list, str))


@pytest.mark.django_db
class TestInvalidDataFormats:
    """Test handling of invalid data formats."""
    
    def setup_method(self):
        """Set up test data."""
        self.list_url = reverse('announcements:announcement-list')
    
    def test_malformed_json_returns_400(self, authenticated_client):
        """Test malformed JSON returns 400."""
        response = authenticated_client.post(
            self.list_url,
            data='{"title": "Test", invalid json}',
            content_type='application/json'
        )
        
        assert response.status_code == 400
    
    def test_invalid_content_type(self, authenticated_client):
        """Test invalid content type is handled."""
        response = authenticated_client.post(
            self.list_url,
            data='title=Test&message=Message',
            content_type='text/plain'
        )
        
        assert response.status_code in [400, 415]
    
    def test_invalid_boolean_value(self, authenticated_client):
        """Test invalid boolean value returns error."""
        data = {
            'title': 'Test Announcement',
            'message': 'Message content here.',
            'is_active': 'not_a_boolean'
        }
        response = authenticated_client.post(
            self.list_url, data, format='json'
        )
        
        assert response.status_code == 400
    
    def test_extra_fields_ignored(self, authenticated_client):
        """Test extra unknown fields are ignored."""
        data = {
            'title': 'Test Announcement',
            'message': 'Message content here.',
            'is_active': True,
            'unknown_field': 'value'
        }
        response = authenticated_client.post(self.list_url, data)
        
        assert response.status_code == 201
    
    def test_null_value_for_required_field(self, authenticated_client):
        """Test null value for required field returns error."""
        data = {
            'title': None,
            'message': 'Message content here.',
            'is_active': True
        }
        response = authenticated_client.post(
            self.list_url, data, format='json'
        )
        
        assert response.status_code == 400
        assert 'title' in response.data


@pytest.mark.django_db
class TestMissingFields:
    """Test handling of missing required fields."""
    
    def setup_method(self):
        """Set up test data."""
        self.list_url = reverse('announcements:announcement-list')
    
    def test_missing_all_fields_returns_errors(self, authenticated_client):
        """Test missing all required fields returns multiple errors."""
        data = {}
        response = authenticated_client.post(self.list_url, data)
        
        assert response.status_code == 400
        assert 'title' in response.data
        assert 'message' in response.data
    
    def test_missing_title_returns_specific_error(self, authenticated_client):
        """Test missing title returns specific error."""
        data = {
            'message': 'Message content here.',
            'is_active': True
        }
        response = authenticated_client.post(self.list_url, data)
        
        assert response.status_code == 400
        assert 'title' in response.data
        assert 'message' not in response.data
    
    def test_missing_message_returns_specific_error(
        self, authenticated_client
    ):
        """Test missing message returns specific error."""
        data = {
            'title': 'Test Announcement',
            'is_active': True
        }
        response = authenticated_client.post(self.list_url, data)
        
        assert response.status_code == 400
        assert 'message' in response.data
        assert 'title' not in response.data


@pytest.mark.django_db
class TestMethodNotAllowed:
    """Test HTTP method restrictions."""
    
    def test_put_on_list_not_allowed(self, authenticated_client):
        """Test PUT on list endpoint is not allowed."""
        url = reverse('announcements:announcement-list')
        data = {
            'title': 'Test Announcement',
            'message': 'Message content here.',
            'is_active': True
        }
        response = authenticated_client.put(url, data)
        
        assert response.status_code == 405
    
    def test_post_on_detail_not_allowed(
        self, authenticated_client, announcement
    ):
        """Test POST on detail endpoint is not allowed."""
        url = reverse('announcements:announcement-detail', args=[announcement.id])
        data = {
            'title': 'Test Announcement',
            'message': 'Message content here.',
            'is_active': True
        }
        response = authenticated_client.post(url, data)
        
        assert response.status_code == 405


@pytest.mark.django_db
class TestConcurrentModification:
    """Test concurrent modification scenarios."""
    
    def test_update_after_delete_returns_404(
        self, authenticated_client, announcement
    ):
        """Test updating deleted announcement returns 404."""
        url = reverse('announcements:announcement-detail', args=[announcement.id])
        
        authenticated_client.delete(url)
        
        data = {'title': 'Updated Title'}
        response = authenticated_client.patch(url, data)
        
        assert response.status_code == 404
    
    def test_delete_after_delete_returns_404(
        self, authenticated_client, announcement
    ):
        """Test deleting already deleted announcement returns 404."""
        url = reverse('announcements:announcement-detail', args=[announcement.id])
        
        response1 = authenticated_client.delete(url)
        assert response1.status_code == 204
        
        response2 = authenticated_client.delete(url)
        assert response2.status_code == 404