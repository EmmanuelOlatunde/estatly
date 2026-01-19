# tests/test_views_create.py

"""
Tests for announcements create endpoint.

Coverage:
- Authentication/authorization
- Success paths
- Validation failures
- Database side effects
- Permission checks
"""

import pytest
from django.urls import reverse
from announcements.models import Announcement


@pytest.mark.django_db
class TestAnnouncementCreate:
    """Test POST /api/announcements/ endpoint."""
    
    def setup_method(self):
        """Set up test data."""
        self.url = reverse('announcements:announcement-list')
        self.valid_data = {
            'title': 'Test Announcement',
            'message': 'This is a test message with sufficient length.',
            'is_active': True
        }
    
    def test_unauthenticated_user_denied(self, api_client):
        """Test unauthenticated users cannot create announcements."""
        response = api_client.post(self.url, self.valid_data)
        assert response.status_code == 401
    
    def test_regular_user_denied(self, regular_client):
        """Test regular users without manager permissions cannot create."""
        response = regular_client.post(self.url, self.valid_data)
        assert response.status_code == 403
    
    def test_manager_can_create_announcement(self, authenticated_client):
        """Test managers can create announcements."""
        response = authenticated_client.post(self.url, self.valid_data)
        
        assert response.status_code == 201
        assert 'id' in response.data
        assert response.data['title'] == self.valid_data['title']
        assert response.data['message'] == self.valid_data['message']
    
    def test_created_announcement_exists_in_database(
        self, authenticated_client, authenticated_user
    ):
        """Test created announcement exists in database with correct values."""
        response = authenticated_client.post(self.url, self.valid_data)
        
        assert response.status_code == 201
        
        announcement = Announcement.objects.get(id=response.data['id'])
        assert announcement.title == self.valid_data['title']
        assert announcement.message == self.valid_data['message']
        assert announcement.is_active == self.valid_data['is_active']
        assert announcement.created_by == authenticated_user
        assert announcement.created_at is not None
        assert announcement.updated_at is not None
    
    def test_created_by_set_automatically(
        self, authenticated_client, authenticated_user
    ):
        """Test created_by is set automatically to current user."""
        response = authenticated_client.post(self.url, self.valid_data)
        
        assert response.status_code == 201
        
        announcement = Announcement.objects.get(id=response.data['id'])
        assert announcement.created_by == authenticated_user
    
    def test_missing_title_returns_400(self, authenticated_client):
        """Test missing title returns validation error."""
        data = {
            'message': 'This is a test message.',
            'is_active': True
        }
        response = authenticated_client.post(self.url, data)
        
        assert response.status_code == 400
        assert 'title' in response.data
    
    def test_missing_message_returns_400(self, authenticated_client):
        """Test missing message returns validation error."""
        data = {
            'title': 'Test Announcement',
            'is_active': True
        }
        response = authenticated_client.post(self.url, data)
        
        assert response.status_code == 400
        assert 'message' in response.data
    
    def test_empty_title_returns_400(self, authenticated_client):
        """Test empty title returns validation error."""
        data = {
            'title': '',
            'message': 'This is a test message.',
            'is_active': True
        }
        response = authenticated_client.post(self.url, data)
        
        assert response.status_code == 400
        assert 'title' in response.data
    
    def test_whitespace_only_title_returns_400(self, authenticated_client):
        """Test whitespace-only title returns validation error."""
        data = {
            'title': '   ',
            'message': 'This is a test message.',
            'is_active': True
        }
        response = authenticated_client.post(self.url, data)
        
        assert response.status_code == 400
        assert 'title' in response.data
    
    def test_short_title_returns_400(self, authenticated_client):
        """Test title under 3 characters returns validation error."""
        data = {
            'title': 'AB',
            'message': 'This is a test message.',
            'is_active': True
        }
        response = authenticated_client.post(self.url, data)
        
        assert response.status_code == 400
        assert 'title' in response.data
    
    def test_empty_message_returns_400(self, authenticated_client):
        """Test empty message returns validation error."""
        data = {
            'title': 'Test Announcement',
            'message': '',
            'is_active': True
        }
        response = authenticated_client.post(self.url, data)
        
        assert response.status_code == 400
        assert 'message' in response.data
    
    def test_whitespace_only_message_returns_400(self, authenticated_client):
        """Test whitespace-only message returns validation error."""
        data = {
            'title': 'Test Announcement',
            'message': '   ',
            'is_active': True
        }
        response = authenticated_client.post(self.url, data)
        
        assert response.status_code == 400
        assert 'message' in response.data
    
    def test_short_message_returns_400(self, authenticated_client):
        """Test message under 10 characters returns validation error."""
        data = {
            'title': 'Test Announcement',
            'message': 'Short',
            'is_active': True
        }
        response = authenticated_client.post(self.url, data)
        
        assert response.status_code == 400
        assert 'message' in response.data
    
    def test_is_active_defaults_to_true(self, authenticated_client):
        """Test is_active defaults to true when not provided."""
        data = {
            'title': 'Test Announcement',
            'message': 'This is a test message.',
        }
        response = authenticated_client.post(self.url, data)
        
        assert response.status_code == 201
        
        announcement = Announcement.objects.get(id=response.data['id'])
        assert announcement.is_active is True
    
    def test_can_create_inactive_announcement(self, authenticated_client):
        """Test can explicitly create inactive announcement."""
        data = {
            'title': 'Test Announcement',
            'message': 'This is a test message.',
            'is_active': False
        }
        response = authenticated_client.post(self.url, data)
        
        assert response.status_code == 201
        assert response.data['is_active'] is False
    
    def test_title_whitespace_is_stripped(
        self, authenticated_client, authenticated_user
    ):
        """Test leading/trailing whitespace is stripped from title."""
        data = {
            'title': '  Test Announcement  ',
            'message': 'This is a test message.',
            'is_active': True
        }
        response = authenticated_client.post(self.url, data)
        
        assert response.status_code == 201
        
        announcement = Announcement.objects.get(id=response.data['id'])
        assert announcement.title == 'Test Announcement'
    
    def test_message_whitespace_is_stripped(
        self, authenticated_client, authenticated_user
    ):
        """Test leading/trailing whitespace is stripped from message."""
        data = {
            'title': 'Test Announcement',
            'message': '  This is a test message.  ',
            'is_active': True
        }
        response = authenticated_client.post(self.url, data)
        
        assert response.status_code == 201
        
        announcement = Announcement.objects.get(id=response.data['id'])
        assert announcement.message == 'This is a test message.'
    
    def test_very_long_title_accepted(self, authenticated_client):
        """Test very long title (near max_length) is accepted."""
        data = {
            'title': 'A' * 190,
            'message': 'This is a test message.',
            'is_active': True
        }
        response = authenticated_client.post(self.url, data)
        
        assert response.status_code == 201
    
    def test_very_long_message_accepted(self, authenticated_client):
        """Test very long message is accepted."""
        data = {
            'title': 'Test Announcement',
            'message': 'A' * 5000,
            'is_active': True
        }
        response = authenticated_client.post(self.url, data)
        
        assert response.status_code == 201
    
    def test_special_characters_in_title(self, authenticated_client):
        """Test special characters in title are accepted."""
        data = {
            'title': 'Test & Announcement <special>',
            'message': 'This is a test message.',
            'is_active': True
        }
        response = authenticated_client.post(self.url, data)
        
        assert response.status_code == 201
    
    def test_unicode_characters_accepted(self, authenticated_client):
        """Test unicode characters are accepted."""
        data = {
            'title': 'Test Announcement 测试 🎉',
            'message': 'This is a test message with unicode: 你好世界',
            'is_active': True
        }
        response = authenticated_client.post(self.url, data)
        
        assert response.status_code == 201
    
    def test_admin_can_create_announcement(self, admin_client):
        """Test admin users can create announcements."""
        response = admin_client.post(self.url, self.valid_data)
        
        assert response.status_code == 201
    
    def test_jwt_authentication_works(self, jwt_client):
        """Test JWT authentication works for create endpoint."""
        response = jwt_client.post(self.url, self.valid_data)
        
        assert response.status_code == 201
    
    def test_malformed_json_returns_400(self, authenticated_client):
        """Test malformed JSON returns 400."""
        response = authenticated_client.post(
            self.url,
            data='{"invalid": json}',
            content_type='application/json'
        )
        
        assert response.status_code == 400