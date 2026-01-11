# tests/test_urls.py

"""
Tests for maintenance app URL routing.

Coverage:
- URL pattern resolution
- Reverse URL generation
- Router registration
"""

import pytest
from django.urls import reverse, resolve


@pytest.mark.django_db
class TestMaintenanceURLs:
    """Test URL routing for maintenance endpoints."""
    
    def test_ticket_list_url_resolves(self):
        """Test ticket list URL resolves correctly."""
        url = reverse('maintenance:maintenance-ticket-list')
        assert url == '/api/maintenance/tickets/'
        
        resolved = resolve(url)
        assert resolved.view_name == 'maintenance:maintenance-ticket-list'
    
    def test_ticket_detail_url_resolves(self, ticket):
        """Test ticket detail URL resolves with UUID."""
        url = reverse('maintenance:maintenance-ticket-detail', args=[ticket.id])
        assert url == f'/api/maintenance/tickets/{ticket.id}/'
        
        resolved = resolve(url)
        assert resolved.view_name == 'maintenance:maintenance-ticket-detail'
    
    def test_ticket_resolve_action_url(self, ticket):
        """Test resolve action URL generation."""
        url = reverse('maintenance:maintenance-ticket-resolve', args=[ticket.id])
        assert url == f'/api/maintenance/tickets/{ticket.id}/resolve/'
    
    def test_ticket_reopen_action_url(self, ticket):
        """Test reopen action URL generation."""
        url = reverse('maintenance:maintenance-ticket-reopen', args=[ticket.id])
        assert url == f'/api/maintenance/tickets/{ticket.id}/reopen/'
    
    def test_ticket_statistics_action_url(self):
        """Test statistics action URL generation."""
        url = reverse('maintenance:maintenance-ticket-statistics')
        assert url == '/api/maintenance/tickets/statistics/'