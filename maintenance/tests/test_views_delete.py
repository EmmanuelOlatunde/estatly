# tests/test_views_delete.py

"""
Tests for maintenance ticket delete endpoint.

Coverage:
- DELETE authentication/authorization
- Success paths
- Cascading effects
- Cannot delete other users' tickets
"""

import pytest
import uuid
from django.urls import reverse
from maintenance.models import MaintenanceTicket


@pytest.mark.django_db
class TestMaintenanceTicketDelete:
    """Test DELETE /api/maintenance/tickets/{id}/ endpoint."""
    
    def test_unauthenticated_user_cannot_delete_ticket(self, api_client, ticket):
        """Test unauthenticated users get 401."""
        url = reverse('maintenance:maintenance-ticket-detail', args=[ticket.id])
        response = api_client.delete(url)
        assert response.status_code == 401
        assert MaintenanceTicket.objects.filter(id=ticket.id).exists()
    
    def test_user_can_delete_own_ticket(
        self, authenticated_client, ticket
    ):
        """Test user can delete their own ticket."""
        ticket_id = ticket.id
        url = reverse('maintenance:maintenance-ticket-detail', args=[ticket_id])
        
        response = authenticated_client.delete(url)
        assert response.status_code == 204
        assert not MaintenanceTicket.objects.filter(id=ticket_id).exists()
    
    def test_user_cannot_delete_other_users_ticket(
        self, authenticated_client, other_user_ticket
    ):
        """Test user cannot delete another user's ticket."""
        ticket_id = other_user_ticket.id
        url = reverse('maintenance:maintenance-ticket-detail', args=[ticket_id])
        
        response = authenticated_client.delete(url)
        assert response.status_code == 404
        assert MaintenanceTicket.objects.filter(id=ticket_id).exists()
    
    def test_staff_can_delete_any_ticket(
        self, admin_client, other_user_ticket
    ):
        """Test staff users can delete any ticket."""
        ticket_id = other_user_ticket.id
        url = reverse('maintenance:maintenance-ticket-detail', args=[ticket_id])
        
        response = admin_client.delete(url)
        assert response.status_code == 204
        assert not MaintenanceTicket.objects.filter(id=ticket_id).exists()
    
    def test_delete_nonexistent_ticket_returns_404(
        self, authenticated_client
    ):
        """Test deleting non-existent ticket returns 404."""
        fake_id = uuid.uuid4()
        url = reverse('maintenance:maintenance-ticket-detail', args=[fake_id])
        
        response = authenticated_client.delete(url)
        assert response.status_code == 404
    
    def test_delete_returns_no_content(
        self, authenticated_client, ticket
    ):
        """Test delete returns 204 No Content with empty body."""
        url = reverse('maintenance:maintenance-ticket-detail', args=[ticket.id])
        
        response = authenticated_client.delete(url)
        assert response.status_code == 204
        assert not response.data
    
    def test_delete_is_permanent(
        self, authenticated_client, ticket
    ):
        """Test deleted tickets cannot be retrieved."""
        ticket_id = ticket.id
        url = reverse('maintenance:maintenance-ticket-detail', args=[ticket_id])
        
        delete_response = authenticated_client.delete(url)
        assert delete_response.status_code == 204
        
        get_response = authenticated_client.get(url)
        assert get_response.status_code == 404
    
    def test_delete_multiple_tickets(
        self, authenticated_client, authenticated_user, estate
    ):
        """Test deleting multiple tickets sequentially."""
        from .factories import MaintenanceTicketFactory
        tickets = MaintenanceTicketFactory.create_batch(
            3, created_by=authenticated_user, estate=estate
        )
        
        for ticket in tickets:
            url = reverse('maintenance:maintenance-ticket-detail', args=[ticket.id])
            response = authenticated_client.delete(url)
            assert response.status_code == 204
        
        assert MaintenanceTicket.objects.filter(
            created_by=authenticated_user
        ).count() == 0
    
    def test_cannot_delete_twice(
        self, authenticated_client, ticket
    ):
        """Test cannot delete same ticket twice."""
        url = reverse('maintenance:maintenance-ticket-detail', args=[ticket.id])
        
        first_response = authenticated_client.delete(url)
        assert first_response.status_code == 204
        
        second_response = authenticated_client.delete(url)
        assert second_response.status_code == 404
    
    def test_delete_resolved_ticket(
        self, authenticated_client, resolved_ticket
    ):
        """Test can delete resolved tickets."""
        ticket_id = resolved_ticket.id
        url = reverse('maintenance:maintenance-ticket-detail', args=[ticket_id])
        
        response = authenticated_client.delete(url)
        assert response.status_code == 204
        assert not MaintenanceTicket.objects.filter(id=ticket_id).exists()
    
    def test_delete_ticket_with_unit(
        self, authenticated_client, ticket, unit
    ):
        """Test deleting ticket with unit association."""
        ticket.unit = unit
        ticket.save()
        ticket_id = ticket.id
        
        url = reverse('maintenance:maintenance-ticket-detail', args=[ticket_id])
        response = authenticated_client.delete(url)
        
        assert response.status_code == 204
        assert not MaintenanceTicket.objects.filter(id=ticket_id).exists()
        
        from units.models import Unit
        assert Unit.objects.filter(id=unit.id).exists()
    
    def test_delete_does_not_affect_other_tickets(
        self, authenticated_client, authenticated_user, estate
    ):
        """Test deleting one ticket doesn't affect others."""
        from .factories import MaintenanceTicketFactory
        ticket1 = MaintenanceTicketFactory.create(
            created_by=authenticated_user, estate=estate
        )
        ticket2 = MaintenanceTicketFactory.create(
            created_by=authenticated_user, estate=estate
        )
        
        url = reverse('maintenance:maintenance-ticket-detail', args=[ticket1.id])
        response = authenticated_client.delete(url)
        assert response.status_code == 204
        
        assert not MaintenanceTicket.objects.filter(id=ticket1.id).exists()
        assert MaintenanceTicket.objects.filter(id=ticket2.id).exists()