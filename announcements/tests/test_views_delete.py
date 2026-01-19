# tests/test_views_delete.py

"""
Tests for announcements delete endpoint.

Coverage:
- Authentication/authorization
- Success paths
- Cross-user access prevention
- Database side effects
- Non-existent resources
"""

import pytest
from django.urls import reverse
from announcements.models import Announcement
import uuid


@pytest.mark.django_db
class TestAnnouncementDelete:
    """Test DELETE /api/announcements/{id}/ endpoint."""
    
    def test_unauthenticated_user_denied(self, api_client, announcement):
        """Test unauthenticated users cannot delete announcements."""
        url = reverse('announcements:announcement-detail', args=[announcement.id])
        response = api_client.delete(url)
        
        assert response.status_code == 401
    
    def test_owner_can_delete_own_announcement(
        self, authenticated_client, announcement
    ):
        """Test owner can delete their own announcement."""
        url = reverse('announcements:announcement-detail', args=[announcement.id])
        response = authenticated_client.delete(url)
        
        assert response.status_code == 204
    
    def test_non_owner_cannot_delete_announcement(
        self, other_client, announcement
    ):
        """Test non-owner cannot delete announcement."""
        url = reverse('announcements:announcement-detail', args=[announcement.id])
        response = other_client.delete(url)
        
        assert response.status_code == 403
    
    def test_admin_can_delete_any_announcement(
        self, admin_client, other_user_announcement
    ):
        """Test admin can delete any announcement."""
        url = reverse(
            'announcements:announcement-detail',
            args=[other_user_announcement.id]
        )
        response = admin_client.delete(url)
        
        assert response.status_code == 204
    
    def test_delete_removes_from_database(
        self, authenticated_client, announcement
    ):
        """Test delete permanently removes announcement from database."""
        announcement_id = announcement.id
        url = reverse('announcements:announcement-detail', args=[announcement_id])
        
        response = authenticated_client.delete(url)
        
        assert response.status_code == 204
        assert not Announcement.objects.filter(id=announcement_id).exists()
    
    def test_delete_non_existent_announcement_returns_404(
        self, authenticated_client
    ):
        """Test deleting non-existent announcement returns 404."""
        fake_id = uuid.uuid4()
        url = reverse('announcements:announcement-detail', args=[fake_id])
        
        response = authenticated_client.delete(url)
        
        assert response.status_code == 404
    
    def test_delete_returns_no_content(
        self, authenticated_client, announcement
    ):
        """Test delete returns 204 No Content with empty body."""
        url = reverse('announcements:announcement-detail', args=[announcement.id])
        
        response = authenticated_client.delete(url)
        
        assert response.status_code == 204
        assert not response.data
    
    def test_cannot_access_deleted_announcement(
        self, authenticated_client, announcement
    ):
        """Test deleted announcement cannot be accessed afterward."""
        announcement_id = announcement.id
        url = reverse('announcements:announcement-detail', args=[announcement_id])
        
        authenticated_client.delete(url)
        
        response = authenticated_client.get(url)
        assert response.status_code == 404
    
    def test_regular_user_cannot_delete_others_announcement(
        self, regular_client, other_user_announcement
    ):
        """Test regular user cannot delete another user's announcement."""
        url = reverse(
            'announcements:announcement-detail',
            args=[other_user_announcement.id]
        )
        response = regular_client.delete(url)
        
        assert response.status_code == 403
        assert Announcement.objects.filter(
            id=other_user_announcement.id
        ).exists()
    
    def test_delete_inactive_announcement(
        self, authenticated_client, inactive_announcement
    ):
        """Test can delete inactive announcement."""
        url = reverse(
            'announcements:announcement-detail',
            args=[inactive_announcement.id]
        )
        response = authenticated_client.delete(url)
        
        assert response.status_code == 204
        assert not Announcement.objects.filter(
            id=inactive_announcement.id
        ).exists()
    
    def test_jwt_authentication_works_for_delete(
        self, jwt_client, announcement
    ):
        """Test JWT authentication works for delete endpoint."""
        url = reverse('announcements:announcement-detail', args=[announcement.id])
        
        response = jwt_client.delete(url)
        
        assert response.status_code == 204
    
    def test_delete_is_idempotent(
        self, authenticated_client, announcement
    ):
        """Test deleting already deleted announcement returns 404."""
        url = reverse('announcements:announcement-detail', args=[announcement.id])
        
        response1 = authenticated_client.delete(url)
        assert response1.status_code == 204
        
        response2 = authenticated_client.delete(url)
        assert response2.status_code == 404