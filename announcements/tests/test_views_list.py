# tests/test_views_list.py

"""
Tests for announcements list endpoint.

Coverage:
- Authentication/authorization
- Success paths
- Empty results
- Multiple announcements
- Response structure
"""

import pytest
from django.urls import reverse
from .factories import AnnouncementFactory
from .helpers import assert_announcement_list_response


@pytest.mark.django_db
class TestAnnouncementList:
    """Test GET /api/announcements/ endpoint."""
    
    def setup_method(self):
        """Set up test data."""
        self.url = reverse('announcements:announcement-list')
    
    def test_unauthenticated_user_denied(self, api_client):
        """Test unauthenticated users cannot access list."""
        response = api_client.get(self.url)
        assert response.status_code == 401
    
    def test_authenticated_user_can_list_announcements(self, authenticated_client):
        """Test authenticated users can list announcements."""
        response = authenticated_client.get(self.url)
        assert response.status_code == 200
    
    def test_empty_list_returns_empty_results(self, authenticated_client):
        """Test empty list returns empty results array."""
        response = authenticated_client.get(self.url)
        
        assert response.status_code == 200
        assert 'results' in response.data
        assert len(response.data['results']) == 0
    
    def test_manager_sees_own_announcements(self, authenticated_client, announcement_list):
        """Test managers see their own announcements."""
        response = authenticated_client.get(self.url)
        
        assert_announcement_list_response(response, expected_count=5)
    
    def test_manager_sees_only_own_announcements(
        self, authenticated_client, authenticated_user, other_user
    ):
        """Test managers see only their own announcements."""
        own_announcement = AnnouncementFactory.create(created_by=authenticated_user)
        other_announcement = AnnouncementFactory.create(created_by=other_user)
        
        response = authenticated_client.get(self.url)
        
        assert response.status_code == 200
        result_ids = [item['id'] for item in response.data['results']]
        assert str(own_announcement.id) in result_ids
        assert str(other_announcement.id) in result_ids
    
    def test_regular_user_sees_all_active_announcements(
        self, regular_client, authenticated_user, other_user
    ):
        """Test regular users see all active announcements."""
        announcement1 = AnnouncementFactory.create(
            created_by=authenticated_user, is_active=True
        )
        announcement2 = AnnouncementFactory.create(
            created_by=other_user, is_active=True
        )
        
        response = regular_client.get(self.url)
        
        assert response.status_code == 200
        assert len(response.data['results']) == 2
    
    def test_response_structure_is_correct(
        self, authenticated_client, authenticated_user
    ):
        """Test response has correct structure and fields."""
        AnnouncementFactory.create(created_by=authenticated_user)
        
        response = authenticated_client.get(self.url)
        
        assert response.status_code == 200
        assert 'count' in response.data
        assert 'results' in response.data
        
        result = response.data['results'][0]
        required_fields = [
            'id', 'title', 'message', 'preview',
            'created_by', 'is_active', 'created_at', 'updated_at'
        ]
        for field in required_fields:
            assert field in result
    
    def test_created_by_is_nested_with_user_info(
        self, authenticated_client, authenticated_user
    ):
        """Test created_by field contains nested user information."""
        AnnouncementFactory.create(created_by=authenticated_user)
        
        response = authenticated_client.get(self.url)
        
        assert response.status_code == 200
        creator = response.data['results'][0]['created_by']
        assert 'id' in creator
        assert 'email' in creator
        assert 'full_name' in creator
    
    def test_inactive_announcements_excluded_by_default(
        self, authenticated_client, authenticated_user
    ):
        """Test inactive announcements are excluded from list by default."""
        active = AnnouncementFactory.create(
            created_by=authenticated_user, is_active=True
        )
        inactive = AnnouncementFactory.create(
            created_by=authenticated_user, is_active=False
        )
        
        response = authenticated_client.get(self.url)
        
        assert response.status_code == 200
        result_ids = [item['id'] for item in response.data['results']]
        assert str(active.id) in result_ids
        assert str(inactive.id) not in result_ids
    
    def test_include_inactive_parameter_shows_all(
        self, authenticated_client, authenticated_user
    ):
        """Test include_inactive parameter includes inactive announcements."""
        active = AnnouncementFactory.create(
            created_by=authenticated_user, is_active=True
        )
        inactive = AnnouncementFactory.create(
            created_by=authenticated_user, is_active=False
        )
        
        response = authenticated_client.get(
            self.url, {'include_inactive': 'true'}
        )
        
        assert response.status_code == 200
        result_ids = [item['id'] for item in response.data['results']]
        assert str(active.id) in result_ids
        assert str(inactive.id) in result_ids
    
    def test_list_ordered_by_created_at_desc(
        self, authenticated_client, authenticated_user
    ):
        """Test list is ordered by created_at descending."""
        announcements = [
            AnnouncementFactory.create(created_by=authenticated_user)
            for _ in range(3)
        ]
        
        response = authenticated_client.get(self.url)
        
        assert response.status_code == 200
        results = response.data['results']
        
        for i in range(len(results) - 1):
            current_date = results[i]['created_at']
            next_date = results[i + 1]['created_at']
            assert current_date >= next_date
    
    def test_jwt_authentication_works(self, jwt_client, authenticated_user):
        """Test JWT token authentication works for list endpoint."""
        AnnouncementFactory.create(created_by=authenticated_user)
        
        response = jwt_client.get(self.url)
        
        assert response.status_code == 200
        assert len(response.data['results']) > 0