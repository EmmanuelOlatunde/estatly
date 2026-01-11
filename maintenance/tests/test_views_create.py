# tests/test_views_create.py

"""
Tests for maintenance ticket creation endpoint.

Coverage:
- Authentication/authorization
- Success paths
- Validation errors
- Business rules
"""

import pytest
from django.urls import reverse
from maintenance.models import MaintenanceTicket
from .helpers import assert_error_response


@pytest.mark.django_db
class TestMaintenanceTicketCreate:
    """Test POST /api/maintenance/tickets/ endpoint."""
    
    def setup_method(self):
        """Setup common test data."""
        self.url = reverse('maintenance:maintenance-ticket-list')
    
    def test_unauthenticated_user_cannot_create_ticket(self, api_client, estate):
        """Test unauthenticated users get 401."""
        data = {
            'title': 'Test ticket',
            'description': 'Test description',
            'category': 'WATER',
            'estate': str(estate.id)
        }
        response = api_client.post(self.url, data, format='json')
        assert response.status_code == 401
    
    def test_authenticated_user_can_create_ticket(
        self, authenticated_client, authenticated_user, estate
    ):
        """Test authenticated user can create ticket."""
        data = {
            'title': 'Water leak',
            'description': 'There is a water leak in the basement',
            'category': 'WATER',
            'estate': str(estate.id)
        }
        
        response = authenticated_client.post(self.url, data, format='json')
        assert response.status_code == 201
        assert response.data['title'] == data['title']
        assert response.data['description'] == data['description']
        assert response.data['category'] == data['category']
        assert response.data['status'] == 'OPEN'
        assert str(response.data['created_by']) == str(authenticated_user.id)

        
        # Verify database state
        ticket = MaintenanceTicket.objects.get(id=response.data['id'])
        assert ticket.title == data['title']
        assert ticket.created_by == authenticated_user
        assert ticket.estate_id == estate.id
        assert ticket.created_at is not None
    
    def test_create_ticket_with_unit(
        self, authenticated_client, authenticated_user, estate, unit
    ):
        """Test creating ticket with unit association."""
        data = {
            'title': 'Unit issue',
            'description': 'Problem in specific unit',
            'category': 'OTHER',
            'estate': str(estate.id),
            'unit': str(unit.id)
        }
        
        response = authenticated_client.post(self.url, data, format='json')
        assert response.status_code == 201
        assert str(response.data['unit']) == str(unit.id)

        
        ticket = MaintenanceTicket.objects.get(id=response.data['id'])
        assert ticket.unit_id == unit.id
    
    def test_create_ticket_without_unit(
        self, authenticated_client, authenticated_user, estate
    ):
        """Test creating ticket without unit (estate-wide issue)."""
        data = {
            'title': 'General issue',
            'description': 'Estate-wide problem',
            'category': 'SECURITY',
            'estate': str(estate.id)
        }
        
        response = authenticated_client.post(self.url, data, format='json')
        assert response.status_code == 201
        assert response.data['unit'] is None
    
    def test_create_fails_missing_title(
        self, authenticated_client, estate
    ):
        """Test creation fails when title is missing."""
        data = {
            'description': 'Test description',
            'category': 'WATER',
            'estate': str(estate.id)
        }
        
        response = authenticated_client.post(self.url, data, format='json')
        assert_error_response(response, status_code=400, field='title')
    
    def test_create_fails_missing_description(
        self, authenticated_client, estate
    ):
        """Test creation fails when description is missing."""
        data = {
            'title': 'Test ticket',
            'category': 'WATER',
            'estate': str(estate.id)
        }
        
        response = authenticated_client.post(self.url, data, format='json')
        assert_error_response(response, status_code=400, field='description')
    
    def test_create_fails_missing_category(
        self, authenticated_client, estate
    ):
        """Test creation fails when category is missing."""
        data = {
            'title': 'Test ticket',
            'description': 'Test description',
            'estate': str(estate.id)
        }
        
        response = authenticated_client.post(self.url, data, format='json')
        assert_error_response(response, status_code=400, field='category')
    
    def test_create_fails_missing_estate(
        self, authenticated_client
    ):
        """Test creation fails when estate is missing."""
        data = {
            'title': 'Test ticket',
            'description': 'Test description',
            'category': 'WATER'
        }
        
        response = authenticated_client.post(self.url, data, format='json')
        assert_error_response(response, status_code=400, field='estate')
    
    def test_create_fails_empty_title(
        self, authenticated_client, estate
    ):
        """Test creation fails with empty title."""
        data = {
            'title': '',
            'description': 'Test description',
            'category': 'WATER',
            'estate': str(estate.id)
        }
        
        response = authenticated_client.post(self.url, data, format='json')
        assert_error_response(response, status_code=400, field='title')
    
    def test_create_fails_whitespace_only_title(
        self, authenticated_client, estate
    ):
        """Test creation fails with whitespace-only title."""
        data = {
            'title': '   ',
            'description': 'Test description',
            'category': 'WATER',
            'estate': str(estate.id)
        }
        
        response = authenticated_client.post(self.url, data, format='json')
        assert_error_response(response, status_code=400, field='title')
    
    def test_create_fails_empty_description(
        self, authenticated_client, estate
    ):
        """Test creation fails with empty description."""
        data = {
            'title': 'Test ticket',
            'description': '',
            'category': 'WATER',
            'estate': str(estate.id)
        }
        
        response = authenticated_client.post(self.url, data, format='json')
        assert_error_response(response, status_code=400, field='description')
    
    def test_create_fails_invalid_category(
        self, authenticated_client, estate
    ):
        """Test creation fails with invalid category."""
        data = {
            'title': 'Test ticket',
            'description': 'Test description',
            'category': 'INVALID_CATEGORY',
            'estate': str(estate.id)
        }
        
        response = authenticated_client.post(self.url, data, format='json')
        assert_error_response(response, status_code=400, field='category')
    
    def test_create_fails_invalid_estate_uuid(
        self, authenticated_client
    ):
        """Test creation fails with invalid estate UUID."""
        data = {
            'title': 'Test ticket',
            'description': 'Test description',
            'category': 'WATER',
            'estate': 'invalid-uuid'
        }
        
        response = authenticated_client.post(self.url, data, format='json')
        assert response.status_code == 400
    
    def test_create_fails_nonexistent_estate(
        self, authenticated_client
    ):
        """Test creation fails with non-existent estate."""
        import uuid
        data = {
            'title': 'Test ticket',
            'description': 'Test description',
            'category': 'WATER',
            'estate': str(uuid.uuid4())
        }
        
        response = authenticated_client.post(self.url, data, format='json')
        assert response.status_code == 400
    
    def test_create_fails_unit_not_in_estate(
        self, authenticated_client, estate
    ):
        """Test creation fails when unit doesn't belong to estate."""
        from .factories import UnitFactory, EstateFactory
        other_estate = EstateFactory.create()
        other_unit = UnitFactory.create(estate=other_estate)
        
        data = {
            'title': 'Test ticket',
            'description': 'Test description',
            'category': 'WATER',
            'estate': str(estate.id),
            'unit': str(other_unit.id)
        }
        
        response = authenticated_client.post(self.url, data, format='json')
        assert_error_response(response, status_code=400, field='unit')
    
    def test_create_trims_whitespace_from_title(
        self, authenticated_client, estate
    ):
        """Test title whitespace is trimmed."""
        data = {
            'title': '  Water leak  ',
            'description': 'Test description',
            'category': 'WATER',
            'estate': str(estate.id)
        }
        
        response = authenticated_client.post(self.url, data, format='json')
        assert response.status_code == 201
        assert response.data['title'] == 'Water leak'
    
    def test_create_all_categories(
        self, authenticated_client, authenticated_user, estate
    ):
        """Test creating tickets with all category types."""
        categories = ['WATER', 'ELECTRICITY', 'SECURITY', 'WASTE', 'OTHER']
        
        for category in categories:
            data = {
                'title': f'{category} issue',
                'description': f'Test {category} issue',
                'category': category,
                'estate': str(estate.id)
            }
            
            response = authenticated_client.post(self.url, data, format='json')
            assert response.status_code == 201
            assert response.data['category'] == category
        
        assert MaintenanceTicket.objects.filter(
            created_by=authenticated_user
        ).count() == 5