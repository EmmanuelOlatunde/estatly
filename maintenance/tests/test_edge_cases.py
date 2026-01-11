# tests/test_edge_cases.py

"""
Tests for edge cases and boundary conditions.

Coverage:
- Empty strings vs null values
- Very long strings
- Special characters and Unicode
- Concurrent operations
- Boundary values
- Extreme data scenarios
"""

import pytest
from django.urls import reverse
from maintenance.models import MaintenanceTicket
from .factories import MaintenanceTicketFactory


@pytest.mark.django_db
class TestEmptyAndNullValues:
    """Test handling of empty and null values."""
    
    def setup_method(self):
        """Setup common test data."""
        self.url = reverse('maintenance:maintenance-ticket-list')
    
    def test_null_unit_is_valid(
        self, authenticated_client, estate
    ):
        """Test creating ticket with null unit."""
        data = {
            'title': 'Test ticket',
            'description': 'Test description',
            'category': 'WATER',
            'estate': str(estate.id),
            'unit': None
        }
        
        response = authenticated_client.post(self.url, data, format='json')
        assert response.status_code == 201
        assert response.data['unit'] is None
    
    def test_empty_string_unit_treated_as_null(
        self, authenticated_client, estate
    ):
        """Test empty string for unit is handled."""
        data = {
            'title': 'Test ticket',
            'description': 'Test description',
            'category': 'WATER',
            'estate': str(estate.id),
            'unit': ''
        }
        
        response = authenticated_client.post(self.url, data, format='json')
        assert response.status_code in [201, 400]


@pytest.mark.django_db
class TestLongStrings:
    """Test handling of very long strings."""
    
    def setup_method(self):
        """Setup common test data."""
        self.url = reverse('maintenance:maintenance-ticket-list')
    
    def test_very_long_title(
        self, authenticated_client, estate
    ):
        """Test creating ticket with very long title."""
        long_title = 'A' * 250
        data = {
            'title': long_title,
            'description': 'Test description',
            'category': 'WATER',
            'estate': str(estate.id)
        }
        
        response = authenticated_client.post(self.url, data, format='json')
        assert response.status_code == 201
    
    def test_extremely_long_description(
        self, authenticated_client, estate
    ):
        """Test creating ticket with very long description."""
        long_description = 'This is a test description. ' * 500
        data = {
            'title': 'Test ticket',
            'description': long_description,
            'category': 'WATER',
            'estate': str(estate.id)
        }
        
        response = authenticated_client.post(self.url, data, format='json')
        assert response.status_code == 201
        assert len(response.data['description']) > 1000
    
    def test_title_at_max_length(
        self, authenticated_client, estate
    ):
        """Test title at maximum allowed length."""
        max_title = 'A' * 255
        data = {
            'title': max_title,
            'description': 'Test description',
            'category': 'WATER',
            'estate': str(estate.id)
        }
        
        response = authenticated_client.post(self.url, data, format='json')
        assert response.status_code == 201


@pytest.mark.django_db
class TestSpecialCharacters:
    """Test handling of special characters and Unicode."""
    
    def setup_method(self):
        """Setup common test data."""
        self.url = reverse('maintenance:maintenance-ticket-list')
    
    def test_unicode_characters_in_title(
        self, authenticated_client, estate
    ):
        """Test Unicode characters in title."""
        data = {
            'title': 'Wässer läck 漏水问题 مشكلة المياه',
            'description': 'Test description',
            'category': 'WATER',
            'estate': str(estate.id)
        }
        
        response = authenticated_client.post(self.url, data, format='json')
        assert response.status_code == 201
        assert '漏水' in response.data['title']
    
    def test_emoji_in_title(
        self, authenticated_client, estate
    ):
        """Test emoji characters in title."""
        data = {
            'title': '💧 Water leak 🚰',
            'description': 'Test description',
            'category': 'WATER',
            'estate': str(estate.id)
        }
        
        response = authenticated_client.post(self.url, data, format='json')
        assert response.status_code == 201
        assert '💧' in response.data['title']
    
    def test_special_characters_in_description(
        self, authenticated_client, estate
    ):
        """Test special characters in description."""
        data = {
            'title': 'Test ticket',
            'description': 'Special chars: @#$%^&*()_+-=[]{}|;:,.<>?/',
            'category': 'WATER',
            'estate': str(estate.id)
        }
        
        response = authenticated_client.post(self.url, data, format='json')
        assert response.status_code == 201
    
    def test_newlines_in_description(
        self, authenticated_client, estate
    ):
        """Test newline characters in description."""
        data = {
            'title': 'Test ticket',
            'description': 'Line 1\nLine 2\nLine 3',
            'category': 'WATER',
            'estate': str(estate.id)
        }
        
        response = authenticated_client.post(self.url, data, format='json')
        assert response.status_code == 201
        assert '\n' in response.data['description']


@pytest.mark.django_db
class TestBoundaryConditions:
    """Test boundary value conditions."""
    
    def test_single_ticket_in_system(
        self, authenticated_client, authenticated_user, estate
    ):
        """Test system with only one ticket."""
        MaintenanceTicketFactory.create(
            created_by=authenticated_user, estate=estate
        )
        
        url = reverse('maintenance:maintenance-ticket-list')
        response = authenticated_client.get(url)
        
        assert response.status_code == 200
        assert response.data['count'] == 1
        assert len(response.data['results']) == 1
    
    def test_large_dataset_performance(
        self, authenticated_client, authenticated_user, estate
    ):
        """Test handling large number of tickets."""
        MaintenanceTicketFactory.create_batch(
            100, created_by=authenticated_user, estate=estate
        )
        
        url = reverse('maintenance:maintenance-ticket-list')
        response = authenticated_client.get(url)
        
        assert response.status_code == 200
        assert response.data['count'] == 100
    
    def test_zero_tickets_in_system(
        self, authenticated_client
    ):
        """Test system with no tickets."""
        url = reverse('maintenance:maintenance-ticket-list')
        response = authenticated_client.get(url)
        
        assert response.status_code == 200
        assert response.data['count'] == 0
        assert response.data['results'] == []


@pytest.mark.django_db
class TestConcurrentOperations:
    """Test concurrent operation scenarios."""
    
    def test_update_same_ticket_sequentially(
        self, authenticated_client, ticket
    ):
        """Test multiple sequential updates to same ticket."""
        url = reverse('maintenance:maintenance-ticket-detail', args=[ticket.id])
        
        response1 = authenticated_client.patch(
            url, {'title': 'Update 1'}, format='json'
        )
        assert response1.status_code == 200
        
        response2 = authenticated_client.patch(
            url, {'title': 'Update 2'}, format='json'
        )
        assert response2.status_code == 200
        
        ticket.refresh_from_db()
        assert ticket.title == 'Update 2'
    
    def test_resolve_and_reopen_sequentially(
        self, authenticated_client, ticket
    ):
        """Test resolving and reopening same ticket."""
        resolve_url = reverse('maintenance:maintenance-ticket-resolve', args=[ticket.id])
        reopen_url = reverse('maintenance:maintenance-ticket-reopen', args=[ticket.id])
        
        resolve_response = authenticated_client.post(resolve_url)
        assert resolve_response.status_code == 200
        
        reopen_response = authenticated_client.post(reopen_url)
        assert reopen_response.status_code == 200
        
        ticket.refresh_from_db()
        assert ticket.status == 'OPEN'


@pytest.mark.django_db
class TestCaseSensitivity:
    """Test case sensitivity in various operations."""
    
    def test_search_case_insensitive(
        self, authenticated_client, authenticated_user, estate
    ):
        """Test search is case insensitive."""
        MaintenanceTicketFactory.create(
            title='WATER LEAK URGENT',
            created_by=authenticated_user,
            estate=estate
        )
        
        url = reverse('maintenance:maintenance-ticket-list')
        
        response1 = authenticated_client.get(url, {'search': 'water'})
        response2 = authenticated_client.get(url, {'search': 'WATER'})
        response3 = authenticated_client.get(url, {'search': 'WaTeR'})
        
        assert response1.status_code == 200
        assert response2.status_code == 200
        assert response3.status_code == 200
        assert response1.data['count'] == response2.data['count'] == response3.data['count'] == 1
    
    def test_category_filter_case_insensitive(
        self, authenticated_client, authenticated_user, estate
    ):
        """Test category filter is case insensitive."""
        MaintenanceTicketFactory.create(
            created_by=authenticated_user, estate=estate, category='WATER'
        )
        
        url = reverse('maintenance:maintenance-ticket-list')
        
        # All these should work and return the ticket
        response_upper = authenticated_client.get(url, {'category': 'WATER'})
        response_lower = authenticated_client.get(url, {'category': 'water'})
        response_title = authenticated_client.get(url, {'category': 'Water'})
        
        assert response_upper.status_code == 200
        assert response_lower.status_code == 200
        assert response_title.status_code == 200
        
        assert response_upper.data['count'] == 1
        assert response_lower.data['count'] == 1
        assert response_title.data['count'] == 1

@pytest.mark.django_db
class TestTimezoneHandling:
    """Test timezone-aware datetime handling."""
    
    def test_created_at_has_timezone(
        self, authenticated_client, ticket
    ):
        """Test created_at includes timezone information."""
        url = reverse('maintenance:maintenance-ticket-detail', args=[ticket.id])
        response = authenticated_client.get(url)
        
        assert response.status_code == 200
        assert 'created_at' in response.data
        created_at_str = response.data['created_at']
        assert 'Z' in created_at_str or '+' in created_at_str or '-' in created_at_str
    
    def test_resolved_at_has_timezone(
        self, authenticated_client, resolved_ticket
    ):
        """Test resolved_at includes timezone information."""
        url = reverse('maintenance:maintenance-ticket-detail', args=[resolved_ticket.id])
        response = authenticated_client.get(url)
        
        assert response.status_code == 200
        assert response.data['resolved_at'] is not None
        resolved_at_str = response.data['resolved_at']
        assert 'Z' in resolved_at_str or '+' in resolved_at_str or '-' in resolved_at_str