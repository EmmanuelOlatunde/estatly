# tests/test_custom_actions.py

"""
Tests for custom announcement actions.

Coverage:
- Print announcement action
- Authentication/authorization
- Response format
- HTML output validation
"""

import pytest
from django.urls import reverse
from bs4 import BeautifulSoup


@pytest.mark.django_db
class TestPrintAnnouncementAction:
    """Test GET /api/announcements/{id}/print/ custom action."""
    
    def test_unauthenticated_user_denied(self, api_client, announcement):
        """Test unauthenticated users cannot access print endpoint."""
        url = reverse(
            'announcements:announcement-print-announcement',
            args=[announcement.id]
        )
        response = api_client.get(url)
        
        assert response.status_code == 401
    
    def test_authenticated_user_can_print_active_announcement(
        self, authenticated_client, other_user_announcement
    ):
        """Test authenticated user can print active announcements."""
        url = reverse(
            'announcements:announcement-print-announcement',
            args=[other_user_announcement.id]
        )
        response = authenticated_client.get(url)
        
        assert response.status_code == 200
        assert response['Content-Type'] == 'text/html; charset=utf-8'
    
    def test_print_returns_html_content(
        self, authenticated_client, announcement
    ):
        """Test print action returns HTML content."""
        url = reverse(
            'announcements:announcement-print-announcement',
            args=[announcement.id]
        )
        response = authenticated_client.get(url)
        
        assert response.status_code == 200
        assert 'text/html' in response['Content-Type']
        
        content = response.content.decode('utf-8')
        assert '<!DOCTYPE html>' in content
        assert '<html>' in content
    
    def test_print_contains_announcement_data(
        self, authenticated_client, announcement
    ):
        """Test print output contains announcement data."""
        url = reverse(
            'announcements:announcement-print-announcement',
            args=[announcement.id]
        )
        response = authenticated_client.get(url)
        
        assert response.status_code == 200
        
        content = response.content.decode('utf-8')
        assert announcement.title in content
        assert announcement.message in content
        assert announcement.created_by.email in content
    
    def test_print_html_structure_is_valid(
        self, authenticated_client, announcement
    ):
        """Test print HTML has valid structure."""
        url = reverse(
            'announcements:announcement-print-announcement',
            args=[announcement.id]
        )
        response = authenticated_client.get(url)
        
        assert response.status_code == 200
        
        soup = BeautifulSoup(response.content, 'html.parser')
        assert soup.find('title') is not None
        assert soup.find('body') is not None
        assert soup.find('style') is not None
    
    def test_print_includes_creator_email(
        self, authenticated_client, announcement
    ):
        """Test print includes creator email."""
        url = reverse(
            'announcements:announcement-print-announcement',
            args=[announcement.id]
        )
        response = authenticated_client.get(url)
        
        assert response.status_code == 200
        
        content = response.content.decode('utf-8')
        assert announcement.created_by.email in content
    
    def test_print_includes_created_date(
        self, authenticated_client, announcement
    ):
        """Test print includes creation date."""
        url = reverse(
            'announcements:announcement-print-announcement',
            args=[announcement.id]
        )
        response = authenticated_client.get(url)
        
        assert response.status_code == 200
        
        content = response.content.decode('utf-8')
        assert str(announcement.created_at.year) in content
    
    def test_print_has_print_optimized_styles(
        self, authenticated_client, announcement
    ):
        """Test print output includes print-optimized CSS."""
        url = reverse(
            'announcements:announcement-print-announcement',
            args=[announcement.id]
        )
        response = authenticated_client.get(url)
        
        assert response.status_code == 200
        
        content = response.content.decode('utf-8')
        assert '@media print' in content
    
    def test_non_owner_can_print_active_announcement(
        self, regular_client, other_user_announcement
    ):
        """Test non-owner can print active announcements."""
        url = reverse(
            'announcements:announcement-print-announcement',
            args=[other_user_announcement.id]
        )
        response = regular_client.get(url)
        
        assert response.status_code == 200
    
    def test_non_owner_cannot_print_inactive_announcement(
        self, regular_client, inactive_announcement
    ):
        """Test non-owner cannot print inactive announcements."""
        url = reverse(
            'announcements:announcement-print-announcement',
            args=[inactive_announcement.id]
        )
        response = regular_client.get(url)
        
        assert response.status_code == 403
    
    def test_owner_can_print_own_inactive_announcement(
        self, authenticated_client, inactive_announcement
    ):
        """Test owner can print their own inactive announcement."""
        url = reverse(
            'announcements:announcement-print-announcement',
            args=[inactive_announcement.id]
        )
        response = authenticated_client.get(url)
        
        assert response.status_code == 200
    
    def test_print_preserves_message_formatting(
        self, authenticated_client, authenticated_user
    ):
        """Test print preserves line breaks in message."""
        from .factories import AnnouncementFactory
        
        announcement = AnnouncementFactory.create(
            created_by=authenticated_user,
            message="Line 1\nLine 2\nLine 3"
        )
        
        url = reverse(
            'announcements:announcement-print-announcement',
            args=[announcement.id]
        )
        response = authenticated_client.get(url)
        
        assert response.status_code == 200
        
        content = response.content.decode('utf-8')
        assert 'white-space: pre-wrap' in content
    
    def test_print_handles_special_characters(
        self, authenticated_client, authenticated_user
    ):
        """Test print handles special HTML characters."""
        from .factories import AnnouncementFactory
        
        announcement = AnnouncementFactory.create(
            created_by=authenticated_user,
            title="Test & Special <chars>",
            message="Message with <tags> & symbols"
        )
        
        url = reverse(
            'announcements:announcement-print-announcement',
            args=[announcement.id]
        )
        response = authenticated_client.get(url)
        
        assert response.status_code == 200
    
    def test_jwt_authentication_works_for_print(
        self, jwt_client, announcement
    ):
        """Test JWT authentication works for print action."""
        url = reverse(
            'announcements:announcement-print-announcement',
            args=[announcement.id]
        )
        response = jwt_client.get(url)
        
        assert response.status_code == 200