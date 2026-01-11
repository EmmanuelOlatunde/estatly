# tests/test_custom_actions.py

"""
Tests for maintenance ticket custom actions.

Coverage:
- Resolve action
- Reopen action
- Statistics action
- Authorization for actions
"""

import pytest
from django.urls import reverse
from django.utils import timezone
from maintenance.models import MaintenanceTicket
from .factories import MaintenanceTicketFactory


@pytest.mark.django_db
class TestResolveAction:
    """Test POST /api/maintenance/tickets/{id}/resolve/ action."""
    
    def test_unauthenticated_user_cannot_resolve(self, api_client, ticket):
        """Test unauthenticated users get 401."""
        url = reverse('maintenance:maintenance-ticket-resolve', args=[ticket.id])
        response = api_client.post(url)
        assert response.status_code == 401
    
    def test_user_can_resolve_own_ticket(
        self, authenticated_client, ticket
    ):
        """Test user can resolve their own ticket."""
        url = reverse('maintenance:maintenance-ticket-resolve', args=[ticket.id])
        response = authenticated_client.post(url)
        
        assert response.status_code == 200
        assert response.data['status'] == 'RESOLVED'
        assert response.data['resolved_at'] is not None
        
        ticket.refresh_from_db()
        assert ticket.status == 'RESOLVED'
        assert ticket.resolved_at is not None
    
    def test_user_cannot_resolve_other_users_ticket(
        self, authenticated_client, other_user_ticket
    ):
        """Test user cannot resolve another user's ticket."""
        url = reverse('maintenance:maintenance-ticket-resolve', args=[other_user_ticket.id])
        response = authenticated_client.post(url)
        assert response.status_code == 404
    
    def test_staff_can_resolve_any_ticket(
        self, admin_client, other_user_ticket
    ):
        """Test staff can resolve any ticket."""
        url = reverse('maintenance:maintenance-ticket-resolve', args=[other_user_ticket.id])
        response = admin_client.post(url)
        
        assert response.status_code == 200
        assert response.data['status'] == 'RESOLVED'
    
    def test_resolve_already_resolved_ticket_fails(
        self, authenticated_client, resolved_ticket
    ):
        """Test resolving already resolved ticket returns error."""
        url = reverse('maintenance:maintenance-ticket-resolve', args=[resolved_ticket.id])
        response = authenticated_client.post(url)
        
        assert response.status_code == 400
        assert 'error' in response.data
    
    def test_resolve_sets_resolved_at_timestamp(
        self, authenticated_client, ticket
    ):
        """Test resolve action sets resolved_at timestamp."""
        before_resolve = timezone.now()
        
        url = reverse('maintenance:maintenance-ticket-resolve', args=[ticket.id])
        response = authenticated_client.post(url)
        
        after_resolve = timezone.now()
        
        assert response.status_code == 200
        ticket.refresh_from_db()
        assert ticket.resolved_at >= before_resolve
        assert ticket.resolved_at <= after_resolve


@pytest.mark.django_db
class TestReopenAction:
    """Test POST /api/maintenance/tickets/{id}/reopen/ action."""
    
    def test_unauthenticated_user_cannot_reopen(self, api_client, resolved_ticket):
        """Test unauthenticated users get 401."""
        url = reverse('maintenance:maintenance-ticket-reopen', args=[resolved_ticket.id])
        response = api_client.post(url)
        assert response.status_code == 401
    
    def test_user_can_reopen_own_resolved_ticket(
        self, authenticated_client, resolved_ticket
    ):
        """Test user can reopen their own resolved ticket."""
        url = reverse('maintenance:maintenance-ticket-reopen', args=[resolved_ticket.id])
        response = authenticated_client.post(url)
        
        assert response.status_code == 200
        assert response.data['status'] == 'OPEN'
        assert response.data['resolved_at'] is None
        
        resolved_ticket.refresh_from_db()
        assert resolved_ticket.status == 'OPEN'
        assert resolved_ticket.resolved_at is None
    
    def test_user_cannot_reopen_other_users_ticket(
        self, authenticated_client, other_user, estate
    ):
        """Test user cannot reopen another user's ticket."""
        other_resolved = MaintenanceTicketFactory.create(
            created_by=other_user,
            estate=estate,
            status='RESOLVED',
            resolved_at=timezone.now()
        )
        url = reverse('maintenance:maintenance-ticket-reopen', args=[other_resolved.id])
        response = authenticated_client.post(url)
        assert response.status_code == 404
    
    def test_staff_can_reopen_any_ticket(
        self, admin_client, other_user, estate
    ):
        """Test staff can reopen any ticket."""
        other_resolved = MaintenanceTicketFactory.create(
            created_by=other_user,
            estate=estate,
            status='RESOLVED',
            resolved_at=timezone.now()
        )
        url = reverse('maintenance:maintenance-ticket-reopen', args=[other_resolved.id])
        response = admin_client.post(url)
        
        assert response.status_code == 200
        assert response.data['status'] == 'OPEN'
    
    def test_reopen_open_ticket_fails(
        self, authenticated_client, ticket
    ):
        """Test reopening already open ticket returns error."""
        url = reverse('maintenance:maintenance-ticket-reopen', args=[ticket.id])
        response = authenticated_client.post(url)
        
        assert response.status_code == 400
        assert 'error' in response.data
    
    def test_reopen_clears_resolved_at_timestamp(
        self, authenticated_client, resolved_ticket
    ):
        """Test reopen action clears resolved_at timestamp."""
        assert resolved_ticket.resolved_at is not None
        
        url = reverse('maintenance:maintenance-ticket-reopen', args=[resolved_ticket.id])
        response = authenticated_client.post(url)
        
        assert response.status_code == 200
        resolved_ticket.refresh_from_db()
        assert resolved_ticket.resolved_at is None


@pytest.mark.django_db
class TestStatisticsAction:
    """Test GET /api/maintenance/tickets/statistics/ action."""
    
    def setup_method(self):
        """Setup common test data."""
        self.url = reverse('maintenance:maintenance-ticket-statistics')
    
    def test_unauthenticated_user_cannot_get_statistics(self, api_client, estate):
        """Test unauthenticated users get 401."""
        response = api_client.get(self.url, {'estate_id': str(estate.id)})
        assert response.status_code == 401
    
    def test_authenticated_user_can_get_statistics(
        self, authenticated_client, authenticated_user, estate
    ):
        """Test authenticated user can get statistics."""
        MaintenanceTicketFactory.create_batch(
            3, created_by=authenticated_user, estate=estate, status='OPEN'
        )
        MaintenanceTicketFactory.create_batch(
            2, created_by=authenticated_user, estate=estate, status='RESOLVED',
            resolved_at=timezone.now()
        )
        
        response = authenticated_client.get(self.url, {'estate_id': str(estate.id)})
        
        assert response.status_code == 200
        assert 'total_tickets' in response.data
        assert 'open_tickets' in response.data
        assert 'resolved_tickets' in response.data
        assert 'by_category' in response.data
        assert response.data['total_tickets'] == 5
        assert response.data['open_tickets'] == 3
        assert response.data['resolved_tickets'] == 2
    
    def test_statistics_missing_estate_id_fails(
        self, authenticated_client
    ):
        """Test statistics without estate_id returns 400."""
        response = authenticated_client.get(self.url)
        assert response.status_code == 400
        assert 'error' in response.data
    
    def test_statistics_by_category(
        self, authenticated_client, authenticated_user, estate
    ):
        """Test statistics include breakdown by category."""
        MaintenanceTicketFactory.create(
            created_by=authenticated_user, estate=estate, category='WATER'
        )
        MaintenanceTicketFactory.create(
            created_by=authenticated_user, estate=estate, category='WATER'
        )
        MaintenanceTicketFactory.create(
            created_by=authenticated_user, estate=estate, category='ELECTRICITY'
        )
        
        response = authenticated_client.get(self.url, {'estate_id': str(estate.id)})
        
        assert response.status_code == 200
        assert response.data['by_category']['Water'] == 2
        assert response.data['by_category']['Electricity'] == 1
    
    def test_statistics_empty_estate(
        self, authenticated_client, estate
    ):
        """Test statistics for estate with no tickets."""
        response = authenticated_client.get(self.url, {'estate_id': str(estate.id)})
        
        assert response.status_code == 200
        assert response.data['total_tickets'] == 0
        assert response.data['open_tickets'] == 0
        assert response.data['resolved_tickets'] == 0
    
    def test_statistics_multiple_estates_isolated(
        self, authenticated_client, authenticated_user
    ):
        """Test statistics only include tickets from specified estate."""
        from .factories import EstateFactory
        estate1 = EstateFactory.create()
        estate2 = EstateFactory.create()
        
        MaintenanceTicketFactory.create_batch(
            3, created_by=authenticated_user, estate=estate1
        )
        MaintenanceTicketFactory.create_batch(
            5, created_by=authenticated_user, estate=estate2
        )
        
        response = authenticated_client.get(self.url, {'estate_id': str(estate1.id)})
        
        assert response.status_code == 200
        assert response.data['total_tickets'] == 3