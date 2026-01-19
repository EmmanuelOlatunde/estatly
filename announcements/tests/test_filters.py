# tests/test_filters.py

"""
Tests for announcement filtering and search functionality.

Coverage:
- Filter by is_active
- Filter by created_by
- Search in title and message
- Multiple filters combined
- Invalid filter values
"""

import pytest
from django.urls import reverse
from .factories import AnnouncementFactory


@pytest.mark.django_db
class TestAnnouncementFilters:
    """Test filtering for announcement list endpoint."""
    
    def setup_method(self):
        """Set up test data."""
        self.url = reverse('announcements:announcement-list')
    
    def test_filter_by_is_active_true(
        self, authenticated_client, authenticated_user
    ):
        """Test filter by active status."""
        active = AnnouncementFactory.create(
            created_by=authenticated_user, is_active=True
        )
        inactive = AnnouncementFactory.create(
            created_by=authenticated_user, is_active=False
        )
        
        response = authenticated_client.get(
            self.url, {'is_active': 'true'}
        )
        
        assert response.status_code == 200
        result_ids = [item['id'] for item in response.data['results']]
        assert str(active.id) in result_ids
        assert str(inactive.id) not in result_ids
    
    def test_filter_by_is_active_false(
        self, authenticated_client, authenticated_user
    ):
        """Test filter by inactive status."""
        active = AnnouncementFactory.create(
            created_by=authenticated_user, is_active=True
        )
        inactive = AnnouncementFactory.create(
            created_by=authenticated_user, is_active=False
        )
        
        response = authenticated_client.get(
            self.url, {'is_active': 'false', 'include_inactive': 'true'}
        )
        
        assert response.status_code == 200
        result_ids = [item['id'] for item in response.data['results']]
        assert str(inactive.id) in result_ids
        assert str(active.id) not in result_ids
    
    def test_filter_by_created_by(
        self, authenticated_client, authenticated_user, other_user
    ):
        """Test filter by creator user ID."""
        own = AnnouncementFactory.create(created_by=authenticated_user)
        other = AnnouncementFactory.create(created_by=other_user)
        
        response = authenticated_client.get(
            self.url, {'created_by': str(authenticated_user.id)}
        )
        
        assert response.status_code == 200
        result_ids = [item['id'] for item in response.data['results']]
        assert str(own.id) in result_ids
    
    def test_search_in_title(
        self, authenticated_client, authenticated_user
    ):
        """Test search finds announcements by title."""
        matching = AnnouncementFactory.create(
            created_by=authenticated_user,
            title="Important Security Update"
        )
        non_matching = AnnouncementFactory.create(
            created_by=authenticated_user,
            title="Regular Maintenance"
        )
        
        response = authenticated_client.get(
            self.url, {'search': 'Security'}
        )
        
        assert response.status_code == 200
        result_ids = [item['id'] for item in response.data['results']]
        assert str(matching.id) in result_ids
        assert str(non_matching.id) not in result_ids
    
    def test_search_in_message(
        self, authenticated_client, authenticated_user
    ):
        """Test search finds announcements by message content."""
        matching = AnnouncementFactory.create(
            created_by=authenticated_user,
            message="This contains the keyword security in the message."
        )
        non_matching = AnnouncementFactory.create(
            created_by=authenticated_user,
            message="This is about maintenance only."
        )
        
        response = authenticated_client.get(
            self.url, {'search': 'security'}
        )
        
        assert response.status_code == 200
        result_ids = [item['id'] for item in response.data['results']]
        assert str(matching.id) in result_ids
        assert str(non_matching.id) not in result_ids
    
    def test_search_is_case_insensitive(
        self, authenticated_client, authenticated_user
    ):
        """Test search is case insensitive."""
        announcement = AnnouncementFactory.create(
            created_by=authenticated_user,
            title="Important Security Update"
        )
        
        for search_term in ['security', 'SECURITY', 'Security', 'sEcUrItY']:
            response = authenticated_client.get(
                self.url, {'search': search_term}
            )
            
            assert response.status_code == 200
            result_ids = [item['id'] for item in response.data['results']]
            assert str(announcement.id) in result_ids
    
    def test_search_partial_match(
        self, authenticated_client, authenticated_user
    ):
        """Test search matches partial words."""
        announcement = AnnouncementFactory.create(
            created_by=authenticated_user,
            title="Security Update"
        )
        
        response = authenticated_client.get(
            self.url, {'search': 'Sec'}
        )
        
        assert response.status_code == 200
        result_ids = [item['id'] for item in response.data['results']]
        assert str(announcement.id) in result_ids
    
    def test_multiple_filters_combined(
        self, authenticated_client, authenticated_user
    ):
        """Test multiple filters work together."""
        matching = AnnouncementFactory.create(
            created_by=authenticated_user,
            title="Active Security Update",
            is_active=True
        )
        inactive_security = AnnouncementFactory.create(
            created_by=authenticated_user,
            title="Inactive Security Update",
            is_active=False
        )
        active_other = AnnouncementFactory.create(
            created_by=authenticated_user,
            title="Active Maintenance",
            is_active=True
        )
        
        response = authenticated_client.get(
            self.url, {
                'search': 'Security',
                'is_active': 'true'
            }
        )
        
        assert response.status_code == 200
        result_ids = [item['id'] for item in response.data['results']]
        assert str(matching.id) in result_ids
        assert str(inactive_security.id) not in result_ids
        assert str(active_other.id) not in result_ids
    
    def test_empty_search_returns_all(
        self, authenticated_client, authenticated_user
    ):
        """Test empty search parameter returns all results."""
        announcements = [
            AnnouncementFactory.create(created_by=authenticated_user)
            for _ in range(3)
        ]
        
        response = authenticated_client.get(
            self.url, {'search': ''}
        )
        
        assert response.status_code == 200
        assert len(response.data['results']) == 3
    
    def test_no_matches_returns_empty_list(
        self, authenticated_client, authenticated_user
    ):
        """Test search with no matches returns empty results."""
        AnnouncementFactory.create(
            created_by=authenticated_user,
            title="Some Announcement"
        )
        
        response = authenticated_client.get(
            self.url, {'search': 'NonExistentTerm'}
        )
        
        assert response.status_code == 200
        assert len(response.data['results']) == 0
    
    def test_search_with_special_characters(
        self, authenticated_client, authenticated_user
    ):
        """Test search handles special characters."""
        announcement = AnnouncementFactory.create(
            created_by=authenticated_user,
            title="Update & Maintenance"
        )
        
        response = authenticated_client.get(
            self.url, {'search': '&'}
        )
        
        assert response.status_code == 200