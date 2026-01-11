# tests/test_integration.py

"""
Tests for multi-endpoint workflows and integration scenarios.

Coverage:
- Complete ticket lifecycle
- Multi-step workflows
- Cross-endpoint interactions
- Real-world usage patterns
"""

import pytest
from django.urls import reverse
from maintenance.models import MaintenanceTicket


@pytest.mark.django_db
class TestCompleteTicketLifecycle:
    """Test complete ticket lifecycle from creation to resolution."""
    
    def test_create_update_resolve_workflow(
        self, authenticated_client, estate
    ):
        """Test creating, updating, and resolving a ticket."""
        # Step 1: Create ticket
        create_data = {
            'title': 'Water leak in basement',
            'description': 'There is water leaking from the ceiling',
            'category': 'WATER',
            'estate': str(estate.id)
        }
        
        create_url = reverse('maintenance:maintenance-ticket-list')
        create_response = authenticated_client.post(create_url, create_data, format='json')
        assert create_response.status_code == 201
        ticket_id = create_response.data['id']
        
        # Step 2: Update ticket with more details
        update_data = {
            'description': 'Water leaking from ceiling in basement near boiler room'
        }
        
        update_url = reverse('maintenance:maintenance-ticket-detail', args=[ticket_id])
        update_response = authenticated_client.patch(update_url, update_data, format='json')
        assert update_response.status_code == 200
        assert 'boiler room' in update_response.data['description']
        
        # Step 3: Resolve the ticket
        resolve_url = reverse('maintenance:maintenance-ticket-resolve', args=[ticket_id])
        resolve_response = authenticated_client.post(resolve_url)
        assert resolve_response.status_code == 200
        assert resolve_response.data['status'] == 'RESOLVED'
        
        # Step 4: Verify final state
        detail_url = reverse('maintenance:maintenance-ticket-detail', args=[ticket_id])
        detail_response = authenticated_client.get(detail_url)
        assert detail_response.status_code == 200
        assert detail_response.data['status'] == 'RESOLVED'
        assert detail_response.data['resolved_at'] is not None
    
    def test_create_resolve_reopen_workflow(
        self, authenticated_client, estate
    ):
        """Test creating, resolving, and reopening a ticket."""
        # Create ticket
        create_data = {
            'title': 'Elevator not working',
            'description': 'Main elevator is stuck',
            'category': 'OTHER',
            'estate': str(estate.id)
        }
        
        create_url = reverse('maintenance:maintenance-ticket-list')
        create_response = authenticated_client.post(create_url, create_data, format='json')
        ticket_id = create_response.data['id']
        
        # Resolve ticket
        resolve_url = reverse('maintenance:maintenance-ticket-resolve', args=[ticket_id])
        authenticated_client.post(resolve_url)
        
        # Reopen ticket (issue came back)
        reopen_url = reverse('maintenance:maintenance-ticket-reopen', args=[ticket_id])
        reopen_response = authenticated_client.post(reopen_url)
        assert reopen_response.status_code == 200
        assert reopen_response.data['status'] == 'OPEN'
        assert reopen_response.data['resolved_at'] is None
    
    def test_create_update_delete_workflow(
        self, authenticated_client, estate
    ):
        """Test creating, updating, and deleting a ticket."""
        # Create ticket
        create_data = {
            'title': 'Test issue',
            'description': 'Test description',
            'category': 'OTHER',
            'estate': str(estate.id)
        }
        
        create_url = reverse('maintenance:maintenance-ticket-list')
        create_response = authenticated_client.post(create_url, create_data, format='json')
        ticket_id = create_response.data['id']
        
        # Update ticket
        update_url = reverse('maintenance:maintenance-ticket-detail', args=[ticket_id])
        authenticated_client.patch(
            update_url,
            {'title': 'Updated title'},
            format='json'
        )
        
        # Delete ticket
        delete_response = authenticated_client.delete(update_url)
        assert delete_response.status_code == 204
        
        # Verify deletion
        get_response = authenticated_client.get(update_url)
        assert get_response.status_code == 404


@pytest.mark.django_db
class TestMultiTicketWorkflows:
    """Test workflows involving multiple tickets."""
    
    def test_create_multiple_tickets_and_list(
        self, authenticated_client, estate
    ):
        """Test creating multiple tickets and listing them."""
        # Create 5 tickets
        create_url = reverse('maintenance:maintenance-ticket-list')
        
        for i in range(5):
            data = {
                'title': f'Issue {i+1}',
                'description': f'Description for issue {i+1}',
                'category': ['WATER', 'ELECTRICITY', 'SECURITY', 'WASTE', 'OTHER'][i],
                'estate': str(estate.id)
            }
            response = authenticated_client.post(create_url, data, format='json')
            assert response.status_code == 201
        
        # List all tickets
        list_response = authenticated_client.get(create_url)
        assert list_response.status_code == 200
        assert list_response.data['count'] == 5
    
    def test_filter_and_order_multiple_tickets(
        self, authenticated_client, authenticated_user, estate
    ):
        """Test filtering and ordering multiple tickets."""
        from .factories import MaintenanceTicketFactory
        
        # Create tickets with different statuses and categories
        MaintenanceTicketFactory.create_batch(
            3, created_by=authenticated_user, estate=estate,
            category='WATER', status='OPEN'
        )
        MaintenanceTicketFactory.create_batch(
            2, created_by=authenticated_user, estate=estate,
            category='WATER', status='RESOLVED', resolved_at='2024-01-01'
        )
        MaintenanceTicketFactory.create_batch(
            2, created_by=authenticated_user, estate=estate,
            category='ELECTRICITY', status='OPEN'
        )
        
        list_url = reverse('maintenance:maintenance-ticket-list')
        
        # Filter by category
        category_response = authenticated_client.get(
            list_url,
            {'category': 'WATER'}
        )
        assert category_response.status_code == 200
        assert category_response.data['count'] == 5
        
        # Filter by status
        status_response = authenticated_client.get(
            list_url,
            {'status': 'OPEN'}
        )
        assert status_response.status_code == 200
        assert status_response.data['count'] == 5
        
        # Combined filter
        combined_response = authenticated_client.get(
            list_url,
            {'category': 'WATER', 'status': 'OPEN'}
        )
        assert combined_response.status_code == 200
        assert combined_response.data['count'] == 3
    
    def test_batch_resolve_workflow(
        self, authenticated_client, authenticated_user, estate
    ):
        """Test resolving multiple tickets."""
        from .factories import MaintenanceTicketFactory
        
        # Create 3 tickets
        tickets = MaintenanceTicketFactory.create_batch(
            3, created_by=authenticated_user, estate=estate, status='OPEN'
        )
        
        # Resolve all tickets
        for ticket in tickets:
            resolve_url = reverse('maintenance:maintenance-ticket-resolve', args=[ticket.id])
            response = authenticated_client.post(resolve_url)
            assert response.status_code == 200
        
        # Verify all are resolved
        list_url = reverse('maintenance:maintenance-ticket-list')
        response = authenticated_client.get(list_url, {'status': 'RESOLVED'})
        assert response.status_code == 200
        assert response.data['count'] == 3


@pytest.mark.django_db
class TestSearchAndStatistics:
    """Test search and statistics integration."""
    
    def test_search_then_get_statistics(
        self, authenticated_client, authenticated_user, estate
    ):
        """Test searching tickets then getting statistics."""
        from .factories import MaintenanceTicketFactory
        
        # Create tickets
        MaintenanceTicketFactory.create(
            title='Water leak urgent',
            created_by=authenticated_user,
            estate=estate,
            category='WATER'
        )
        MaintenanceTicketFactory.create(
            title='Water pressure issue',
            created_by=authenticated_user,
            estate=estate,
            category='WATER'
        )
        MaintenanceTicketFactory.create(
            title='Electrical problem',
            created_by=authenticated_user,
            estate=estate,
            category='ELECTRICITY'
        )
        
        # Search for water issues
        list_url = reverse('maintenance:maintenance-ticket-list')
        search_response = authenticated_client.get(list_url, {'search': 'water'})
        assert search_response.status_code == 200
        assert search_response.data['count'] == 2
        
        # Get statistics
        stats_url = reverse('maintenance:maintenance-ticket-statistics')
        stats_response = authenticated_client.get(
            stats_url,
            {'estate_id': str(estate.id)}
        )
        assert stats_response.status_code == 200
        assert stats_response.data['total_tickets'] == 3
        assert stats_response.data['by_category']['Water'] == 2


@pytest.mark.django_db
class TestCrossUserScenarios:
    """Test scenarios involving multiple users."""
    
    def test_staff_can_manage_all_tickets(
        self, admin_client, authenticated_user, other_user, estate
    ):
        """Test staff user can manage tickets from all users."""
        from .factories import MaintenanceTicketFactory
        
        # Create tickets by different users
        user1_ticket = MaintenanceTicketFactory.create(
            created_by=authenticated_user, estate=estate
        )
        user2_ticket = MaintenanceTicketFactory.create(
            created_by=other_user, estate=estate
        )
        
        # Staff can list all
        list_url = reverse('maintenance:maintenance-ticket-list')
        list_response = admin_client.get(list_url)
        assert list_response.status_code == 200
        assert list_response.data['count'] >= 2
        
        # Staff can update user1's ticket
        update_url = reverse('maintenance:maintenance-ticket-detail', args=[user1_ticket.id])
        update_response = admin_client.patch(
            update_url,
            {'title': 'Admin updated'},
            format='json'
        )
        assert update_response.status_code == 200
        
        # Staff can resolve user2's ticket
        resolve_url = reverse('maintenance:maintenance-ticket-resolve', args=[user2_ticket.id])
        resolve_response = admin_client.post(resolve_url)
        assert resolve_response.status_code == 200


@pytest.mark.django_db
class TestRealWorldScenarios:
    """Test realistic real-world usage scenarios."""
    
    def test_estate_manager_daily_workflow(
        self, authenticated_client, estate, unit
    ):
        """Test typical estate manager daily workflow."""
        # Morning: Create new tickets from resident calls
        create_url = reverse('maintenance:maintenance-ticket-list')
        
        ticket1 = authenticated_client.post(create_url, {
            'title': 'Broken lock on main gate',
            'description': 'Main gate lock is broken, security concern',
            'category': 'SECURITY',
            'estate': str(estate.id)
        }, format='json')
        
        ticket2 = authenticated_client.post(create_url, {
            'title': 'Water not running in Unit 101',
            'description': 'No water supply in unit',
            'category': 'WATER',
            'estate': str(estate.id),
            'unit': str(unit.id)
        }, format='json')
        
        assert ticket1.status_code == 201
        assert ticket2.status_code == 201
        
        # Afternoon: Check open tickets
        list_response = authenticated_client.get(
            create_url,
            {'status': 'OPEN'}
        )
        assert list_response.status_code == 200
        assert list_response.data['count'] >= 2
        
        # Evening: Resolve fixed issues
        resolve_url = reverse(
            'maintenance:maintenance-ticket-resolve',
            args=[ticket1.data['id']]
        )
        resolve_response = authenticated_client.post(resolve_url)
        assert resolve_response.status_code == 200
        
        # End of day: Check statistics
        stats_url = reverse('maintenance:maintenance-ticket-statistics')
        stats_response = authenticated_client.get(
            stats_url,
            {'estate_id': str(estate.id)}
        )
        assert stats_response.status_code == 200
        assert stats_response.data['total_tickets'] >= 2
        assert stats_response.data['open_tickets'] >= 1
        assert stats_response.data['resolved_tickets'] >= 1