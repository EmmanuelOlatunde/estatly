# tests/test_pagination_ordering.py

"""
Tests for announcement pagination and ordering.

Coverage:
- Pagination metadata
- Page size limits
- Page navigation
- Ordering by different fields
- Invalid pagination parameters
"""

import pytest
from django.urls import reverse
from .factories import AnnouncementFactory


@pytest.mark.django_db
class TestAnnouncementPagination:
    """Test pagination for announcement list endpoint."""
    
    def setup_method(self):
        """Set up test data."""
        self.url = reverse('announcements:announcement-list')
    
    def test_pagination_metadata_present(
        self, authenticated_client, authenticated_user
    ):
        """Test pagination metadata is present in response."""
        AnnouncementFactory.create_batch(5, created_by=authenticated_user)
        
        response = authenticated_client.get(self.url)
        
        assert response.status_code == 200
        assert 'count' in response.data
        assert 'results' in response.data
    
    def test_default_page_size(
        self, authenticated_client, authenticated_user
    ):
        """Test default page size returns expected number of results."""
        AnnouncementFactory.create_batch(25, created_by=authenticated_user)
        
        response = authenticated_client.get(self.url)
        
        assert response.status_code == 200
        assert response.data['count'] == 25
    
    def test_custom_page_size(
        self, authenticated_client, authenticated_user
    ):
        """Test custom page_size parameter works."""
        AnnouncementFactory.create_batch(20, created_by=authenticated_user)
        
        response = authenticated_client.get(
            self.url, {'page_size': '5'}
        )
        
        assert response.status_code == 200
        assert len(response.data['results']) == 5
    
    def test_page_navigation(
        self, authenticated_client, authenticated_user
    ):
        """Test page parameter for navigation."""
        announcements = AnnouncementFactory.create_batch(
            15, created_by=authenticated_user
        )
        
        response = authenticated_client.get(
            self.url, {'page': '1', 'page_size': '10'}
        )
        
        assert response.status_code == 200
        assert len(response.data['results']) == 10
        
        response = authenticated_client.get(
            self.url, {'page': '2', 'page_size': '10'}
        )
        
        assert response.status_code == 200
        assert len(response.data['results']) == 5
    
    def test_invalid_page_number_returns_404(
        self, authenticated_client, authenticated_user
    ):
        """Test invalid page number returns 404."""
        AnnouncementFactory.create_batch(5, created_by=authenticated_user)
        
        response = authenticated_client.get(
            self.url, {'page': '999'}
        )
        
        assert response.status_code == 404
    
    def test_zero_page_number_returns_404(
        self, authenticated_client, authenticated_user
    ):
        """Test page number 0 returns 404."""
        AnnouncementFactory.create_batch(5, created_by=authenticated_user)
        
        response = authenticated_client.get(
            self.url, {'page': '0'}
        )
        
        assert response.status_code == 404
    
    def test_negative_page_number_returns_404(
        self, authenticated_client, authenticated_user
    ):
        """Test negative page number returns 404."""
        AnnouncementFactory.create_batch(5, created_by=authenticated_user)
        
        response = authenticated_client.get(
            self.url, {'page': '-1'}
        )
        
        assert response.status_code == 404
    
    def test_count_is_accurate(
        self, authenticated_client, authenticated_user
    ):
        """Test count field reflects total number of results."""
        AnnouncementFactory.create_batch(37, created_by=authenticated_user)
        
        response = authenticated_client.get(self.url)
        
        assert response.status_code == 200
        assert response.data['count'] == 37


@pytest.mark.django_db
class TestAnnouncementOrdering:
    """Test ordering for announcement list endpoint."""
    
    def setup_method(self):
        """Set up test data."""
        self.url = reverse('announcements:announcement-list')
    
    def test_default_ordering_created_at_desc(
        self, authenticated_client, authenticated_user
    ):
        """Test default ordering is by created_at descending."""
        announcements = [
            AnnouncementFactory.create(created_by=authenticated_user)
            for _ in range(5)
        ]
        
        response = authenticated_client.get(self.url)
        
        assert response.status_code == 200
        results = response.data['results']
        
        for i in range(len(results) - 1):
            current_date = results[i]['created_at']
            next_date = results[i + 1]['created_at']
            assert current_date >= next_date
    
    def test_order_by_created_at_ascending(
        self, authenticated_client, authenticated_user
    ):
        """Test ordering by created_at ascending."""
        announcements = [
            AnnouncementFactory.create(created_by=authenticated_user)
            for _ in range(5)
        ]
        
        response = authenticated_client.get(
            self.url, {'ordering': 'created_at'}
        )
        
        assert response.status_code == 200
        results = response.data['results']
        
        for i in range(len(results) - 1):
            current_date = results[i]['created_at']
            next_date = results[i + 1]['created_at']
            assert current_date <= next_date
    
    def test_order_by_updated_at_descending(
        self, authenticated_client, authenticated_user
    ):
        """Test ordering by updated_at descending."""
        announcements = [
            AnnouncementFactory.create(created_by=authenticated_user)
            for _ in range(5)
        ]
        
        response = authenticated_client.get(
            self.url, {'ordering': '-updated_at'}
        )
        
        assert response.status_code == 200
        results = response.data['results']
        
        for i in range(len(results) - 1):
            current_date = results[i]['updated_at']
            next_date = results[i + 1]['updated_at']
            assert current_date >= next_date
    
    def test_order_by_title_ascending(
        self, authenticated_client, authenticated_user
    ):
        """Test ordering by title ascending."""
        AnnouncementFactory.create(
            created_by=authenticated_user, title="Zebra Announcement"
        )
        AnnouncementFactory.create(
            created_by=authenticated_user, title="Alpha Announcement"
        )
        AnnouncementFactory.create(
            created_by=authenticated_user, title="Beta Announcement"
        )
        
        response = authenticated_client.get(
            self.url, {'ordering': 'title'}
        )
        
        assert response.status_code == 200
        results = response.data['results']
        
        assert results[0]['title'] == "Alpha Announcement"
        assert results[1]['title'] == "Beta Announcement"
        assert results[2]['title'] == "Zebra Announcement"
    
    def test_order_by_title_descending(
        self, authenticated_client, authenticated_user
    ):
        """Test ordering by title descending."""
        AnnouncementFactory.create(
            created_by=authenticated_user, title="Alpha Announcement"
        )
        AnnouncementFactory.create(
            created_by=authenticated_user, title="Beta Announcement"
        )
        AnnouncementFactory.create(
            created_by=authenticated_user, title="Zebra Announcement"
        )
        
        response = authenticated_client.get(
            self.url, {'ordering': '-title'}
        )
        
        assert response.status_code == 200
        results = response.data['results']
        
        assert results[0]['title'] == "Zebra Announcement"
        assert results[1]['title'] == "Beta Announcement"
        assert results[2]['title'] == "Alpha Announcement"
    
    def test_invalid_ordering_field_ignored(
        self, authenticated_client, authenticated_user
    ):
        """Test invalid ordering field is ignored."""
        AnnouncementFactory.create_batch(3, created_by=authenticated_user)
        
        response = authenticated_client.get(
            self.url, {'ordering': 'invalid_field'}
        )
        
        assert response.status_code == 200
    
    def test_multiple_ordering_fields(
        self, authenticated_client, authenticated_user
    ):
        """Test ordering by multiple fields."""
        response = authenticated_client.get(
            self.url, {'ordering': '-created_at,title'}
        )
        
        assert response.status_code == 200