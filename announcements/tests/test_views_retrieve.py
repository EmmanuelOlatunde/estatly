# tests/test_views_retrieve.py

"""
Tests for announcements retrieve endpoint.

Coverage:
- Authentication/authorization
- Success paths
- Non-existent resources
- Cross-user access
- Inactive announcements
"""

import pytest
from django.urls import reverse
from .factories import AnnouncementFactory
from .helpers import assert_announcement_matches_data
import uuid


@pytest.mark.django_db
class TestAnnouncementRetrieve:
    """Test GET /api/announcements/{id}/ endpoint."""
    
    def test_unauthenticated_user_denied(self, api_client, announcement):
        """Test unauthenticated users cannot retrieve announcement."""
        url = reverse('announcements:announcement-detail', args=[announcement.id])
        response = api_client.get(url)
        
        assert response.status_code == 401
    
    def test_owner_can_retrieve_own_announcement(
        self, authenticated_client, announcement
    ):
        """Test owner can retrieve their own announcement."""
        url = reverse('announcements:announcement-detail', args=[announcement.id])
        response = authenticated_client.get(url)
        
        assert response.status_code == 200
        assert_announcement_matches_data(response.data, announcement)
    
    def test_user_can_retrieve_active_announcement(
        self, regular_client, other_user_announcement
    ):
        """Test any user can retrieve active announcements."""
        url = reverse(
            'announcements:announcement-detail',
            args=[other_user_announcement.id]
        )
        response = regular_client.get(url)
        
        assert response.status_code == 200
        assert response.data['id'] == str(other_user_announcement.id)
    
    def test_non_owner_cannot_retrieve_inactive_announcement(
        self, regular_client, inactive_announcement
    ):
        """Test non-owner cannot retrieve inactive announcements."""
        url = reverse(
            'announcements:announcement-detail',
            args=[inactive_announcement.id]
        )
        response = regular_client.get(url)
        
        assert response.status_code == 404
    
    def test_owner_can_retrieve_own_inactive_announcement(
        self, authenticated_client, inactive_announcement
    ):
        """Test owner can retrieve their own inactive announcement."""
        url = reverse(
            'announcements:announcement-detail',
            args=[inactive_announcement.id]
        )
        response = authenticated_client.get(url)
        
        assert response.status_code == 200
        assert response.data['is_active'] is False
    
    def test_non_existent_announcement_returns_404(self, authenticated_client):
        """Test retrieving non-existent announcement returns 404."""
        fake_id = uuid.uuid4()
        url = reverse('announcements:announcement-detail', args=[fake_id])
        response = authenticated_client.get(url)
        
        assert response.status_code == 404
    
    def test_invalid_uuid_returns_404(self, authenticated_client):
        """Test invalid UUID returns 404."""
        url = '/api/announcements/invalid-uuid/'
        response = authenticated_client.get(url)
        
        assert response.status_code == 404
    
    def test_response_contains_all_fields(
        self, authenticated_client, announcement
    ):
        """Test response contains all expected fields."""
        url = reverse('announcements:announcement-detail', args=[announcement.id])
        response = authenticated_client.get(url)
        
        assert response.status_code == 200
        
        required_fields = [
            'id', 'title', 'message', 'preview',
            'created_by', 'is_active', 'created_at', 'updated_at'
        ]
        for field in required_fields:
            assert field in response.data
    
    def test_response_excludes_sensitive_fields(
        self, authenticated_client, announcement
    ):
        """Test response doesn't contain sensitive fields."""
        url = reverse('announcements:announcement-detail', args=[announcement.id])
        response = authenticated_client.get(url)
        
        assert response.status_code == 200
        
        sensitive_fields = ['password', 'token', 'secret']
        for field in sensitive_fields:
            assert field not in response.data
    
    def test_created_by_contains_user_details(
        self, authenticated_client, announcement
    ):
        """Test created_by field contains user information."""
        url = reverse('announcements:announcement-detail', args=[announcement.id])
        response = authenticated_client.get(url)
        
        assert response.status_code == 200
        assert 'created_by' in response.data
        
        creator = response.data['created_by']
        assert 'id' in creator
        assert 'email' in creator
        assert 'full_name' in creator
    
    def test_jwt_authentication_works(self, jwt_client, announcement):
        """Test JWT authentication works for retrieve endpoint."""
        url = reverse('announcements:announcement-detail', args=[announcement.id])
        response = jwt_client.get(url)
        
        assert response.status_code == 200