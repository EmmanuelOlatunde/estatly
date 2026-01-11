# tests/test_views_update.py

"""
Tests for maintenance ticket update endpoints.

Coverage:
- PUT/PATCH authentication/authorization
- Success paths for updates
- Validation errors
- Partial vs full updates
- Field immutability
"""

import pytest
from django.urls import reverse
from django.utils import timezone
from maintenance.models import MaintenanceTicket
from .helpers import assert_error_response


@pytest.mark.django_db
class TestMaintenanceTicketUpdate:
    """Test PUT/PATCH /api/maintenance/tickets/{id}/ endpoints."""
    
    def test_unauthenticated_user_cannot_update_ticket(self, api_client, ticket):
        """Test unauthenticated users get 401."""
        url = reverse('maintenance:maintenance-ticket-detail', args=[ticket.id])
        data = {'title': 'Updated title'}
        response = api_client.patch(url, data, format='json')
        assert response.status_code == 401
    
    def test_user_can_update_own_ticket(
        self, authenticated_client, ticket
    ):
        """Test user can update their own ticket."""
        url = reverse('maintenance:maintenance-ticket-detail', args=[ticket.id])
        data = {
            'title': 'Updated water leak',
            'description': 'Updated description',
            'category': 'ELECTRICITY'
        }
        
        response = authenticated_client.patch(url, data, format='json')
        assert response.status_code == 200
        assert response.data['title'] == data['title']
        assert response.data['description'] == data['description']
        assert response.data['category'] == data['category']
        
        ticket.refresh_from_db()
        assert ticket.title == data['title']
        assert ticket.description == data['description']
        assert ticket.category == data['category']
    
    def test_user_cannot_update_other_users_ticket(
        self, authenticated_client, other_user_ticket
    ):
        """Test user cannot update another user's ticket."""
        url = reverse('maintenance:maintenance-ticket-detail', args=[other_user_ticket.id])
        data = {'title': 'Hacked title'}
        
        response = authenticated_client.patch(url, data, format='json')
        assert response.status_code == 404
        
        other_user_ticket.refresh_from_db()
        assert other_user_ticket.title != 'Hacked title'
    
    def test_staff_can_update_any_ticket(
        self, admin_client, other_user_ticket
    ):
        """Test staff users can update any ticket."""
        url = reverse('maintenance:maintenance-ticket-detail', args=[other_user_ticket.id])
        data = {'title': 'Admin updated title'}
        
        response = admin_client.patch(url, data, format='json')
        assert response.status_code == 200
        assert response.data['title'] == data['title']
    
    def test_partial_update_title_only(
        self, authenticated_client, ticket
    ):
        """Test partial update of only title field."""
        original_description = ticket.description
        original_category = ticket.category
        
        url = reverse('maintenance:maintenance-ticket-detail', args=[ticket.id])
        data = {'title': 'New title only'}
        
        response = authenticated_client.patch(url, data, format='json')
        assert response.status_code == 200
        assert response.data['title'] == data['title']
        
        ticket.refresh_from_db()
        assert ticket.title == data['title']
        assert ticket.description == original_description
        assert ticket.category == original_category
    
    def test_partial_update_description_only(
        self, authenticated_client, ticket
    ):
        """Test partial update of only description field."""
        original_title = ticket.title
        
        url = reverse('maintenance:maintenance-ticket-detail', args=[ticket.id])
        data = {'description': 'New description only'}
        
        response = authenticated_client.patch(url, data, format='json')
        assert response.status_code == 200
        
        ticket.refresh_from_db()
        assert ticket.description == data['description']
        assert ticket.title == original_title
    
    def test_partial_update_category_only(
        self, authenticated_client, ticket
    ):
        """Test partial update of only category field."""
        url = reverse('maintenance:maintenance-ticket-detail', args=[ticket.id])
        data = {'category': 'SECURITY'}
        
        response = authenticated_client.patch(url, data, format='json')
        assert response.status_code == 200
        
        ticket.refresh_from_db()
        assert ticket.category == 'SECURITY'
    
    def test_update_status_to_resolved(
        self, authenticated_client, ticket
    ):
        """Test updating status to resolved."""
        url = reverse('maintenance:maintenance-ticket-detail', args=[ticket.id])
        data = {'status': 'RESOLVED'}
        
        response = authenticated_client.patch(url, data, format='json')
        assert response.status_code == 200
        assert response.data['status'] == 'RESOLVED'
        
        ticket.refresh_from_db()
        assert ticket.status == 'RESOLVED'
        assert ticket.resolved_at is not None
    
    def test_update_status_from_resolved_to_open(
        self, authenticated_client, resolved_ticket
    ):
        """Test updating status from resolved back to open."""
        url = reverse('maintenance:maintenance-ticket-detail', args=[resolved_ticket.id])
        data = {'status': 'OPEN'}
        
        response = authenticated_client.patch(url, data, format='json')
        assert response.status_code == 200
        assert response.data['status'] == 'OPEN'
        
        resolved_ticket.refresh_from_db()
        assert resolved_ticket.status == 'OPEN'
        assert resolved_ticket.resolved_at is None
    
    def test_update_unit_association(
        self, authenticated_client, ticket, unit
    ):
        """Test updating unit association."""
        url = reverse('maintenance:maintenance-ticket-detail', args=[ticket.id])
        data = {'unit': str(unit.id)}
        
        response = authenticated_client.patch(url, data, format='json')
        assert response.status_code == 200
        
        ticket.refresh_from_db()
        assert ticket.unit_id == unit.id
    
    def test_update_remove_unit_association(
        self, authenticated_client, ticket, unit
    ):
        """Test removing unit association."""
        ticket.unit = unit
        ticket.save()
        
        url = reverse('maintenance:maintenance-ticket-detail', args=[ticket.id])
        data = {'unit': None}
        
        response = authenticated_client.patch(url, data, format='json')
        assert response.status_code == 200
        
        ticket.refresh_from_db()
        assert ticket.unit is None
    
    def test_update_fails_empty_title(
        self, authenticated_client, ticket
    ):
        """Test update fails with empty title."""
        url = reverse('maintenance:maintenance-ticket-detail', args=[ticket.id])
        data = {'title': ''}
        
        response = authenticated_client.patch(url, data, format='json')
        assert_error_response(response, status_code=400, field='title')
    
    def test_update_fails_whitespace_only_title(
        self, authenticated_client, ticket
    ):
        """Test update fails with whitespace-only title."""
        url = reverse('maintenance:maintenance-ticket-detail', args=[ticket.id])
        data = {'title': '   '}
        
        response = authenticated_client.patch(url, data, format='json')
        assert_error_response(response, status_code=400, field='title')
    
    def test_update_fails_empty_description(
        self, authenticated_client, ticket
    ):
        """Test update fails with empty description."""
        url = reverse('maintenance:maintenance-ticket-detail', args=[ticket.id])
        data = {'description': ''}
        
        response = authenticated_client.patch(url, data, format='json')
        assert_error_response(response, status_code=400, field='description')
    
    def test_update_fails_invalid_category(
        self, authenticated_client, ticket
    ):
        """Test update fails with invalid category."""
        url = reverse('maintenance:maintenance-ticket-detail', args=[ticket.id])
        data = {'category': 'INVALID_CATEGORY'}
        
        response = authenticated_client.patch(url, data, format='json')
        assert_error_response(response, status_code=400, field='category')
    
    def test_update_fails_invalid_status(
        self, authenticated_client, ticket
    ):
        """Test update fails with invalid status."""
        url = reverse('maintenance:maintenance-ticket-detail', args=[ticket.id])
        data = {'status': 'INVALID_STATUS'}
        
        response = authenticated_client.patch(url, data, format='json')
        assert_error_response(response, status_code=400, field='status')
    
    def test_update_fails_unit_from_different_estate(
        self, authenticated_client, ticket
    ):
        """Test update fails when unit doesn't belong to ticket's estate."""
        from .factories import UnitFactory, EstateFactory
        other_estate = EstateFactory.create()
        other_unit = UnitFactory.create(estate=other_estate)
        
        url = reverse('maintenance:maintenance-ticket-detail', args=[ticket.id])
        data = {'unit': str(other_unit.id)}
        
        response = authenticated_client.patch(url, data, format='json')
        assert_error_response(response, status_code=400, field='unit')
    
    def test_update_trims_whitespace_from_title(
        self, authenticated_client, ticket
    ):
        """Test title whitespace is trimmed on update."""
        url = reverse('maintenance:maintenance-ticket-detail', args=[ticket.id])
        data = {'title': '  Updated title  '}
        
        response = authenticated_client.patch(url, data, format='json')
        assert response.status_code == 200
        assert response.data['title'] == 'Updated title'
    
    def test_update_trims_whitespace_from_description(
        self, authenticated_client, ticket
    ):
        """Test description whitespace is trimmed on update."""
        url = reverse('maintenance:maintenance-ticket-detail', args=[ticket.id])
        data = {'description': '  Updated description  '}
        
        response = authenticated_client.patch(url, data, format='json')
        assert response.status_code == 200
        assert response.data['description'] == 'Updated description'
    
    def test_full_update_with_put(
        self, authenticated_client, ticket, estate
    ):
        """Test full update using PUT method."""
        url = reverse('maintenance:maintenance-ticket-detail', args=[ticket.id])
        data = {
            'title': 'Completely new title',
            'description': 'Completely new description',
            'category': 'WASTE',
            'status': 'OPEN',
            'estate': str(estate.id)
        }
        
        response = authenticated_client.put(url, data, format='json')
        assert response.status_code == 200
        
        ticket.refresh_from_db()
        assert ticket.title == data['title']
        assert ticket.description == data['description']
        assert ticket.category == data['category']
    
    def test_cannot_modify_created_by_on_update(
        self, authenticated_client, ticket, other_user
    ):
        """Test cannot change created_by field on update."""
        original_creator = ticket.created_by
        
        url = reverse('maintenance:maintenance-ticket-detail', args=[ticket.id])
        data = {
            'title': 'Updated title',
            'created_by': str(other_user.id)
        }
        
        response = authenticated_client.patch(url, data, format='json')
        
        ticket.refresh_from_db()
        assert ticket.created_by == original_creator
    
    def test_cannot_modify_estate_on_update(
        self, authenticated_client, ticket
    ):
        """Test cannot change estate field on update."""
        from .factories import EstateFactory
        original_estate = ticket.estate
        new_estate = EstateFactory.create()
        
        url = reverse('maintenance:maintenance-ticket-detail', args=[ticket.id])
        data = {
            'title': 'Updated title',
            'estate': str(new_estate.id)
        }
        
        response = authenticated_client.patch(url, data, format='json')
        
        ticket.refresh_from_db()
        assert ticket.estate == original_estate
    
    def test_updated_at_changes_on_update(
        self, authenticated_client, ticket
    ):
        """Test updated_at timestamp is updated."""
        original_updated_at = ticket.updated_at
        
        url = reverse('maintenance:maintenance-ticket-detail', args=[ticket.id])
        data = {'title': 'New title'}
        
        import time
        time.sleep(0.1)
        
        response = authenticated_client.patch(url, data, format='json')
        assert response.status_code == 200
        
        ticket.refresh_from_db()
        assert ticket.updated_at > original_updated_at
    
    def test_multiple_sequential_updates(
        self, authenticated_client, ticket
    ):
        """Test multiple sequential updates work correctly."""
        url = reverse('maintenance:maintenance-ticket-detail', args=[ticket.id])
        
        response1 = authenticated_client.patch(url, {'title': 'First update'}, format='json')
        assert response1.status_code == 200
        
        response2 = authenticated_client.patch(url, {'description': 'Second update'}, format='json')
        assert response2.status_code == 200
        
        response3 = authenticated_client.patch(url, {'category': 'WASTE'}, format='json')
        assert response3.status_code == 200
        
        ticket.refresh_from_db()
        assert ticket.title == 'First update'
        assert ticket.description == 'Second update'
        assert ticket.category == 'WASTE'