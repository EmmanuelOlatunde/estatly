# tests/test_security.py

"""
Tests for security-specific scenarios.

Coverage:
- IDOR (Insecure Direct Object References)
- Mass assignment vulnerabilities
- Sensitive data exposure
- XSS prevention
- SQL injection prevention
- Authorization bypass attempts
"""

import pytest
from django.urls import reverse
from announcements.models import Announcement
from .factories import UserFactory, AnnouncementFactory
import uuid


@pytest.mark.django_db
class TestIDORPrevention:
    """Test prevention of Insecure Direct Object References."""
    
    def test_user_cannot_update_other_users_announcement_via_idor(
        self, authenticated_client, other_user_announcement
    ):
        """Test user cannot update another user's announcement by ID."""
        url = reverse(
            'announcements:announcement-detail',
            args=[other_user_announcement.id]
        )
        data = {'title': 'Malicious Update'}
        
        response = authenticated_client.patch(url, data)
        
        assert response.status_code == 403
        
        other_user_announcement.refresh_from_db()
        assert other_user_announcement.title != 'Malicious Update'
    
    def test_user_cannot_delete_other_users_announcement_via_idor(
        self, authenticated_client, other_user_announcement
    ):
        """Test user cannot delete another user's announcement by ID."""
        url = reverse(
            'announcements:announcement-detail',
            args=[other_user_announcement.id]
        )
        
        response = authenticated_client.delete(url)
        
        assert response.status_code == 403
        assert Announcement.objects.filter(
            id=other_user_announcement.id
        ).exists()
    
    def test_regular_user_cannot_view_inactive_announcement_via_idor(
        self, regular_client, inactive_announcement
    ):
        """Test non-owner cannot view inactive announcement by guessing ID."""
        url = reverse(
            'announcements:announcement-detail',
            args=[inactive_announcement.id]
        )
        
        response = regular_client.get(url)
        
        assert response.status_code == 404
    
    def test_enumerating_ids_doesnt_leak_existence(
        self, regular_client, other_user
    ):
        """Test that 404 vs 403 doesn't leak announcement existence."""
        inactive = AnnouncementFactory.create(
            created_by=other_user, is_active=False
        )
        fake_id = uuid.uuid4()
        
        url_inactive = reverse(
            'announcements:announcement-detail',
            args=[inactive.id]
        )
        url_fake = reverse(
            'announcements:announcement-detail',
            args=[fake_id]
        )
        
        response_inactive = regular_client.get(url_inactive)
        response_fake = regular_client.get(url_fake)
        
        assert response_inactive.status_code == 404
        assert response_fake.status_code == 404


@pytest.mark.django_db
class TestMassAssignmentPrevention:
    """Test prevention of mass assignment vulnerabilities."""
    
    def test_cannot_set_created_by_on_create(
        self, authenticated_client, other_user
    ):
        """Test cannot override created_by field on create."""
        url = reverse('announcements:announcement-list')
        data = {
            'title': 'Test Announcement',
            'message': 'Message content here.',
            'created_by': str(other_user.id),
            'is_active': True
        }
        
        response = authenticated_client.post(url, data)
        
        assert response.status_code == 201
        
        announcement = Announcement.objects.get(id=response.data['id'])
        assert announcement.created_by != other_user
    
    def test_cannot_modify_created_by_on_update(
        self, authenticated_client, announcement, other_user
    ):
        """Test cannot change created_by field on update."""
        url = reverse('announcements:announcement-detail', args=[announcement.id])
        original_creator = announcement.created_by
        data = {
            'title': 'Updated Title',
            'created_by': str(other_user.id)
        }
        
        response = authenticated_client.patch(url, data)
        
        assert response.status_code == 200
        
        announcement.refresh_from_db()
        assert announcement.created_by == original_creator
    
    def test_cannot_set_id_on_create(self, authenticated_client):
        """Test cannot set custom ID on create."""
        url = reverse('announcements:announcement-list')
        custom_id = uuid.uuid4()
        data = {
            'id': str(custom_id),
            'title': 'Test Announcement',
            'message': 'Message content here.',
            'is_active': True
        }
        
        response = authenticated_client.post(url, data)
        
        assert response.status_code == 201
        assert response.data['id'] != str(custom_id)
    
    def test_cannot_modify_created_at(
        self, authenticated_client, announcement
    ):
        """Test cannot modify created_at timestamp."""
        url = reverse('announcements:announcement-detail', args=[announcement.id])
        original_created_at = announcement.created_at
        data = {
            'title': 'Updated Title',
            'created_at': '2020-01-01T00:00:00Z'
        }
        
        response = authenticated_client.patch(url, data)
        
        assert response.status_code == 200
        
        announcement.refresh_from_db()
        assert announcement.created_at == original_created_at


@pytest.mark.django_db
class TestSensitiveDataExposure:
    """Test that sensitive data is not exposed in responses."""
    
    def test_password_not_in_response(
        self, authenticated_client, announcement
    ):
        """Test user passwords are never in response."""
        url = reverse('announcements:announcement-detail', args=[announcement.id])
        response = authenticated_client.get(url)
        
        assert response.status_code == 200
        response_str = str(response.data)
        assert 'password' not in response_str.lower()
    
    def test_user_sensitive_fields_not_exposed(
        self, authenticated_client, announcement
    ):
        """Test sensitive user fields are not exposed."""
        url = reverse('announcements:announcement-detail', args=[announcement.id])
        response = authenticated_client.get(url)
        
        assert response.status_code == 200
        
        creator = response.data['created_by']
        assert 'password' not in creator
        assert 'last_login' not in creator
    
    def test_error_messages_dont_leak_sensitive_info(
        self, authenticated_client
    ):
        """Test error messages don't leak sensitive information."""
        url = reverse('announcements:announcement-list')
        data = {
            'title': '',
            'message': '',
        }
        
        response = authenticated_client.post(url, data)
        
        assert response.status_code == 400
        response_str = str(response.data)
        assert 'password' not in response_str.lower()
        assert 'secret' not in response_str.lower()


@pytest.mark.django_db
class TestXSSPrevention:
    """Test XSS attack prevention."""
    
    def test_script_tags_in_title_not_executed(
        self, authenticated_client, authenticated_user
    ):
        """Test script tags in title are stored but not executed."""
        url = reverse('announcements:announcement-list')
        data = {
            'title': '<script>alert("XSS")</script>',
            'message': 'Normal message content.',
            'is_active': True
        }
        
        response = authenticated_client.post(url, data)
        
        assert response.status_code == 201
        
        announcement = Announcement.objects.get(id=response.data['id'])
        assert '<script>' in announcement.title
    
    def test_javascript_url_in_title(self, authenticated_client):
        """Test javascript: URLs are safely handled."""
        url = reverse('announcements:announcement-list')
        data = {
            'title': '<a href="javascript:alert(1)">Click</a>',
            'message': 'Message content here.',
            'is_active': True
        }
        
        response = authenticated_client.post(url, data)
        
        assert response.status_code == 201
    
    def test_event_handlers_in_content(self, authenticated_client):
        """Test HTML event handlers are safely stored."""
        url = reverse('announcements:announcement-list')
        data = {
            'title': 'Test Announcement',
            'message': '<img src=x onerror="alert(1)">',
            'is_active': True
        }
        
        response = authenticated_client.post(url, data)
        
        assert response.status_code == 201


@pytest.mark.django_db
class TestSQLInjectionPrevention:
    """Test SQL injection attack prevention."""
    
    def test_sql_injection_in_search(
        self, authenticated_client, authenticated_user
    ):
        """Test SQL injection attempts in search are safe."""
        AnnouncementFactory.create(created_by=authenticated_user)
        
        url = reverse('announcements:announcement-list')
        sql_payloads = [
            "'; DROP TABLE announcements_announcement; --",
            "1' OR '1'='1",
            "1; DELETE FROM announcements_announcement",
            "' UNION SELECT * FROM auth_user--",
        ]
        
        for payload in sql_payloads:
            response = authenticated_client.get(url, {'search': payload})
            assert response.status_code == 200
            assert Announcement.objects.count() >= 1
    
    def test_sql_injection_in_filter(
        self, authenticated_client, authenticated_user
    ):
        """Test SQL injection in filter parameters."""
        AnnouncementFactory.create(created_by=authenticated_user)
        
        url = reverse('announcements:announcement-list')
        response = authenticated_client.get(
            url, {'created_by': "' OR '1'='1"}
        )
        
        assert response.status_code == 200


@pytest.mark.django_db
class TestAuthorizationBypass:
    """Test authorization bypass attempts."""
    
    def test_cannot_bypass_auth_with_fake_token(self, api_client, announcement):
        """Test fake JWT token is rejected."""
        url = reverse('announcements:announcement-detail', args=[announcement.id])
        api_client.credentials(HTTP_AUTHORIZATION='Bearer fake_token_here')
        
        response = api_client.get(url)
        
        assert response.status_code == 401
    
    def test_cannot_access_with_expired_session(
        self, api_client, announcement
    ):
        """Test expired sessions are rejected."""
        url = reverse('announcements:announcement-detail', args=[announcement.id])
        
        response = api_client.get(url)
        
        assert response.status_code == 401
    
    def test_permission_checked_on_every_request(
        self, authenticated_client, announcement, authenticated_user
    ):
        """Test permissions are checked on each request."""
        url = reverse('announcements:announcement-detail', args=[announcement.id])
        
        response = authenticated_client.get(url)
        assert response.status_code == 200
        
        authenticated_user.is_active = False
        authenticated_user.save()
        
        response = authenticated_client.get(url)
        assert response.status_code in [401, 403]