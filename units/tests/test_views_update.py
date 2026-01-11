# tests/test_views_update.py
"""
Tests for units app update endpoints.

Coverage:
- Authentication/authorization for updates
- Full updates (PUT)
- Partial updates (PATCH)
- Validation failures
- Database side effects
- Cross-user access prevention
"""

import pytest
from django.urls import reverse
from units.models import Unit
from .factories import EstateFactory as estate_factory
import time  # Add this import for the timing test


@pytest.mark.django_db
class TestUnitUpdateEndpoint:
    """Test PUT /units/{id}/ endpoint."""
    
    def test_unauthenticated_user_denied(self, api_client, unit):
        """Test that unauthenticated users cannot update units."""
        url = reverse("units:unit-detail", args=[unit.id])
        data = {"identifier": "New Name"}
        response = api_client.put(url, data)
        
        assert response.status_code == 401
    
    def test_owner_can_update_own_unit(self, authenticated_client, unit):
        """Test that owner can update their own unit."""
        url = reverse("units:unit-detail", args=[unit.id])
        data = {
            "identifier": "Updated Unit",
            "unit_type": Unit.UnitType.FLAT,
            "is_occupied": False,
        }
        
        response = authenticated_client.put(url, data, format="json")
        
        assert response.status_code == 200
        assert response.data["identifier"] == "Updated Unit"
        
        unit.refresh_from_db()
        assert unit.identifier == "Updated Unit"
    
    def test_user_cannot_update_other_users_unit(
        self, authenticated_client, other_users_unit
    ):
        """Test that user cannot update another user's unit."""
        url = reverse("units:unit-detail", args=[other_users_unit.id])
        data = {"identifier": "Hacked Name"}
        
        response = authenticated_client.put(url, data, format="json")
        
        assert response.status_code in [403, 404]
        
        other_users_unit.refresh_from_db()
        assert other_users_unit.identifier != "Hacked Name"
    

    def test_update_with_duplicate_identifier_fails(
        self, authenticated_client, user
    ):
        """Test that updating to duplicate identifier fails."""
        # Create estate first
        estate = estate_factory()
        
        # Create both units with estate
        unit1 = Unit.objects.create(
            owner=user,
            estate=estate,  # ADD THIS
            identifier="Unit 1",
            unit_type=Unit.UnitType.HOUSE
        )
        unit2 = Unit.objects.create(
            owner=user,
            estate=estate,  # ADD THIS
            identifier="Unit 2",
            unit_type=Unit.UnitType.HOUSE
        )
        
        url = reverse("units:unit-detail", args=[unit2.id])
        data = {
            "identifier": "Unit 1",  # Try to use unit1's identifier
            "unit_type": Unit.UnitType.HOUSE,
        }
        
        response = authenticated_client.put(url, data, format="json")
        
        assert response.status_code == 400


    def test_update_validates_occupancy_consistency(
        self, authenticated_client, unit
    ):
        """Test that occupancy validation works on updates."""
        url = reverse("units:unit-detail", args=[unit.id])
        data = {
            "identifier": unit.identifier,
            "unit_type": unit.unit_type,
            "is_occupied": False,
            "occupant_name": "John Doe",
        }
        
        response = authenticated_client.put(url, data, format="json")
        
        assert response.status_code == 400

    def test_update_updates_updated_at(self, authenticated_client, unit):
        """Test that updated_at is changed on update."""
        original_updated_at = unit.updated_at
        
        # Add a small delay to ensure timestamp difference
        time.sleep(0.01)  # 10ms delay
        
        url = reverse("units:unit-detail", args=[unit.id])
        data = {
            "identifier": "New Name",
            "unit_type": unit.unit_type,
        }
        
        response = authenticated_client.put(url, data, format="json")
        
        assert response.status_code == 200
        
        unit.refresh_from_db()
        assert unit.updated_at > original_updated_at





@pytest.mark.django_db
class TestUnitPartialUpdateEndpoint:
    """Test PATCH /units/{id}/ endpoint."""
    
    def test_unauthenticated_user_denied(self, api_client, unit):
        """Test that unauthenticated users cannot partially update units."""
        url = reverse("units:unit-detail", args=[unit.id])
        data = {"identifier": "New Name"}
        response = api_client.patch(url, data)
        
        assert response.status_code == 401
    
    def test_owner_can_partially_update_own_unit(
        self, authenticated_client, unit
    ):
        """Test that owner can partially update their unit."""
        original_unit_type = unit.unit_type
        
        url = reverse("units:unit-detail", args=[unit.id])
        data = {"identifier": "Updated Identifier"}
        
        response = authenticated_client.patch(url, data, format="json")
        
        assert response.status_code == 200
        assert response.data["identifier"] == "Updated Identifier"
        
        unit.refresh_from_db()
        assert unit.identifier == "Updated Identifier"
        assert unit.unit_type == original_unit_type
    
    def test_user_cannot_partially_update_other_users_unit(
        self, authenticated_client, other_users_unit
    ):
        """Test that user cannot partially update another user's unit."""
        url = reverse("units:unit-detail", args=[other_users_unit.id])
        data = {"identifier": "Hacked Name"}
        
        response = authenticated_client.patch(url, data, format="json")
        
        assert response.status_code in [403, 404]
    
    def test_partial_update_single_field(self, authenticated_client, unit):
        """Test updating only description field."""
        url = reverse("units:unit-detail", args=[unit.id])
        data = {"description": "New description"}
        
        response = authenticated_client.patch(url, data, format="json")
        
        assert response.status_code == 200
        
        unit.refresh_from_db()
        assert unit.description == "New description"
    
    def test_partial_update_multiple_fields(self, authenticated_client, unit):
        """Test updating multiple fields at once."""
        url = reverse("units:unit-detail", args=[unit.id])
        data = {
            "identifier": "New Name",
            "description": "New description",
            "is_active": False,
        }
        
        response = authenticated_client.patch(url, data, format="json")
        
        assert response.status_code == 200
        
        unit.refresh_from_db()
        assert unit.identifier == "New Name"
        assert unit.description == "New description"
        assert unit.is_active is False
    
    def test_partial_update_occupancy_fields(
        self, authenticated_client, vacant_unit
    ):
        """Test updating occupancy fields."""
        url = reverse("units:unit-detail", args=[vacant_unit.id])
        data = {
            "is_occupied": True,
            "occupant_name": "John Doe",
            "occupant_phone": "+1234567890",
        }
        
        response = authenticated_client.patch(url, data, format="json")
        
        assert response.status_code == 200
        
        vacant_unit.refresh_from_db()
        assert vacant_unit.is_occupied is True
        assert vacant_unit.occupant_name == "John Doe"
    
    def test_partial_update_validates_consistency(
        self, authenticated_client, unit
    ):
        """Test that partial update validates field consistency."""
        url = reverse("units:unit-detail", args=[unit.id])
        data = {
            "is_occupied": False,
            "occupant_name": "John Doe",
        }
        
        response = authenticated_client.patch(url, data, format="json")
        
        assert response.status_code == 400
    
    def test_partial_update_empty_identifier_fails(
        self, authenticated_client, unit
    ):
        """Test that empty identifier fails validation."""
        url = reverse("units:unit-detail", args=[unit.id])
        data = {"identifier": "   "}
        
        response = authenticated_client.patch(url, data, format="json")
        
        assert response.status_code == 400
        assert "identifier" in response.data


    def test_jwt_authentication_works(self, jwt_client, user):
        """Test that JWT authentication works for partial update."""
        # Create estate first
        estate = estate_factory()
        
        # Create unit with estate
        unit = Unit.objects.create(
            owner=user,
            estate=estate,  # ADD THIS
            identifier="Original",
            unit_type=Unit.UnitType.HOUSE
        )
        
        url = reverse("units:unit-detail", args=[unit.id])
        data = {"identifier": "Updated"}
        
        response = jwt_client.patch(url, data, format="json")
        
        assert response.status_code == 200
        
        unit.refresh_from_db()
        assert unit.identifier == "Updated"



    def test_partial_update_unit_type(self, authenticated_client, unit):
        """Test changing unit type via partial update."""
        url = reverse("units:unit-detail", args=[unit.id])
        data = {"unit_type": Unit.UnitType.APARTMENT}
        
        response = authenticated_client.patch(url, data, format="json")
        
        assert response.status_code == 200
        
        unit.refresh_from_db()
        assert unit.unit_type == Unit.UnitType.APARTMENT
    
    def test_cannot_change_owner_via_update(self, authenticated_client, unit, other_user):
        """Test that owner cannot be changed via update."""
        url = reverse("units:unit-detail", args=[unit.id])
        data = {"owner": str(other_user.id)}
        
        response = authenticated_client.patch(url, data, format="json")
        
        unit.refresh_from_db()
        assert unit.owner != other_user