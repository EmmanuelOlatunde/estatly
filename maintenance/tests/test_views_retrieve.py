# tests/test_views_retrieve.py

"""
Tests for maintenance ticket retrieve endpoint.

Coverage:
- Authentication/authorization
- Success paths
- Not found scenarios
- Cross-user access
"""

import pytest
import uuid
from django.urls import reverse
from .helpers import assert_ticket_data_matches


@pytest.mark.django_db
class TestMaintenanceTicketRetrieve:
    """Test GET /api/maintenance/tickets/{id}/ endpoint."""
    
    def test_unauthenticated_user_cannot_retrieve_ticket(self, api_client, ticket):
        """Test unauthenticated users get 401."""
        url = reverse('maintenance:maintenance-ticket-detail', args=[ticket.id])
        response = api_client.get(url)
        assert response.status_code == 401
    
    def test_user_can_retrieve_own_ticket(
        self, authenticated_client, ticket
    ):
        """Test user can retrieve their own ticket."""
        url = reverse('maintenance:maintenance-ticket-detail', args=[ticket.id])
        response = authenticated_client.get(url)
        
        assert response.status_code == 200
        assert_ticket_data_matches(response.data, ticket)
    
    def test_user_cannot_retrieve_other_users_ticket(
        self, authenticated_client, other_user_ticket
    ):
        """Test user cannot retrieve another user's ticket."""
        url = reverse('maintenance:maintenance-ticket-detail', args=[other_user_ticket.id])
        response = authenticated_client.get(url)
        assert response.status_code == 404
    
    def test_staff_can_retrieve_any_ticket(
        self, admin_client, other_user_ticket
    ):
        """Test staff users can retrieve any ticket."""
        url = reverse('maintenance:maintenance-ticket-detail', args=[other_user_ticket.id])
        response = admin_client.get(url)
        assert response.status_code == 200
    
    def test_retrieve_nonexistent_ticket_returns_404(
        self, authenticated_client
    ):
        """Test retrieving non-existent ticket returns 404."""
        fake_id = uuid.uuid4()
        url = reverse('maintenance:maintenance-ticket-detail', args=[fake_id])
        response = authenticated_client.get(url)
        assert response.status_code == 404
    
    def test_retrieve_returns_all_fields(
        self, authenticated_client, ticket
    ):
        """Test retrieve response contains all expected fields."""
        url = reverse('maintenance:maintenance-ticket-detail', args=[ticket.id])
        response = authenticated_client.get(url)
        
        assert response.status_code == 200
        expected_fields = [
            'id', 'title', 'description', 'category', 'category_display',
            'status', 'status_display', 'created_by', 'created_by_name',
            'unit', 'identifier', 'estate', 'estate_name', 'created_at',
            'updated_at', 'resolved_at', 'is_resolved', 'days_open'
        ]
        for field in expected_fields:
            assert field in response.data, f"Missing field: {field}"
    
    def test_retrieve_resolved_ticket_shows_resolved_at(
        self, authenticated_client, resolved_ticket
    ):
        """Test resolved ticket has resolved_at timestamp."""
        url = reverse('maintenance:maintenance-ticket-detail', args=[resolved_ticket.id])
        response = authenticated_client.get(url)
        
        assert response.status_code == 200
        assert response.data['status'] == 'RESOLVED'
        assert response.data['resolved_at'] is not None
        assert response.data['is_resolved'] is True
    
    def test_retrieve_open_ticket_has_no_resolved_at(
        self, authenticated_client, ticket
    ):
        """Test open ticket has null resolved_at."""
        url = reverse('maintenance:maintenance-ticket-detail', args=[ticket.id])
        response = authenticated_client.get(url)
        
        assert response.status_code == 200
        assert response.data['status'] == 'OPEN'
        assert response.data['resolved_at'] is None
        assert response.data['is_resolved'] is False
    
    def test_retrieve_calculates_days_open(
        self, authenticated_client, ticket
    ):
        """Test days_open is calculated correctly."""
        url = reverse('maintenance:maintenance-ticket-detail', args=[ticket.id])
        response = authenticated_client.get(url)
        
        assert response.status_code == 200
        assert 'days_open' in response.data
        assert isinstance(response.data['days_open'], int)
        assert response.data['days_open'] >= 0