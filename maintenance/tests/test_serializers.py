# tests/test_serializers.py

"""
Tests for maintenance app serializers.

Coverage:
- Serializer field validation
- Required vs optional fields
- Read-only fields
- Computed fields
- Nested relationships
"""

import pytest
from django.utils import timezone
from maintenance.serializers import (
    MaintenanceTicketSerializer,
    MaintenanceTicketCreateSerializer,
    MaintenanceTicketUpdateSerializer,
    MaintenanceTicketListSerializer,
)
from .factories import MaintenanceTicketFactory, UserFactory, EstateFactory, UnitFactory


@pytest.mark.django_db
class TestMaintenanceTicketSerializer:
    """Test MaintenanceTicketSerializer (read serializer)."""
    
    def test_serializer_contains_expected_fields(self, ticket):
        """Test serializer contains all expected fields."""
        serializer = MaintenanceTicketSerializer(ticket)
        expected_fields = {
            'id', 'title', 'description', 'category', 'category_display',
            'status', 'status_display', 'created_by', 'created_by_name',
            'unit', 'identifier', 'estate', 'estate_name', 'created_at',
            'updated_at', 'resolved_at', 'is_resolved', 'days_open'
        }
        assert set(serializer.data.keys()) == expected_fields
    
    def test_category_display_shows_human_readable(self, ticket):
        """Test category_display field shows human-readable value."""
        ticket.category = 'WATER'
        ticket.save()
        
        serializer = MaintenanceTicketSerializer(ticket)
        assert serializer.data['category'] == 'WATER'
        assert serializer.data['category_display'] == 'Water'
    
    def test_status_display_shows_human_readable(self, ticket):
        """Test status_display field shows human-readable value."""
        ticket.status = 'OPEN'
        ticket.save()
        
        serializer = MaintenanceTicketSerializer(ticket)
        assert serializer.data['status'] == 'OPEN'
        assert serializer.data['status_display'] == 'Open'
    
    def test_created_by_name_returns_user_name(self, ticket):
        """Test created_by_name returns user's name."""
        ticket.created_by.first_name = 'John'
        ticket.created_by.last_name = 'Doe'
        ticket.created_by.save()
        
        serializer = MaintenanceTicketSerializer(ticket)
        assert 'John' in serializer.data['created_by_name'] or \
               'Doe' in serializer.data['created_by_name']
    
    def test_estate_name_returns_estate_name(self, ticket):
        """Test estate_name returns estate's name."""
        serializer = MaintenanceTicketSerializer(ticket)
        assert serializer.data['estate_name'] == ticket.estate.name
    
    def test_identifier_returns_unit_number_when_exists(self, ticket, unit):
        """Test identifier returns unit number when unit exists."""
        ticket.unit = unit
        ticket.save()
        
        serializer = MaintenanceTicketSerializer(ticket)
        assert serializer.data['identifier'] == unit.unit_number 
    
    def test_identifier_returns_none_when_no_unit(self, ticket):
        """Test identifier returns None when no unit."""
        ticket.unit = None
        ticket.save()
        
        serializer = MaintenanceTicketSerializer(ticket)
        assert serializer.data['identifier'] is None
    
    def test_is_resolved_true_for_resolved_ticket(self, resolved_ticket):
        """Test is_resolved returns True for resolved tickets."""
        serializer = MaintenanceTicketSerializer(resolved_ticket)
        assert serializer.data['is_resolved'] is True
    
    def test_is_resolved_false_for_open_ticket(self, ticket):
        """Test is_resolved returns False for open tickets."""
        serializer = MaintenanceTicketSerializer(ticket)
        assert serializer.data['is_resolved'] is False
    
    def test_days_open_calculates_correctly(self, ticket):
        """Test days_open field calculates days correctly."""
        serializer = MaintenanceTicketSerializer(ticket)
        assert isinstance(serializer.data['days_open'], int)
        assert serializer.data['days_open'] >= 0
    
    def test_resolved_at_present_for_resolved_ticket(self, resolved_ticket):
        """Test resolved_at is present for resolved tickets."""
        serializer = MaintenanceTicketSerializer(resolved_ticket)
        assert serializer.data['resolved_at'] is not None
    
    def test_resolved_at_null_for_open_ticket(self, ticket):
        """Test resolved_at is null for open tickets."""
        serializer = MaintenanceTicketSerializer(ticket)
        assert serializer.data['resolved_at'] is None


@pytest.mark.django_db
class TestMaintenanceTicketCreateSerializer:
    """Test MaintenanceTicketCreateSerializer (write serializer)."""
    
    def test_valid_data_passes_validation(self, estate):
        """Test valid data passes validation."""
        data = {
            'title': 'Water leak',
            'description': 'There is a water leak',
            'category': 'WATER',
            'estate': estate.id
        }
        
        serializer = MaintenanceTicketCreateSerializer(data=data)
        assert serializer.is_valid()
    
    def test_missing_title_fails_validation(self, estate):
        """Test missing title fails validation."""
        data = {
            'description': 'Test description',
            'category': 'WATER',
            'estate': estate.id
        }
        
        serializer = MaintenanceTicketCreateSerializer(data=data)
        assert not serializer.is_valid()
        assert 'title' in serializer.errors
    
    def test_missing_description_fails_validation(self, estate):
        """Test missing description fails validation."""
        data = {
            'title': 'Test title',
            'category': 'WATER',
            'estate': estate.id
        }
        
        serializer = MaintenanceTicketCreateSerializer(data=data)
        assert not serializer.is_valid()
        assert 'description' in serializer.errors
    
    def test_missing_category_fails_validation(self, estate):
        """Test missing category fails validation."""
        data = {
            'title': 'Test title',
            'description': 'Test description',
            'estate': estate.id
        }
        
        serializer = MaintenanceTicketCreateSerializer(data=data)
        assert not serializer.is_valid()
        assert 'category' in serializer.errors
    
    def test_missing_estate_fails_validation(self):
        """Test missing estate fails validation."""
        data = {
            'title': 'Test title',
            'description': 'Test description',
            'category': 'WATER'
        }
        
        serializer = MaintenanceTicketCreateSerializer(data=data)
        assert not serializer.is_valid()
        assert 'estate' in serializer.errors
    
    def test_empty_title_fails_validation(self, estate):
        """Test empty title fails validation."""
        data = {
            'title': '',
            'description': 'Test description',
            'category': 'WATER',
            'estate': estate.id
        }
        
        serializer = MaintenanceTicketCreateSerializer(data=data)
        assert not serializer.is_valid()
        assert 'title' in serializer.errors
    
    def test_whitespace_only_title_fails_validation(self, estate):
        """Test whitespace-only title fails validation."""
        data = {
            'title': '   ',
            'description': 'Test description',
            'category': 'WATER',
            'estate': estate.id
        }
        
        serializer = MaintenanceTicketCreateSerializer(data=data)
        assert not serializer.is_valid()
        assert 'title' in serializer.errors
    
    def test_invalid_category_fails_validation(self, estate):
        """Test invalid category fails validation."""
        data = {
            'title': 'Test title',
            'description': 'Test description',
            'category': 'INVALID',
            'estate': estate.id
        }
        
        serializer = MaintenanceTicketCreateSerializer(data=data)
        assert not serializer.is_valid()
        assert 'category' in serializer.errors
    
    def test_unit_from_different_estate_fails_validation(self, estate):
        """Test unit from different estate fails validation."""
        other_estate = EstateFactory.create()
        other_unit = UnitFactory.create(estate=other_estate)
        
        data = {
            'title': 'Test title',
            'description': 'Test description',
            'category': 'WATER',
            'estate': estate.id,
            'unit': other_unit.id
        }
        
        serializer = MaintenanceTicketCreateSerializer(data=data)
        assert not serializer.is_valid()
        assert 'unit' in serializer.errors
    
    def test_unit_optional_field(self, estate):
        """Test unit field is optional."""
        data = {
            'title': 'Test title',
            'description': 'Test description',
            'category': 'WATER',
            'estate': estate.id
        }
        
        serializer = MaintenanceTicketCreateSerializer(data=data)
        assert serializer.is_valid()
    
    def test_title_whitespace_trimmed(self, estate):
        """Test title whitespace is trimmed."""
        data = {
            'title': '  Test title  ',
            'description': 'Test description',
            'category': 'WATER',
            'estate': estate.id
        }
        
        serializer = MaintenanceTicketCreateSerializer(data=data)
        assert serializer.is_valid()
        assert serializer.validated_data['title'] == 'Test title'


@pytest.mark.django_db
class TestMaintenanceTicketUpdateSerializer:
    """Test MaintenanceTicketUpdateSerializer."""
    
    def test_valid_update_data_passes_validation(self, ticket):
        """Test valid update data passes validation."""
        data = {
            'title': 'Updated title',
            'description': 'Updated description',
            'category': 'ELECTRICITY',
            'status': 'RESOLVED'
        }
        
        serializer = MaintenanceTicketUpdateSerializer(ticket, data=data, partial=True)
        assert serializer.is_valid()
    
    def test_partial_update_title_only(self, ticket):
        """Test partial update of title only."""
        data = {'title': 'New title'}
        
        serializer = MaintenanceTicketUpdateSerializer(ticket, data=data, partial=True)
        assert serializer.is_valid()
    
    def test_empty_title_fails_validation(self, ticket):
        """Test empty title fails validation."""
        data = {'title': ''}
        
        serializer = MaintenanceTicketUpdateSerializer(ticket, data=data, partial=True)
        assert not serializer.is_valid()
        assert 'title' in serializer.errors
    
    def test_invalid_status_fails_validation(self, ticket):
        """Test invalid status fails validation."""
        data = {'status': 'INVALID_STATUS'}
        
        serializer = MaintenanceTicketUpdateSerializer(ticket, data=data, partial=True)
        assert not serializer.is_valid()
        assert 'status' in serializer.errors
    
    def test_update_sets_resolved_at_when_status_changes_to_resolved(self, ticket):
        """Test updating status to resolved sets resolved_at."""
        data = {'status': 'RESOLVED'}
        
        serializer = MaintenanceTicketUpdateSerializer(ticket, data=data, partial=True)
        assert serializer.is_valid()
        updated_ticket = serializer.save()
        
        assert updated_ticket.resolved_at is not None
    
    def test_update_clears_resolved_at_when_status_changes_to_open(self, resolved_ticket):
        """Test updating status to open clears resolved_at."""
        data = {'status': 'OPEN'}
        
        serializer = MaintenanceTicketUpdateSerializer(
            resolved_ticket, data=data, partial=True
        )
        assert serializer.is_valid()
        updated_ticket = serializer.save()
        
        assert updated_ticket.resolved_at is None


@pytest.mark.django_db
class TestMaintenanceTicketListSerializer:
    """Test MaintenanceTicketListSerializer (lightweight list)."""
    
    def test_list_serializer_contains_minimal_fields(self, ticket):
        """Test list serializer contains only essential fields."""
        serializer = MaintenanceTicketListSerializer(ticket)
        expected_fields = {
            'id', 'title', 'category', 'category_display',
            'status', 'status_display', 'estate_name',
            'created_at', 'updated_at'
        }
        assert set(serializer.data.keys()) == expected_fields
    
    def test_list_serializer_excludes_heavy_fields(self, ticket):
        """Test list serializer excludes description and other heavy fields."""
        serializer = MaintenanceTicketListSerializer(ticket)
        assert 'description' not in serializer.data
        assert 'days_open' not in serializer.data
    
    def test_list_serializer_all_fields_readonly(self, ticket):
        """Test all fields in list serializer are read-only."""
        serializer = MaintenanceTicketListSerializer(ticket)
        
        for field in serializer.fields.values():
            assert field.read_only