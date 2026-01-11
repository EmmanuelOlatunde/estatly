# tests/test_serializers.py
"""
Tests for units app serializers.

Coverage:
- Serializer validation
- Field requirements
- Field transformations
- Cross-field validation
- Read-only and write-only fields
"""

import pytest
from units.serializers import (
    UnitSerializer,
    UnitListSerializer,
    UnitCreateSerializer,
    UnitUpdateSerializer,
    UnitOccupancySerializer,
)
from units.models import Unit
from .factories import UserFactory, UnitFactory
from .factories import EstateFactory as estate_factory


@pytest.mark.django_db
class TestUnitSerializer:
    """Test UnitSerializer for read operations."""
    
    def test_serializes_all_fields(self):
        """Test that serializer includes all expected fields."""
        user = UserFactory.create()
        unit = UnitFactory.create(owner=user)
        serializer = UnitSerializer(unit)
        
        expected_fields = {
            "id", "identifier", "unit_type", "unit_type_display",
            "owner", "owner_email", "occupant_name", "occupant_phone",
            "description", "is_occupied", "is_active",
            "has_occupant_info", "created_at", "updated_at"
        }
        assert set(serializer.data.keys()) == expected_fields
    
    def test_includes_owner_email(self):
        """Test that owner email is included in serialization."""
        user = UserFactory.create(email="owner@test.com")
        unit = UnitFactory.create(owner=user)
        serializer = UnitSerializer(unit)
        
        assert serializer.data["owner_email"] == "owner@test.com"
    
    def test_includes_unit_type_display(self):
        """Test that human-readable unit type is included."""
        unit = UnitFactory.create(unit_type=Unit.UnitType.HOUSE)
        serializer = UnitSerializer(unit)
        
        assert serializer.data["unit_type_display"] == "House"
    
    def test_has_occupant_info_true_when_present(self):
        """Test has_occupant_info is True when occupant info exists."""
        # We explicitly say the unit is occupied so the model validation is happy
        unit = UnitFactory.create(
            is_occupied=True,           # ← This satisfies the clean() rule
            occupant_name="John Doe"
        )
        serializer = UnitSerializer(unit)
        assert serializer.data["has_occupant_info"] is True
        
    def test_has_occupant_info_false_when_absent(self):
        """Test has_occupant_info is False when no occupant info."""
        unit = UnitFactory.create(occupant_name=None, occupant_phone=None)
        serializer = UnitSerializer(unit)
        
        assert serializer.data["has_occupant_info"] is False


@pytest.mark.django_db
class TestUnitListSerializer:
    """Test UnitListSerializer for list views."""
    
    def test_includes_minimal_fields(self):
        """Test that list serializer includes only necessary fields."""
        unit = UnitFactory.create()
        serializer = UnitListSerializer(unit)
        
        expected_fields = {
            "id", "identifier", "unit_type", "unit_type_display",
            "occupant_name", "is_occupied", "is_active", "created_at"
        }
        assert set(serializer.data.keys()) == expected_fields


@pytest.mark.django_db
class TestUnitCreateSerializer:
    """Test UnitCreateSerializer for creation."""
    
    def test_valid_data_passes_validation(self):
        """Test that valid data passes validation."""
        estate = estate_factory() 
        

        data = {
            "identifier": "House 1",
            "unit_type": Unit.UnitType.HOUSE,
            "is_occupied": False,
            "estate": str(estate.id),
        }
        serializer = UnitCreateSerializer(data=data)
        assert serializer.is_valid()
    
    def test_missing_identifier_fails(self):
        """Test that missing identifier fails validation."""
        data = {
            "unit_type": Unit.UnitType.HOUSE,
        }
        serializer = UnitCreateSerializer(data=data)
        assert not serializer.is_valid()
        assert "identifier" in serializer.errors
    
    def test_empty_identifier_fails(self):
        """Test that empty identifier fails validation."""
        data = {
            "identifier": "  ",
            "unit_type": Unit.UnitType.HOUSE,
        }
        serializer = UnitCreateSerializer(data=data)
        assert not serializer.is_valid()
        assert "identifier" in serializer.errors
    
    def test_identifier_strips_whitespace(self):
        """Test that identifier whitespace is stripped."""
        estate = estate_factory() 
        
        data = {
            "identifier": "  House 1  ",
            "unit_type": Unit.UnitType.HOUSE,
            "estate": str(estate.id),
        }
        serializer = UnitCreateSerializer(data=data)
        assert serializer.is_valid()
        assert serializer.validated_data["identifier"] == "House 1"
    
    def test_identifier_too_long_fails(self):
        """Test that identifier over 100 chars fails validation."""
        data = {
            "identifier": "x" * 101,
            "unit_type": Unit.UnitType.HOUSE,
        }
        serializer = UnitCreateSerializer(data=data)
        assert not serializer.is_valid()
        assert "identifier" in serializer.errors
    
    def test_occupant_info_without_occupied_fails(self):
        """Test that occupant info without is_occupied=True fails."""
        estate = estate_factory() 
        

        data = {
            "identifier": "House 1",
            "unit_type": Unit.UnitType.HOUSE,
            "is_occupied": False,
            "occupant_name": "John Doe",
            "estate": str(estate.id),
        }
        serializer = UnitCreateSerializer(data=data)
        assert not serializer.is_valid()
        assert "non_field_errors" in serializer.errors
    
    def test_occupied_with_name_valid(self):
        """Test that occupied with occupant name is valid."""
        estate = estate_factory() 
        
        data = {
            "identifier": "House 1",
            "unit_type": Unit.UnitType.HOUSE,
            "is_occupied": True,
            "occupant_name": "John Doe",
            "estate": str(estate.id),
        }
        serializer = UnitCreateSerializer(data=data)
        assert serializer.is_valid()
    
    def test_occupied_with_phone_valid(self):
        """Test that occupied with occupant phone is valid."""
        estate = estate_factory()
        data = {
            "identifier": "House 1",
            "unit_type": Unit.UnitType.HOUSE,
            "is_occupied": True,
            "occupant_phone": "+1234567890",
            "estate": str(estate.id),
        }
        serializer = UnitCreateSerializer(data=data)
        assert serializer.is_valid()


@pytest.mark.django_db
class TestUnitUpdateSerializer:
    """Test UnitUpdateSerializer for updates."""
    
    def test_partial_update_valid(self):
        """Test that partial update with single field works."""
        unit = UnitFactory.create()
        data = {"identifier": "New Name"}
        serializer = UnitUpdateSerializer(unit, data=data, partial=True)
        assert serializer.is_valid()
    
    def test_validates_occupancy_consistency_on_update(self):
        """Test that occupancy validation works on updates."""
        unit = UnitFactory.create(is_occupied=False)
        data = {
            "occupant_name": "John Doe",
        }
        serializer = UnitUpdateSerializer(unit, data=data, partial=True)
        assert not serializer.is_valid()
        assert "non_field_errors" in serializer.errors
    
    def test_can_update_identifier(self):
        """Test that identifier can be updated."""
        unit = UnitFactory.create(identifier="Old Name")
        data = {"identifier": "New Name"}
        serializer = UnitUpdateSerializer(unit, data=data, partial=True)
        assert serializer.is_valid()
        assert serializer.validated_data["identifier"] == "New Name"


@pytest.mark.django_db
class TestUnitOccupancySerializer:
    """Test UnitOccupancySerializer for occupancy updates."""
    
    def test_mark_as_occupied_with_name(self):
        """Test marking unit as occupied with occupant name."""
        unit = UnitFactory.create(is_occupied=False)
        data = {
            "is_occupied": True,
            "occupant_name": "John Doe",
        }
        serializer = UnitOccupancySerializer(unit, data=data, partial=True)
        assert serializer.is_valid()
    
    def test_mark_as_unoccupied_clears_info(self):
        """Test that marking as unoccupied clears occupant info."""
        unit = UnitFactory.create(
            is_occupied=True,
            occupant_name="John Doe",
            occupant_phone="+1234567890"
        )
        
        data = {"is_occupied": False}
        serializer = UnitOccupancySerializer(unit, data=data, partial=True)
        
        print(f"Valid: {serializer.is_valid()}")
        print(f"Errors: {serializer.errors}")
        
        assert serializer.is_valid(), serializer.errors
        serializer.save()
        
        unit.refresh_from_db()
        assert unit.occupant_name is None
        assert unit.occupant_phone is None
    
    def test_occupant_info_without_occupied_fails(self):
        """Test that occupant info without is_occupied fails."""
        unit = UnitFactory.create(is_occupied=False)
        estate = estate_factory() 
        

        data = {
            "is_occupied": False,
            "occupant_name": "John Doe",
            "estate": str(estate.id),
        }
        serializer = UnitOccupancySerializer(unit, data=data, partial=True)
        assert not serializer.is_valid()