# tests/test_views_list.py

"""
Tests for maintenance ticket list endpoint.

Coverage:
- Authentication/authorization
- Success paths
- Filtering and search
- Pagination
- Ordering
"""

import pytest
from django.urls import reverse
from .factories import MaintenanceTicketFactory
from .helpers import assert_pagination_response, assert_no_sensitive_data_in_response


@pytest.mark.django_db
class TestMaintenanceTicketList:
    """Test GET /api/maintenance/tickets/ endpoint."""
    
    def setup_method(self):
        """Setup common test data."""
        self.url = reverse('maintenance:maintenance-ticket-list')
    
    def test_unauthenticated_user_cannot_list_tickets(self, api_client):
        """Test unauthenticated users get 401."""
        response = api_client.get(self.url)
        assert response.status_code == 401
    
    def test_authenticated_user_can_list_own_tickets(
        self, authenticated_client, authenticated_user, estate
    ):
        """Test authenticated users can list their own tickets."""
        MaintenanceTicketFactory.create_batch(
            3, created_by=authenticated_user, estate=estate
        )
        
        response = authenticated_client.get(self.url)
        assert response.status_code == 200
        assert_pagination_response(response.data)
        assert response.data['count'] == 3
        assert len(response.data['results']) == 3
    
    def test_user_cannot_see_other_users_tickets(
        self, authenticated_client, other_user, estate
    ):
        """Test users only see their own tickets."""
        MaintenanceTicketFactory.create_batch(3, created_by=other_user, estate=estate)
        
        response = authenticated_client.get(self.url)
        assert response.status_code == 200
        assert response.data['count'] == 0
        assert len(response.data['results']) == 0
    
    def test_staff_user_can_see_all_tickets(
        self, admin_client, authenticated_user, other_user, estate
    ):
        """Test staff users can see all tickets."""
        MaintenanceTicketFactory.create_batch(
            2, created_by=authenticated_user, estate=estate
        )
        MaintenanceTicketFactory.create_batch(
            3, created_by=other_user, estate=estate
        )
        
        response = admin_client.get(self.url)
        assert response.status_code == 200
        assert response.data['count'] == 5
    
    def test_empty_list_returns_empty_results(self, authenticated_client):
        """Test empty queryset returns empty list."""
        response = authenticated_client.get(self.url)
        assert response.status_code == 200
        assert response.data['count'] == 0
        assert response.data['results'] == []
    
    def test_list_returns_correct_fields(
        self, authenticated_client, authenticated_user, estate
    ):
        """Test list response contains expected fields."""
        MaintenanceTicketFactory.create(created_by=authenticated_user, estate=estate)
        
        response = authenticated_client.get(self.url)
        assert response.status_code == 200
        
        ticket_data = response.data['results'][0]
        expected_fields = [
            'id', 'title', 'category', 'category_display',
            'status', 'status_display', 'estate_name',
            'created_at', 'updated_at'
        ]
        for field in expected_fields:
            assert field in ticket_data
    
    def test_no_sensitive_data_in_list_response(
        self, authenticated_client, authenticated_user, estate
    ):
        """Test list response does not expose sensitive data."""
        MaintenanceTicketFactory.create(created_by=authenticated_user, estate=estate)
        
        response = authenticated_client.get(self.url)
        assert response.status_code == 200
        assert_no_sensitive_data_in_response(response.data['results'])
    
    def test_pagination_first_page(
        self, authenticated_client, authenticated_user, estate
    ):
        """Test pagination returns correct first page."""
        MaintenanceTicketFactory.create_batch(
            15, created_by=authenticated_user, estate=estate
        )
        
        response = authenticated_client.get(self.url, {'page': 1})
        assert response.status_code == 200
        assert response.data['count'] == 15
        assert len(response.data['results']) <= 10
        assert response.data['next'] is not None
        assert response.data['previous'] is None
    
    def test_pagination_page_size_parameter(
        self, authenticated_client, authenticated_user, estate
    ):
        """Test custom page_size parameter works."""
        MaintenanceTicketFactory.create_batch(
            10, created_by=authenticated_user, estate=estate
        )
        
        response = authenticated_client.get(self.url, {'page_size': 5})
        assert response.status_code == 200
        assert len(response.data['results']) == 5
    
    def test_ordering_by_created_at_desc(
        self, authenticated_client, authenticated_user, estate
    ):
        """Test ordering by created_at descending (default)."""
        tickets = MaintenanceTicketFactory.create_batch(
            3, created_by=authenticated_user, estate=estate
        )
        
        response = authenticated_client.get(self.url)
        assert response.status_code == 200
        
        result_ids = [item['id'] for item in response.data['results']]
        expected_ids = [str(t.id) for t in sorted(
            tickets, key=lambda x: x.created_at, reverse=True
        )]
        assert result_ids == expected_ids
    
    def test_ordering_by_created_at_asc(
        self, authenticated_client, authenticated_user, estate
    ):
        """Test ordering by created_at ascending."""
        MaintenanceTicketFactory.create_batch(
            3, created_by=authenticated_user, estate=estate
        )
        
        response = authenticated_client.get(self.url, {'ordering': 'created_at'})
        assert response.status_code == 200
        
        dates = [item['created_at'] for item in response.data['results']]
        assert dates == sorted(dates)
    
    def test_search_by_title(
        self, authenticated_client, authenticated_user, estate
    ):
        """Test search in title field."""
        MaintenanceTicketFactory.create(
            title="Water leak in basement",
            created_by=authenticated_user,
            estate=estate
        )
        MaintenanceTicketFactory.create(
            title="Broken elevator",
            created_by=authenticated_user,
            estate=estate
        )
        
        response = authenticated_client.get(self.url, {'search': 'water'})
        assert response.status_code == 200
        assert response.data['count'] == 1
        assert 'water' in response.data['results'][0]['title'].lower()
    
    def test_search_by_description(
        self, authenticated_client, authenticated_user, estate
    ):
        """Test search in description field."""
        MaintenanceTicketFactory.create(
            title="Issue",
            description="The water pipe is broken",
            created_by=authenticated_user,
            estate=estate
        )
        MaintenanceTicketFactory.create(
            title="Problem",
            description="The door needs fixing",
            created_by=authenticated_user,
            estate=estate
        )
        
        response = authenticated_client.get(self.url, {'search': 'pipe'})
        assert response.status_code == 200
        assert response.data['count'] == 1
    
    def test_search_case_insensitive(
        self, authenticated_client, authenticated_user, estate
    ):
        """Test search is case insensitive."""
        MaintenanceTicketFactory.create(
            title="URGENT WATER ISSUE",
            created_by=authenticated_user,
            estate=estate
        )
        
        response = authenticated_client.get(self.url, {'search': 'urgent'})
        assert response.status_code == 200
        assert response.data['count'] == 1