# tests/test_custom_actions.py
"""
Tests for units app custom action endpoints.

Coverage:
- deactivate action
- activate action
- update_occupancy action
- Authentication/authorization
- Database side effects
"""

import pytest
from django.urls import reverse
from units.models import Unit
from .factories import EstateFactory as estate_factory


@pytest.mark.django_db
class TestDeactivateAction:
    """Test POST /units/{id}/deactivate/ endpoint."""
    
    def test_unauthenticated_user_denied(self, api_client, unit):
        """Test that unauthenticated users cannot deactivate units."""
        url = reverse("units:unit-deactivate", args=[unit.id])
        response = api_client.post(url)
        
        assert response.status_code == 401
    
    def test_owner_can_deactivate_own_unit(self, authenticated_client, unit):
        """Test that owner can deactivate their unit."""
        url = reverse("units:unit-deactivate", args=[unit.id])
        
        response = authenticated_client.post(url)
        
        assert response.status_code == 200
        assert response.data["is_active"] is False
        
        unit.refresh_from_db()
        assert unit.is_active is False
    
    def test_user_cannot_deactivate_other_users_unit(
        self, authenticated_client, other_users_unit
    ):
        """Test that user cannot deactivate another user's unit."""
        url = reverse("units:unit-deactivate", args=[other_users_unit.id])
        
        response = authenticated_client.post(url)
        
        assert response.status_code in [403, 404]
        
        other_users_unit.refresh_from_db()
        assert other_users_unit.is_active is True
    
    def test_deactivate_already_inactive_unit(
        self, authenticated_client, inactive_unit
    ):
        """Test deactivating an already inactive unit."""
        url = reverse("units:unit-deactivate", args=[inactive_unit.id])
        
        response = authenticated_client.post(url)
        
        assert response.status_code == 404
    
    def test_deactivate_updates_updated_at(self, authenticated_client, unit):
        """Test that deactivate updates the updated_at timestamp."""
        import time
        original_updated_at = unit.updated_at
        
        time.sleep(0.01)  # Add tiny delay
        
        url = reverse("units:unit-deactivate", args=[unit.id])
        response = authenticated_client.post(url)
        
        assert response.status_code == 200  # Verify it actually worked
        
        unit.refresh_from_db()
        assert unit.updated_at > original_updated_at

    def test_jwt_authentication_works(self, jwt_client, user):
        """Test that JWT authentication works for deactivate."""
        estate = estate_factory()
        
        # Create both units with estate
        unit = Unit.objects.create(
            owner=user,
            estate=estate,  # ADD THIS
            identifier="Test",
            unit_type=Unit.UnitType.HOUSE
        )
        url = reverse("units:unit-deactivate", args=[unit.id])
        
        response = jwt_client.post(url)
        
        assert response.status_code == 200
        
        unit.refresh_from_db()
        assert unit.is_active is False


@pytest.mark.django_db
class TestActivateAction:
    """Test POST /units/{id}/activate/ endpoint."""
    
    def test_unauthenticated_user_denied(self, api_client, inactive_unit):
        """Test that unauthenticated users cannot activate units."""
        url = reverse("units:unit-activate", args=[inactive_unit.id])
        response = api_client.post(url)
        
        assert response.status_code == 401
    
    def test_owner_can_activate_own_unit(
        self, authenticated_client, inactive_unit
    ):
        """Test that owner can activate their inactive unit."""
        url = reverse("units:unit-activate", args=[inactive_unit.id])
        
        response = authenticated_client.post(url)
        
        assert response.status_code == 200
        assert response.data["is_active"] is True
        
        inactive_unit.refresh_from_db()
        assert inactive_unit.is_active is True
    
    def test_user_cannot_activate_other_users_unit(
        self, authenticated_client, other_user
    ):
        """Test that user cannot activate another user's unit."""
        estate = estate_factory()
        other_inactive = Unit.objects.create(
            owner=other_user,
            estate=estate,  # ADD THIS
            identifier="Other Unit",
            unit_type=Unit.UnitType.HOUSE,
            is_active=False
        )
        url = reverse("units:unit-activate", args=[other_inactive.id])
        
        response = authenticated_client.post(url)
        
        assert response.status_code in [403, 404]
    
    def test_activate_already_active_unit(self, authenticated_client, unit):
        """Test activating an already active unit."""
        url = reverse("units:unit-activate", args=[unit.id])
        
        response = authenticated_client.post(url)
        
        assert response.status_code == 200
        assert response.data["is_active"] is True
    
    def test_activate_updates_updated_at(
        self, authenticated_client, inactive_unit
    ):
        """Test that activate updates the updated_at timestamp."""
        original_updated_at = inactive_unit.updated_at
        
        url = reverse("units:unit-activate", args=[inactive_unit.id])
        authenticated_client.post(url)
        
        inactive_unit.refresh_from_db()
        assert inactive_unit.updated_at > original_updated_at


@pytest.mark.django_db
class TestUpdateOccupancyAction:
    """Test PATCH /units/{id}/update_occupancy/ endpoint."""
    
    def test_unauthenticated_user_denied(self, api_client, unit):
        """Test that unauthenticated users cannot update occupancy."""
        url = reverse("units:unit-update-occupancy", args=[unit.id])
        data = {"is_occupied": True, "occupant_name": "John Doe"}
        response = api_client.patch(url, data)
        
        assert response.status_code == 401
    
    def test_owner_can_update_occupancy(
        self, authenticated_client, vacant_unit
    ):
        """Test that owner can update occupancy of their unit."""
        url = reverse("units:unit-update-occupancy", args=[vacant_unit.id])
        data = {
            "is_occupied": True,
            "occupant_name": "John Doe",
            "occupant_phone": "+1234567890",
        }
        
        response = authenticated_client.patch(url, data, format="json")
        
        assert response.status_code == 200
        assert response.data["is_occupied"] is True
        assert response.data["occupant_name"] == "John Doe"
        
        vacant_unit.refresh_from_db()
        assert vacant_unit.is_occupied is True
        assert vacant_unit.occupant_name == "John Doe"
    
    def test_user_cannot_update_other_users_occupancy(
        self, authenticated_client, other_users_unit
    ):
        """Test that user cannot update another user's unit occupancy."""
        url = reverse("units:unit-update-occupancy", args=[other_users_unit.id])
        data = {"is_occupied": True, "occupant_name": "Hacker"}
        
        response = authenticated_client.patch(url, data, format="json")
        
        assert response.status_code in [403, 404]
    
    def test_mark_as_unoccupied_clears_info(
        self, authenticated_client, occupied_unit
    ):
        """Test that marking as unoccupied clears occupant info."""
        url = reverse("units:unit-update-occupancy", args=[occupied_unit.id])
        data = {"is_occupied": False}
        
        response = authenticated_client.patch(url, data, format="json")
        
        assert response.status_code == 200
        assert response.data["is_occupied"] is False
        assert response.data["occupant_name"] is None
        assert response.data["occupant_phone"] is None
        
        occupied_unit.refresh_from_db()
        assert occupied_unit.occupant_name is None
        assert occupied_unit.occupant_phone is None
        
    def test_update_only_occupant_name(self, authenticated_client, vacant_unit):
        """Test updating only occupant name."""
        url = reverse("units:unit-update-occupancy", args=[vacant_unit.id])
        data = {
            "is_occupied": True,
            "occupant_name": "John Doe",
        }
        
        response = authenticated_client.patch(url, data, format="json")
        
        assert response.status_code == 200
        
        vacant_unit.refresh_from_db()
        assert vacant_unit.occupant_name == "John Doe"
        assert vacant_unit.occupant_phone is None
    
    def test_update_only_occupant_phone(self, authenticated_client, vacant_unit):
        """Test updating only occupant phone."""
        url = reverse("units:unit-update-occupancy", args=[vacant_unit.id])
        data = {
            "is_occupied": True,
            "occupant_phone": "+1234567890",
        }
        
        response = authenticated_client.patch(url, data, format="json")
        
        assert response.status_code == 200
        
        vacant_unit.refresh_from_db()
        assert vacant_unit.occupant_phone == "+1234567890"
        assert vacant_unit.occupant_name is None
    
    def test_update_occupancy_validates_consistency(
        self, authenticated_client, unit
    ):
        """Test that occupancy validation works."""
        url = reverse("units:unit-update-occupancy", args=[unit.id])
        data = {
            "is_occupied": False,
            "occupant_name": "John Doe",
        }
        
        response = authenticated_client.patch(url, data, format="json")
        
        assert response.status_code == 400
    
    def test_update_occupancy_updates_timestamp(
        self, authenticated_client, vacant_unit
    ):
        """Test that update_occupancy updates updated_at."""
        original_updated_at = vacant_unit.updated_at
        
        url = reverse("units:unit-update-occupancy", args=[vacant_unit.id])
        data = {
            "is_occupied": True,
            "occupant_name": "John Doe",
        }
        
        authenticated_client.patch(url, data, format="json")
        
        vacant_unit.refresh_from_db()
        assert vacant_unit.updated_at > original_updated_at
    
    def test_jwt_authentication_works(self, jwt_client, user):
        """Test that JWT authentication works for update occupancy."""
        estate = estate_factory()
        
        # Create unit with estate
        unit = Unit.objects.create(
            owner=user,
            estate=estate,  # ADD THIS
            identifier="Test",
            unit_type=Unit.UnitType.HOUSE
        )
        
        url = reverse("units:unit-update-occupancy", args=[unit.id])
        data = {
            "is_occupied": True,
            "occupant_name": "John Doe",
        }
        
        response = jwt_client.patch(url, data, format="json")
        
        assert response.status_code == 200
        
        unit.refresh_from_db()
        assert unit.is_occupied is True