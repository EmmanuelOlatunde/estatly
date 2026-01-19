# tests/test_views_update.py

"""
Tests for announcements update endpoints.

Coverage:
- Authentication/authorization
- Full and partial updates
- Validation failures
- Cross-user access prevention
- Database side effects
"""

import pytest
from django.urls import reverse
from announcements.models import Announcement
import uuid


@pytest.mark.django_db
class TestAnnouncementUpdate:
    """Test PUT/PATCH /api/announcements/{id}/ endpoints."""
    
    def test_unauthenticated_user_denied_patch(self, api_client, announcement):
        """Test unauthenticated users cannot update announcements."""
        url = reverse('announcements:announcement-detail', args=[announcement.id])
        data = {'title': 'Updated Title'}
        response = api_client.patch(url, data)
        
        assert response.status_code == 401
    
    def test_unauthenticated_user_denied_put(self, api_client, announcement):
        """Test unauthenticated users cannot update with PUT."""
        url = reverse('announcements:announcement-detail', args=[announcement.id])
        data = {
            'title': 'Updated Title',
            'message': 'Updated message content.',
            'is_active': True
        }
        response = api_client.put(url, data)
        
        assert response.status_code == 401
    
    def test_owner_can_partially_update_announcement(
        self, authenticated_client, announcement
    ):
        """Test owner can partially update their announcement."""
        url = reverse('announcements:announcement-detail', args=[announcement.id])
        data = {'title': 'Updated Title'}
        response = authenticated_client.patch(url, data)
        
        assert response.status_code == 200
        assert response.data['title'] == 'Updated Title'
    
    def test_owner_can_fully_update_announcement(
        self, authenticated_client, announcement
    ):
        """Test owner can fully update their announcement."""
        url = reverse('announcements:announcement-detail', args=[announcement.id])
        data = {
            'title': 'Updated Title',
            'message': 'Updated message content here.',
            'is_active': False
        }
        response = authenticated_client.put(url, data)
        
        assert response.status_code == 200
        assert response.data['title'] == 'Updated Title'
        assert response.data['message'] == 'Updated message content here.'
        assert response.data['is_active'] is False
    
    def test_non_owner_cannot_update_announcement(
        self, other_client, announcement
    ):
        """Test non-owner cannot update announcement."""
        url = reverse('announcements:announcement-detail', args=[announcement.id])
        data = {'title': 'Malicious Update'}
        response = other_client.patch(url, data)
        
        assert response.status_code == 403
    
    def test_admin_can_update_any_announcement(
        self, admin_client, other_user_announcement
    ):
        """Test admin can update any announcement."""
        url = reverse(
            'announcements:announcement-detail',
            args=[other_user_announcement.id]
        )
        data = {'title': 'Admin Updated Title'}
        response = admin_client.patch(url, data)
        
        assert response.status_code == 200
        assert response.data['title'] == 'Admin Updated Title'
    
    def test_update_persists_to_database(
        self, authenticated_client, announcement
    ):
        """Test update changes persist to database."""
        url = reverse('announcements:announcement-detail', args=[announcement.id])
        data = {'title': 'Database Updated Title'}
        response = authenticated_client.patch(url, data)
        
        assert response.status_code == 200
        
        announcement.refresh_from_db()
        assert announcement.title == 'Database Updated Title'
    
    def test_partial_update_title_only(
        self, authenticated_client, announcement
    ):
        """Test can update only title."""
        url = reverse('announcements:announcement-detail', args=[announcement.id])
        original_message = announcement.message
        data = {'title': 'New Title Only'}
        
        response = authenticated_client.patch(url, data)
        
        assert response.status_code == 200
        announcement.refresh_from_db()
        assert announcement.title == 'New Title Only'
        assert announcement.message == original_message
    
    def test_partial_update_message_only(
        self, authenticated_client, announcement
    ):
        """Test can update only message."""
        url = reverse('announcements:announcement-detail', args=[announcement.id])
        original_title = announcement.title
        data = {'message': 'New message content goes here.'}
        
        response = authenticated_client.patch(url, data)
        
        assert response.status_code == 200
        announcement.refresh_from_db()
        assert announcement.title == original_title
        assert announcement.message == 'New message content goes here.'
    
    def test_partial_update_is_active_only(
        self, authenticated_client, announcement
    ):
        """Test can update only is_active status."""
        url = reverse('announcements:announcement-detail', args=[announcement.id])
        data = {'is_active': False}
        
        response = authenticated_client.patch(url, data)
        
        assert response.status_code == 200
        announcement.refresh_from_db()
        assert announcement.is_active is False
    
    def test_update_validates_title_length(
        self, authenticated_client, announcement
    ):
        """Test update validates title minimum length."""
        url = reverse('announcements:announcement-detail', args=[announcement.id])
        data = {'title': 'AB'}
        
        response = authenticated_client.patch(url, data)
        
        assert response.status_code == 400
        assert 'title' in response.data
    
    def test_update_validates_message_length(
        self, authenticated_client, announcement
    ):
        """Test update validates message minimum length."""
        url = reverse('announcements:announcement-detail', args=[announcement.id])
        data = {'message': 'Short'}
        
        response = authenticated_client.patch(url, data)
        
        assert response.status_code == 400
        assert 'message' in response.data
    
    def test_update_empty_title_returns_400(
        self, authenticated_client, announcement
    ):
        """Test empty title returns validation error."""
        url = reverse('announcements:announcement-detail', args=[announcement.id])
        data = {'title': ''}
        
        response = authenticated_client.patch(url, data)
        
        assert response.status_code == 400
        assert 'title' in response.data
    
    def test_update_whitespace_only_title_returns_400(
        self, authenticated_client, announcement
    ):
        """Test whitespace-only title returns validation error."""
        url = reverse('announcements:announcement-detail', args=[announcement.id])
        data = {'title': '   '}
        
        response = authenticated_client.patch(url, data)
        
        assert response.status_code == 400
        assert 'title' in response.data
    
    def test_update_strips_whitespace(
        self, authenticated_client, announcement
    ):
        """Test update strips leading/trailing whitespace."""
        url = reverse('announcements:announcement-detail', args=[announcement.id])
        data = {'title': '  Whitespace Stripped  '}
        
        response = authenticated_client.patch(url, data)
        
        assert response.status_code == 200
        announcement.refresh_from_db()
        assert announcement.title == 'Whitespace Stripped'
    
    def test_update_non_existent_announcement_returns_404(
        self, authenticated_client
    ):
        """Test updating non-existent announcement returns 404."""
        fake_id = uuid.uuid4()
        url = reverse('announcements:announcement-detail', args=[fake_id])
        data = {'title': 'Updated Title'}
        
        response = authenticated_client.patch(url, data)
        
        assert response.status_code == 404
    
    def test_update_updated_at_timestamp(
        self, authenticated_client, announcement
    ):
        """Test updated_at timestamp is updated."""
        url = reverse('announcements:announcement-detail', args=[announcement.id])
        original_updated_at = announcement.updated_at
        data = {'title': 'New Title'}
        
        response = authenticated_client.patch(url, data)
        
        assert response.status_code == 200
        announcement.refresh_from_db()
        assert announcement.updated_at > original_updated_at
    
    def test_update_does_not_change_created_by(
        self, authenticated_client, announcement, authenticated_user
    ):
        """Test update does not change created_by field."""
        url = reverse('announcements:announcement-detail', args=[announcement.id])
        data = {'title': 'New Title'}
        
        response = authenticated_client.patch(url, data)
        
        assert response.status_code == 200
        announcement.refresh_from_db()
        assert announcement.created_by == authenticated_user
    
    def test_update_does_not_change_created_at(
        self, authenticated_client, announcement
    ):
        """Test update does not change created_at timestamp."""
        url = reverse('announcements:announcement-detail', args=[announcement.id])
        original_created_at = announcement.created_at
        data = {'title': 'New Title'}
        
        response = authenticated_client.patch(url, data)
        
        assert response.status_code == 200
        announcement.refresh_from_db()
        assert announcement.created_at == original_created_at
    
    def test_can_toggle_is_active(
        self, authenticated_client, announcement
    ):
        """Test can toggle is_active status."""
        url = reverse('announcements:announcement-detail', args=[announcement.id])
        
        response = authenticated_client.patch(url, {'is_active': False})
        assert response.status_code == 200
        announcement.refresh_from_db()
        assert announcement.is_active is False
        
        response = authenticated_client.patch(url, {'is_active': True})
        assert response.status_code == 200
        announcement.refresh_from_db()
        assert announcement.is_active is True
    
    def test_jwt_authentication_works_for_update(
        self, jwt_client, announcement
    ):
        """Test JWT authentication works for update endpoint."""
        url = reverse('announcements:announcement-detail', args=[announcement.id])
        data = {'title': 'JWT Updated Title'}
        
        response = jwt_client.patch(url, data)
        
        assert response.status_code == 200