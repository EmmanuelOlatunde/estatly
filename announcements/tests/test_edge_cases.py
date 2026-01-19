# tests/test_edge_cases.py

"""
Tests for edge cases and boundary conditions.

Coverage:
- Empty databases
- Maximum field lengths
- Unicode and special characters
- Concurrent operations
- Boundary values
"""

import pytest
from django.urls import reverse
from announcements.models import Announcement
from .factories import AnnouncementFactory


@pytest.mark.django_db
class TestEdgeCases:
    """Test edge cases and boundary conditions."""
    
    def setup_method(self):
        """Set up test data."""
        self.list_url = reverse('announcements:announcement-list')
    
    def test_list_with_no_announcements(self, authenticated_client):
        """Test listing when database is empty."""
        response = authenticated_client.get(self.list_url)
        
        assert response.status_code == 200
        assert response.data['count'] == 0
        assert len(response.data['results']) == 0
    
    def test_single_announcement_in_database(
        self, authenticated_client, authenticated_user
    ):
        """Test with exactly one announcement."""
        announcement = AnnouncementFactory.create(created_by=authenticated_user)
        
        response = authenticated_client.get(self.list_url)
        
        assert response.status_code == 200
        assert response.data['count'] == 1
        assert response.data['results'][0]['id'] == str(announcement.id)
    
    def test_maximum_title_length(self, authenticated_client):
        """Test title at maximum length (200 chars)."""
        data = {
            'title': 'A' * 200,
            'message': 'Valid message content here.',
            'is_active': True
        }
        response = authenticated_client.post(self.list_url, data)
        
        assert response.status_code == 201
    
    def test_title_exceeding_maximum_fails(self, authenticated_client):
        """Test title exceeding max_length fails."""
        data = {
            'title': 'A' * 201,
            'message': 'Valid message content here.',
            'is_active': True
        }
        response = authenticated_client.post(self.list_url, data)
        
        assert response.status_code == 400
        assert 'title' in response.data
    
    def test_very_long_message(self, authenticated_client):
        """Test very long message (5000+ chars)."""
        data = {
            'title': 'Test Announcement',
            'message': 'A' * 5000,
            'is_active': True
        }
        response = authenticated_client.post(self.list_url, data)
        
        assert response.status_code == 201
    
    def test_minimum_valid_title_length(self, authenticated_client):
        """Test minimum valid title (3 chars)."""
        data = {
            'title': 'ABC',
            'message': 'Valid message content here.',
            'is_active': True
        }
        response = authenticated_client.post(self.list_url, data)
        
        assert response.status_code == 201
    
    def test_minimum_valid_message_length(self, authenticated_client):
        """Test minimum valid message (10 chars)."""
        data = {
            'title': 'Test Announcement',
            'message': 'Ten chars!',
            'is_active': True
        }
        response = authenticated_client.post(self.list_url, data)
        
        assert response.status_code == 201
    
    def test_unicode_characters_in_title(self, authenticated_client):
        """Test unicode characters in title."""
        data = {
            'title': 'Announcement 公告 إعلان 📢',
            'message': 'Message with unicode content.',
            'is_active': True
        }
        response = authenticated_client.post(self.list_url, data)
        
        assert response.status_code == 201
        assert 'Announcement 公告 إعلان 📢' in response.data['title']
    
    def test_unicode_characters_in_message(self, authenticated_client):
        """Test unicode characters in message."""
        data = {
            'title': 'Test Announcement',
            'message': 'Message with unicode: 你好世界 مرحبا بالعالم 🌍',
            'is_active': True
        }
        response = authenticated_client.post(self.list_url, data)
        
        assert response.status_code == 201
        assert '你好世界' in response.data['message']
    
    def test_emoji_in_content(self, authenticated_client):
        """Test emoji characters are handled correctly."""
        data = {
            'title': 'Announcement 🎉 🚀',
            'message': 'Great news everyone! 🎊 🎈 🎁',
            'is_active': True
        }
        response = authenticated_client.post(self.list_url, data)
        
        assert response.status_code == 201
    
    def test_html_in_title_not_executed(
        self, authenticated_client, authenticated_user
    ):
        """Test HTML in title is not executed."""
        data = {
            'title': '<script>alert("xss")</script>Test',
            'message': 'Message content here.',
            'is_active': True
        }
        response = authenticated_client.post(self.list_url, data)
        
        assert response.status_code == 201
        
        announcement = Announcement.objects.get(id=response.data['id'])
        assert '<script>' in announcement.title
    
    def test_sql_injection_attempt_in_search(
        self, authenticated_client, authenticated_user
    ):
        """Test SQL injection attempts are safely handled."""
        AnnouncementFactory.create(created_by=authenticated_user)
        
        sql_injection = "'; DROP TABLE announcements_announcement; --"
        response = authenticated_client.get(
            self.list_url, {'search': sql_injection}
        )
        
        assert response.status_code == 200
        assert Announcement.objects.count() == 1
    
    def test_null_characters_in_input(self, authenticated_client):
        """Test null characters in input."""
        data = {
            'title': 'Test\x00Announcement',
            'message': 'Message with\x00null chars.',
            'is_active': True
        }
        response = authenticated_client.post(self.list_url, data)
        
        assert response.status_code in [201, 400]
    
    def test_newlines_in_message_preserved(
        self, authenticated_client, authenticated_user
    ):
        """Test newlines in message are preserved."""
        data = {
            'title': 'Test Announcement',
            'message': 'Line 1\nLine 2\nLine 3',
            'is_active': True
        }
        response = authenticated_client.post(self.list_url, data)
        
        assert response.status_code == 201
        
        announcement = Announcement.objects.get(id=response.data['id'])
        assert 'Line 1\nLine 2\nLine 3' == announcement.message
    
    def test_tabs_in_message_preserved(self, authenticated_client):
        """Test tabs in message are preserved."""
        data = {
            'title': 'Test Announcement',
            'message': 'Column1\tColumn2\tColumn3',
            'is_active': True
        }
        response = authenticated_client.post(self.list_url, data)
        
        assert response.status_code == 201
    
    def test_mixed_case_boolean_parameters(
        self, authenticated_client, authenticated_user
    ):
        """Test mixed case boolean parameters are handled."""
        AnnouncementFactory.create(created_by=authenticated_user, is_active=True)
        
        for value in ['True', 'TRUE', 'tRuE', '1', 'yes']:
            response = authenticated_client.get(
                self.list_url, {'is_active': value}
            )
            assert response.status_code == 200
    
    def test_create_many_announcements(
        self, authenticated_client, authenticated_user
    ):
        """Test creating many announcements doesn't cause issues."""
        for i in range(100):
            data = {
                'title': f'Announcement {i}',
                'message': f'Message content for announcement {i}.',
                'is_active': True
            }
            response = authenticated_client.post(self.list_url, data)
            assert response.status_code == 201
        
        assert Announcement.objects.count() == 100
    
    def test_rapid_updates_to_same_announcement(
        self, authenticated_client, announcement
    ):
        """Test rapid successive updates work correctly."""
        url = reverse('announcements:announcement-detail', args=[announcement.id])
        
        for i in range(10):
            data = {'title': f'Update {i}'}
            response = authenticated_client.patch(url, data)
            assert response.status_code == 200
        
        announcement.refresh_from_db()
        assert announcement.title == 'Update 9'
    
    def test_announcement_with_only_spaces_in_middle(
        self, authenticated_client
    ):
        """Test title/message with spaces in middle."""
        data = {
            'title': 'Test     Announcement',
            'message': 'Message     with     spaces.',
            'is_active': True
        }
        response = authenticated_client.post(self.list_url, data)
        
        assert response.status_code == 201
    
    def test_empty_string_vs_null_handling(self, authenticated_client):
        """Test empty string handling."""
        data = {
            'title': '',
            'message': 'Valid message.',
            'is_active': True
        }
        response = authenticated_client.post(self.list_url, data)
        
        assert response.status_code == 400
        assert 'title' in response.data