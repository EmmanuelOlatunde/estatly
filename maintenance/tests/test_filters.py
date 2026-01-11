# tests/test_filters.py

"""
Tests for maintenance ticket filtering.

Coverage:
- Filter by status
- Filter by category
- Filter by estate
- Filter by unit
- Filter by date ranges
- Combined filters
"""

import pytest
from django.urls import reverse
from django.utils import timezone
from datetime import timedelta
from .factories import MaintenanceTicketFactory


@pytest.mark.django_db
class TestMaintenanceTicketFilters:
    """Test filtering on maintenance ticket list endpoint."""
    
    def setup_method(self):
        """Setup common test data."""
        self.url = reverse('maintenance:maintenance-ticket-list')
    
    def test_filter_by_status_open(
        self, authenticated_client, authenticated_user, estate
    ):
        """Test filtering by status=OPEN."""
        MaintenanceTicketFactory.create_batch(
            2, created_by=authenticated_user, estate=estate, status='OPEN'
        )
        MaintenanceTicketFactory.create(
            created_by=authenticated_user, estate=estate, status='RESOLVED',
            resolved_at=timezone.now()
        )
        
        response = authenticated_client.get(self.url, {'status': 'OPEN'})
        
        assert response.status_code == 200
        assert response.data['count'] == 2
        for ticket in response.data['results']:
            assert ticket['status'] == 'OPEN'
    
    def test_filter_by_status_resolved(
        self, authenticated_client, authenticated_user, estate
    ):
        """Test filtering by status=RESOLVED."""
        MaintenanceTicketFactory.create(
            created_by=authenticated_user, estate=estate, status='OPEN'
        )
        MaintenanceTicketFactory.create_batch(
            3, created_by=authenticated_user, estate=estate, status='RESOLVED',
            resolved_at=timezone.now()
        )
        
        response = authenticated_client.get(self.url, {'status': 'RESOLVED'})
        
        assert response.status_code == 200
        assert response.data['count'] == 3
        for ticket in response.data['results']:
            assert ticket['status'] == 'RESOLVED'
    
    def test_filter_by_category_water(
        self, authenticated_client, authenticated_user, estate
    ):
        """Test filtering by category=WATER."""
        MaintenanceTicketFactory.create_batch(
            2, created_by=authenticated_user, estate=estate, category='WATER'
        )
        MaintenanceTicketFactory.create(
            created_by=authenticated_user, estate=estate, category='ELECTRICITY'
        )
        
        response = authenticated_client.get(self.url, {'category': 'WATER'})
        
        assert response.status_code == 200
        assert response.data['count'] == 2
        for ticket in response.data['results']:
            assert ticket['category'] == 'WATER'
    
    def test_filter_by_estate(
        self, authenticated_client, authenticated_user
    ):
        """Test filtering by estate."""
        from .factories import EstateFactory
        estate1 = EstateFactory.create()
        estate2 = EstateFactory.create()
        
        MaintenanceTicketFactory.create_batch(
            3, created_by=authenticated_user, estate=estate1
        )
        MaintenanceTicketFactory.create_batch(
            2, created_by=authenticated_user, estate=estate2
        )
        
        response = authenticated_client.get(self.url, {'estate': str(estate1.id)})
        
        assert response.status_code == 200
        assert response.data['count'] == 3
    
    def test_filter_by_unit(
        self, authenticated_client, authenticated_user, estate, unit
    ):
        """Test filtering by unit."""
        MaintenanceTicketFactory.create_batch(
            2, created_by=authenticated_user, estate=estate, unit=unit
        )
        MaintenanceTicketFactory.create(
            created_by=authenticated_user, estate=estate, unit=None
        )
        
        response = authenticated_client.get(self.url, {'unit': str(unit.id)})
        
        assert response.status_code == 200
        assert response.data['count'] == 2
    
    def test_filter_by_created_after(
        self, authenticated_client, authenticated_user, estate
    ):
        """Test filtering by created_after date."""
        cutoff = timezone.now() - timedelta(days=2)
        
        old_ticket = MaintenanceTicketFactory.create(
            created_by=authenticated_user, estate=estate
        )
        old_ticket.created_at = cutoff - timedelta(days=1)
        old_ticket.save()
        
        new_ticket = MaintenanceTicketFactory.create(
            created_by=authenticated_user, estate=estate
        )
        new_ticket.created_at = cutoff + timedelta(days=1)
        new_ticket.save()
        
        response = authenticated_client.get(
            self.url,
            {'created_after': cutoff.isoformat()}
        )
        
        assert response.status_code == 200
        assert response.data['count'] == 1
        assert response.data['results'][0]['id'] == str(new_ticket.id)
    
    def test_filter_by_created_before(
        self, authenticated_client, authenticated_user, estate
    ):
        """Test filtering by created_before date."""
        cutoff = timezone.now() - timedelta(days=2)
        
        old_ticket = MaintenanceTicketFactory.create(
            created_by=authenticated_user, estate=estate
        )
        old_ticket.created_at = cutoff - timedelta(days=1)
        old_ticket.save()
        
        new_ticket = MaintenanceTicketFactory.create(
            created_by=authenticated_user, estate=estate
        )
        new_ticket.created_at = cutoff + timedelta(days=1)
        new_ticket.save()
        
        response = authenticated_client.get(
            self.url,
            {'created_before': cutoff.isoformat()}
        )
        
        assert response.status_code == 200
        assert response.data['count'] == 1
        assert response.data['results'][0]['id'] == str(old_ticket.id)
    
    def test_filter_is_resolved_true(
        self, authenticated_client, authenticated_user, estate
    ):
        """Test filtering by is_resolved=true."""
        MaintenanceTicketFactory.create(
            created_by=authenticated_user, estate=estate, status='OPEN'
        )
        MaintenanceTicketFactory.create_batch(
            2, created_by=authenticated_user, estate=estate, status='RESOLVED',
            resolved_at=timezone.now()
        )
        
        response = authenticated_client.get(self.url, {'is_resolved': 'true'})
        
        assert response.status_code == 200
        assert response.data['count'] == 2
    
    def test_filter_is_resolved_false(
        self, authenticated_client, authenticated_user, estate
    ):
        """Test filtering by is_resolved=false."""
        MaintenanceTicketFactory.create_batch(
            3, created_by=authenticated_user, estate=estate, status='OPEN'
        )
        MaintenanceTicketFactory.create(
            created_by=authenticated_user, estate=estate, status='RESOLVED',
            resolved_at=timezone.now()
        )
        
        response = authenticated_client.get(self.url, {'is_resolved': 'false'})
        
        assert response.status_code == 200
        assert response.data['count'] == 3
    
    def test_filter_has_unit_true(
        self, authenticated_client, authenticated_user, estate, unit
    ):
        """Test filtering by has_unit=true."""
        MaintenanceTicketFactory.create_batch(
            2, created_by=authenticated_user, estate=estate, unit=unit
        )
        MaintenanceTicketFactory.create(
            created_by=authenticated_user, estate=estate, unit=None
        )
        
        response = authenticated_client.get(self.url, {'has_unit': 'true'})
        
        assert response.status_code == 200
        assert response.data['count'] == 2
    
    def test_filter_has_unit_false(
        self, authenticated_client, authenticated_user, estate, unit
    ):
        """Test filtering by has_unit=false."""
        MaintenanceTicketFactory.create(
            created_by=authenticated_user, estate=estate, unit=unit
        )
        MaintenanceTicketFactory.create_batch(
            3, created_by=authenticated_user, estate=estate, unit=None
        )
        
        response = authenticated_client.get(self.url, {'has_unit': 'false'})
        
        assert response.status_code == 200
        assert response.data['count'] == 3
    
    def test_combined_filters(
        self, authenticated_client, authenticated_user, estate
    ):
        """Test combining multiple filters."""
        MaintenanceTicketFactory.create(
            created_by=authenticated_user, estate=estate,
            status='OPEN', category='WATER'
        )
        MaintenanceTicketFactory.create(
            created_by=authenticated_user, estate=estate,
            status='OPEN', category='ELECTRICITY'
        )
        MaintenanceTicketFactory.create(
            created_by=authenticated_user, estate=estate,
            status='RESOLVED', category='WATER',
            resolved_at=timezone.now()
        )
        
        response = authenticated_client.get(
            self.url,
            {'status': 'OPEN', 'category': 'WATER'}
        )
        
        assert response.status_code == 200
        assert response.data['count'] == 1
    
    def test_filter_with_search(
        self, authenticated_client, authenticated_user, estate
    ):
        """Test combining filter with search."""
        MaintenanceTicketFactory.create(
            title="Water leak in basement",
            created_by=authenticated_user, estate=estate,
            category='WATER'
        )
        MaintenanceTicketFactory.create(
            title="Water issue in unit",
            created_by=authenticated_user, estate=estate,
            category='OTHER'
        )
        MaintenanceTicketFactory.create(
            title="Electrical problem",
            created_by=authenticated_user, estate=estate,
            category='WATER'
        )
        
        response = authenticated_client.get(
            self.url,
            {'category': 'WATER', 'search': 'water'}
        )
        
        assert response.status_code == 200
        assert response.data['count'] == 1