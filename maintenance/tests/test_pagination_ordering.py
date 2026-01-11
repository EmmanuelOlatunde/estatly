# tests/test_pagination_ordering.py

"""
Tests for pagination and ordering functionality.

Coverage:
- Page navigation
- Page size limits
- Invalid page numbers
- Ordering by different fields
- Ascending/descending order
"""

import pytest
from django.urls import reverse
from .factories import MaintenanceTicketFactory


@pytest.mark.django_db
class TestPagination:
    """Test pagination functionality."""
    
    def setup_method(self):
        """Setup common test data."""
        self.url = reverse('maintenance:maintenance-ticket-list')
    
    def test_default_pagination_applied(
        self, authenticated_client, authenticated_user, estate
    ):
        """Test default pagination is applied to results."""
        MaintenanceTicketFactory.create_batch(
            15, created_by=authenticated_user, estate=estate
        )
        
        response = authenticated_client.get(self.url)
        assert response.status_code == 200
        assert 'count' in response.data
        assert 'next' in response.data
        assert 'previous' in response.data
        assert 'results' in response.data
        assert response.data['count'] == 15
    
    def test_first_page_has_no_previous(
        self, authenticated_client, authenticated_user, estate
    ):
        """Test first page has no previous link."""
        MaintenanceTicketFactory.create_batch(
            15, created_by=authenticated_user, estate=estate
        )
        
        response = authenticated_client.get(self.url, {'page': 1})
        assert response.status_code == 200
        assert response.data['previous'] is None
        assert response.data['next'] is not None
    
    def test_last_page_has_no_next(
        self, authenticated_client, authenticated_user, estate
    ):
        """Test last page has no next link."""
        MaintenanceTicketFactory.create_batch(
            25, created_by=authenticated_user, estate=estate
        )
        
        response = authenticated_client.get(self.url, {'page': 3})
        assert response.status_code == 200
        assert response.data['next'] is None
    
    def test_middle_page_has_both_links(
        self, authenticated_client, authenticated_user, estate
    ):
        """Test middle page has both previous and next links."""
        MaintenanceTicketFactory.create_batch(
            30, created_by=authenticated_user, estate=estate
        )
        
        response = authenticated_client.get(self.url, {'page': 2})
        assert response.status_code == 200
        assert response.data['previous'] is not None
        assert response.data['next'] is not None
    
    def test_custom_page_size(
        self, authenticated_client, authenticated_user, estate
    ):
        """Test custom page_size parameter works."""
        MaintenanceTicketFactory.create_batch(
            20, created_by=authenticated_user, estate=estate
        )
        
        response = authenticated_client.get(self.url, {'page_size': 5})
        assert response.status_code == 200
        assert len(response.data['results']) == 5
    
    def test_page_size_larger_than_count(
        self, authenticated_client, authenticated_user, estate
    ):
        """Test page_size larger than total count returns all results."""
        MaintenanceTicketFactory.create_batch(
            5, created_by=authenticated_user, estate=estate
        )
        
        response = authenticated_client.get(self.url, {'page_size': 100})
        assert response.status_code == 200
        assert len(response.data['results']) == 5
    
    def test_invalid_page_number_returns_404(
        self, authenticated_client, authenticated_user, estate
    ):
        """Test invalid page number returns 404."""
        MaintenanceTicketFactory.create_batch(
            10, created_by=authenticated_user, estate=estate
        )
        
        response = authenticated_client.get(self.url, {'page': 999})
        assert response.status_code == 404
    
    def test_page_zero_invalid(
        self, authenticated_client, authenticated_user, estate
    ):
        """Test page 0 is invalid."""
        MaintenanceTicketFactory.create_batch(
            10, created_by=authenticated_user, estate=estate
        )
        
        response = authenticated_client.get(self.url, {'page': 0})
        assert response.status_code == 404
    
    def test_negative_page_number_invalid(
        self, authenticated_client, authenticated_user, estate
    ):
        """Test negative page number is invalid."""
        MaintenanceTicketFactory.create_batch(
            10, created_by=authenticated_user, estate=estate
        )
        
        response = authenticated_client.get(self.url, {'page': -1})
        assert response.status_code == 404
    
    def test_non_numeric_page_invalid(
        self, authenticated_client, authenticated_user, estate
    ):
        """Test non-numeric page value is invalid."""
        MaintenanceTicketFactory.create_batch(
            10, created_by=authenticated_user, estate=estate
        )
        
        response = authenticated_client.get(self.url, {'page': 'abc'})
        assert response.status_code == 404
    
    def test_count_is_accurate(
        self, authenticated_client, authenticated_user, estate
    ):
        """Test count field shows accurate total."""
        MaintenanceTicketFactory.create_batch(
            37, created_by=authenticated_user, estate=estate
        )
        
        response = authenticated_client.get(self.url)
        assert response.status_code == 200
        assert response.data['count'] == 37
    
    def test_empty_page_beyond_range(
        self, authenticated_client, authenticated_user, estate
    ):
        """Test requesting page beyond available range."""
        MaintenanceTicketFactory.create_batch(
            5, created_by=authenticated_user, estate=estate
        )
        
        response = authenticated_client.get(self.url, {'page': 10})
        assert response.status_code == 404


@pytest.mark.django_db
class TestOrdering:
    """Test ordering functionality."""
    
    def setup_method(self):
        """Setup common test data."""
        self.url = reverse('maintenance:maintenance-ticket-list')
    
    def test_default_ordering_by_created_at_desc(
        self, authenticated_client, authenticated_user, estate
    ):
        """Test default ordering is by created_at descending."""
        tickets = MaintenanceTicketFactory.create_batch(
            5, created_by=authenticated_user, estate=estate
        )
        
        response = authenticated_client.get(self.url)
        assert response.status_code == 200
        
        result_ids = [item['id'] for item in response.data['results']]
        expected_ids = [str(t.id) for t in sorted(
            tickets, key=lambda x: x.created_at, reverse=True
        )]
        assert result_ids == expected_ids
    
    def test_order_by_created_at_asc(
        self, authenticated_client, authenticated_user, estate
    ):
        """Test ordering by created_at ascending."""
        MaintenanceTicketFactory.create_batch(
            5, created_by=authenticated_user, estate=estate
        )
        
        response = authenticated_client.get(self.url, {'ordering': 'created_at'})
        assert response.status_code == 200
        
        dates = [item['created_at'] for item in response.data['results']]
        assert dates == sorted(dates)
    
    def test_order_by_updated_at_desc(
        self, authenticated_client, authenticated_user, estate
    ):
        """Test ordering by updated_at descending."""
        MaintenanceTicketFactory.create_batch(
            5, created_by=authenticated_user, estate=estate
        )
        
        response = authenticated_client.get(self.url, {'ordering': '-updated_at'})
        assert response.status_code == 200
        
        dates = [item['updated_at'] for item in response.data['results']]
        assert dates == sorted(dates, reverse=True)
    
    def test_order_by_status(
        self, authenticated_client, authenticated_user, estate
    ):
        """Test ordering by status field."""
        MaintenanceTicketFactory.create(
            created_by=authenticated_user, estate=estate, status='RESOLVED'
        )
        MaintenanceTicketFactory.create(
            created_by=authenticated_user, estate=estate, status='OPEN'
        )
        
        response = authenticated_client.get(self.url, {'ordering': 'status'})
        assert response.status_code == 200
        assert len(response.data['results']) == 2
    
    def test_order_by_category(
        self, authenticated_client, authenticated_user, estate
    ):
        """Test ordering by category field."""
        MaintenanceTicketFactory.create(
            created_by=authenticated_user, estate=estate, category='WATER'
        )
        MaintenanceTicketFactory.create(
            created_by=authenticated_user, estate=estate, category='ELECTRICITY'
        )
        
        response = authenticated_client.get(self.url, {'ordering': 'category'})
        assert response.status_code == 200
        assert len(response.data['results']) == 2
    
    def test_invalid_ordering_field_ignored(
        self, authenticated_client, authenticated_user, estate
    ):
        """Test invalid ordering field is ignored."""
        MaintenanceTicketFactory.create_batch(
            3, created_by=authenticated_user, estate=estate
        )
        
        response = authenticated_client.get(self.url, {'ordering': 'invalid_field'})
        assert response.status_code == 200
    
    def test_ordering_with_pagination(
        self, authenticated_client, authenticated_user, estate
    ):
        """Test ordering works correctly with pagination."""
        MaintenanceTicketFactory.create_batch(
            15, created_by=authenticated_user, estate=estate
        )
        
        response = authenticated_client.get(
            self.url,
            {'ordering': 'created_at', 'page_size': 5}
        )
        assert response.status_code == 200
        assert len(response.data['results']) == 5
        
        dates = [item['created_at'] for item in response.data['results']]
        assert dates == sorted(dates)
    
    def test_ordering_with_filters(
        self, authenticated_client, authenticated_user, estate
    ):
        """Test ordering works with filters applied."""
        MaintenanceTicketFactory.create_batch(
            3, created_by=authenticated_user, estate=estate, category='WATER'
        )
        MaintenanceTicketFactory.create_batch(
            2, created_by=authenticated_user, estate=estate, category='ELECTRICITY'
        )
        
        response = authenticated_client.get(
            self.url,
            {'category': 'WATER', 'ordering': '-created_at'}
        )
        assert response.status_code == 200
        assert response.data['count'] == 3