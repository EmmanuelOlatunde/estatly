

# tests/test_serializers.py
"""
Tests for estates app serializers.

Coverage:
- Field validation
- Required fields
- Optional fields
- Computed fields
- Read-only fields
- Serializer choices
"""

import pytest
from estates.serializers import (
    EstateSerializer,
    EstateCreateSerializer,
    EstateUpdateSerializer,
    EstateListSerializer
)
from estates.models import Estate


@pytest.mark.django_db
class TestEstateSerializer:
    """Test EstateSerializer for reading estate data."""
    
    def test_serializer_contains_expected_fields(self, estate):
        """Test serializer includes all expected fields."""
        serializer = EstateSerializer(estate)
        data = serializer.data
        
        expected_fields = {
            'id', 'name', 'estate_type', 'estate_type_display',
            'approximate_units', 'unit_count_display', 'fee_frequency',
            'fee_frequency_display', 'is_active', 'status_display',
            'description', 'address', 'created_at', 'updated_at'
        }
        
        assert set(data.keys()) == expected_fields
    
    def test_estate_type_display_field(self, estate):
        """Test estate_type_display shows human-readable value."""
        estate.estate_type = Estate.EstateType.GOVERNMENT
        estate.save()
        
        serializer = EstateSerializer(estate)
        assert serializer.data['estate_type_display'] == 'Government'
    
    def test_fee_frequency_display_field(self, estate):
        """Test fee_frequency_display shows human-readable value."""
        estate.fee_frequency = Estate.FeeFrequency.YEARLY
        estate.save()
        
        serializer = EstateSerializer(estate)
        assert serializer.data['fee_frequency_display'] == 'Yearly'
    
    def test_unit_count_display_with_units(self, estate):
        """Test unit_count_display shows formatted count."""
        estate.approximate_units = 100
        estate.save()
        
        serializer = EstateSerializer(estate)
        assert serializer.data['unit_count_display'] == '~100 units'
    
    def test_unit_count_display_without_units(self, estate):
        """Test unit_count_display when units is None."""
        estate.approximate_units = None
        estate.save()
        
        serializer = EstateSerializer(estate)
        assert serializer.data['unit_count_display'] == 'Unit count not specified'
    
    def test_status_display_active(self, estate):
        """Test status_display for active estate."""
        estate.is_active = True
        estate.save()
        
        serializer = EstateSerializer(estate)
        assert serializer.data['status_display'] == 'Active'
    
    def test_status_display_inactive(self, estate):
        """Test status_display for inactive estate."""
        estate.is_active = False
        estate.save()
        
        serializer = EstateSerializer(estate)
        assert serializer.data['status_display'] == 'Inactive'


@pytest.mark.django_db
class TestEstateCreateSerializer:
    """Test EstateCreateSerializer for creating estates."""
    
    def test_create_with_valid_data(self):
        """Test creating estate with all valid fields."""
        data = {
            'name': 'Test Estate',
            'estate_type': Estate.EstateType.PRIVATE,
            'approximate_units': 50,
            'fee_frequency': Estate.FeeFrequency.MONTHLY,
            'is_active': True,
            'description': 'Test description',
            'address': 'Test address'
        }
        
        serializer = EstateCreateSerializer(data=data)
        assert serializer.is_valid()
        assert serializer.validated_data['name'] == 'Test Estate'
    
    def test_create_with_minimal_data(self):
        """Test creating estate with only required fields."""
        data = {
            'name': 'Minimal Estate',
            'estate_type': Estate.EstateType.GOVERNMENT,
            'fee_frequency': Estate.FeeFrequency.YEARLY
        }
        
        serializer = EstateCreateSerializer(data=data)
        assert serializer.is_valid()
    
    def test_name_validation_empty_string(self):
        """Test name validation rejects empty string."""
        data = {
            'name': '',
            'estate_type': Estate.EstateType.PRIVATE,
            'fee_frequency': Estate.FeeFrequency.MONTHLY
        }
        
        serializer = EstateCreateSerializer(data=data)
        assert not serializer.is_valid()
        assert 'name' in serializer.errors
    
    def test_name_validation_whitespace_only(self):
        """Test name validation rejects whitespace-only string."""
        data = {
            'name': '   ',
            'estate_type': Estate.EstateType.PRIVATE,
            'fee_frequency': Estate.FeeFrequency.MONTHLY
        }
        
        serializer = EstateCreateSerializer(data=data)
        assert not serializer.is_valid()
        assert 'name' in serializer.errors
    
    def test_name_strips_whitespace(self):
        """Test name field strips leading/trailing whitespace."""
        data = {
            'name': '  Test Estate  ',
            'estate_type': Estate.EstateType.PRIVATE,
            'fee_frequency': Estate.FeeFrequency.MONTHLY
        }
        
        serializer = EstateCreateSerializer(data=data)
        assert serializer.is_valid()
        assert serializer.validated_data['name'] == 'Test Estate'
    
    def test_approximate_units_validation_zero(self):
        """Test approximate_units validation rejects zero."""
        data = {
            'name': 'Test Estate',
            'estate_type': Estate.EstateType.PRIVATE,
            'approximate_units': 0,
            'fee_frequency': Estate.FeeFrequency.MONTHLY
        }
        
        serializer = EstateCreateSerializer(data=data)
        assert not serializer.is_valid()
        assert 'approximate_units' in serializer.errors
    
    def test_approximate_units_validation_negative(self):
        """Test approximate_units validation rejects negative values."""
        data = {
            'name': 'Test Estate',
            'estate_type': Estate.EstateType.PRIVATE,
            'approximate_units': -10,
            'fee_frequency': Estate.FeeFrequency.MONTHLY
        }
        
        serializer = EstateCreateSerializer(data=data)
        assert not serializer.is_valid()
        assert 'approximate_units' in serializer.errors
    
    def test_approximate_units_accepts_null(self):
        """Test approximate_units accepts null/None value."""
        data = {
            'name': 'Test Estate',
            'estate_type': Estate.EstateType.PRIVATE,
            'approximate_units': None,
            'fee_frequency': Estate.FeeFrequency.MONTHLY
        }
        
        serializer = EstateCreateSerializer(data=data)
        assert serializer.is_valid()


@pytest.mark.django_db
class TestEstateUpdateSerializer:
    """Test EstateUpdateSerializer for updating estates."""
    
    def test_update_with_valid_data(self, estate):
        """Test updating estate with valid data."""
        data = {'name': 'Updated Estate'}
        
        serializer = EstateUpdateSerializer(estate, data=data, partial=True)
        assert serializer.is_valid()
        assert serializer.validated_data['name'] == 'Updated Estate'
    
    def test_partial_update_name_only(self, estate):
        """Test partial update of only name field."""
        original_type = estate.estate_type
        data = {'name': 'New Name'}
        
        serializer = EstateUpdateSerializer(estate, data=data, partial=True)
        assert serializer.is_valid()
        
        updated_estate = serializer.save()
        assert updated_estate.name == 'New Name'
        assert updated_estate.estate_type == original_type
    
    def test_update_name_validation_empty(self, estate):
        """Test update name validation rejects empty string."""
        data = {'name': ''}
        
        serializer = EstateUpdateSerializer(estate, data=data, partial=True)
        assert not serializer.is_valid()
        assert 'name' in serializer.errors
    
    def test_update_approximate_units_validation(self, estate):
        """Test update approximate_units validation."""
        data = {'approximate_units': -5}
        
        serializer = EstateUpdateSerializer(estate, data=data, partial=True)
        assert not serializer.is_valid()
        assert 'approximate_units' in serializer.errors


@pytest.mark.django_db
class TestEstateListSerializer:
    """Test EstateListSerializer for list views."""
    
    def test_serializer_contains_minimal_fields(self, estate):
        """Test list serializer includes only minimal fields."""
        serializer = EstateListSerializer(estate)
        data = serializer.data
        
        expected_fields = {
            'id', 'name', 'estate_type', 'estate_type_display',
            'approximate_units', 'is_active', 'status_display', 'created_at'
        }
        
        assert set(data.keys()) == expected_fields
    
    def test_all_fields_readonly(self, estate):
        """Test that all fields in list serializer are read-only."""
        serializer = EstateListSerializer(estate)
        
        for field_name in serializer.Meta.read_only_fields:
            assert field_name in serializer.fields

