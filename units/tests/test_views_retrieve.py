# tests/test_views_retrieve.py
"""
Tests for units app retrieve/detail endpoints.

Coverage:
- Authentication/authorization for detail endpoint
- Success paths
- Not found scenarios
- Cross-user access prevention
"""

import pytest
from django.urls import reverse
import uuid
from .factories import UnitFactory
from .helpers import assert_response_has_keys


@pytest.mark.django_db
class TestUnitRetrieveEndpoint:
    """Test GET /units/{id}/ endpoint."""
    
    def test_unauthenticated_user_denied(self, api_client, unit):
        """Test that unauthenticated users get 401."""
        url = reverse("units:unit-detail", args=[unit.id])
        response = api_client.get(url)
        assert response.status_code == 401
    
    def test_owner_can_retrieve_own_unit(self, authenticated_client, unit):
        """Test that owner can retrieve their own unit."""
        url = reverse("units:unit-detail", args=[unit.id])
        response = authenticated_client.get(url)
        
        assert response.status_code == 200
        assert response.data["id"] == str(unit.id)
        assert response.data["identifier"] == unit.identifier
    
    def test_user_cannot_retrieve_other_users_unit(
        self, authenticated_client, other_users_unit
    ):
        """Test that user cannot retrieve another user's unit."""
        url = reverse("units:unit-detail", args=[other_users_unit.id])
        response = authenticated_client.get(url)
        
        assert response.status_code == 404
    
    def test_retrieve_nonexistent_unit_returns_404(self, authenticated_client):
        """Test that retrieving non-existent unit returns 404."""
        fake_id = uuid.uuid4()
        url = reverse("units:unit-detail", args=[fake_id])
        response = authenticated_client.get(url)
        
        assert response.status_code == 404
    
    def test_retrieve_includes_all_fields(self, authenticated_client, user):
        """Test that retrieve response includes all expected fields."""
        unit = UnitFactory.create(
            owner=user,
            identifier="Test Unit",
            occupant_name="John Doe",
            occupant_phone="+1234567890",
            is_occupied=True
        )
        
        url = reverse("units:unit-detail", args=[unit.id])
        response = authenticated_client.get(url)
        
        assert response.status_code == 200
        
        expected_fields = [
            "id", "identifier", "unit_type", "unit_type_display",
            "owner", "owner_email", "occupant_name", "occupant_phone",
            "description", "is_occupied", "is_active",
            "has_occupant_info", "created_at", "updated_at"
        ]
        assert_response_has_keys(response.data, expected_fields)
    
    def test_retrieve_includes_owner_email(self, authenticated_client, user):
        """Test that owner email is included in response."""
        unit = UnitFactory.create(owner=user)
        url = reverse("units:unit-detail", args=[unit.id])
        
        response = authenticated_client.get(url)
        
        assert response.status_code == 200
        assert response.data["owner_email"] == user.email
    
    def test_retrieve_includes_computed_fields(self, authenticated_client, user):
        """Test that computed fields are included."""
        unit = UnitFactory.create(
            owner=user,
            occupant_name="John Doe",
            is_occupied=True
        )
        url = reverse("units:unit-detail", args=[unit.id])
        
        response = authenticated_client.get(url)
        
        assert response.status_code == 200
        assert "has_occupant_info" in response.data
        assert response.data["has_occupant_info"] is True
    
    def test_retrieve_inactive_unit_requires_param(
        self, authenticated_client, user
    ):
        """Test that inactive units are not retrieved by default."""
        unit = UnitFactory.create(owner=user, is_active=False)
        url = reverse("units:unit-detail", args=[unit.id])
        
        response = authenticated_client.get(url)
        
        assert response.status_code == 404
    
    def test_jwt_authentication_works(self, jwt_client, user):
        """Test that JWT authentication works for retrieve endpoint."""
        unit = UnitFactory.create(owner=user)
        url = reverse("units:unit-detail", args=[unit.id])
        
        response = jwt_client.get(url)
        
        assert response.status_code == 200
        assert response.data["id"] == str(unit.id)
    
    def test_retrieve_with_invalid_uuid_returns_404(self, authenticated_client):
        """Test that invalid UUID returns 404."""
        url = reverse("units:unit-detail", args=["invalid-uuid"])
        response = authenticated_client.get(url)
        
        assert response.status_code == 404
    
    def test_admin_cannot_access_other_users_unit(
        self, admin_client, other_users_unit
    ):
        """Test that even admin cannot access other users' units without ownership."""
        url = reverse("units:unit-detail", args=[other_users_unit.id])
        response = admin_client.get(url)
        
        assert response.status_code == 404
    
    def test_retrieve_occupied_unit_includes_occupant_info(
        self, authenticated_client, occupied_unit
    ):
        """Test that occupied unit includes occupant information."""
        url = reverse("units:unit-detail", args=[occupied_unit.id])
        response = authenticated_client.get(url)
        
        assert response.status_code == 200
        assert response.data["is_occupied"] is True
        assert response.data["occupant_name"] is not None
        assert response.data["occupant_phone"] is not None
    
    def test_retrieve_vacant_unit_has_no_occupant_info(
        self, authenticated_client, vacant_unit
    ):
        """Test that vacant unit has no occupant information."""
        url = reverse("units:unit-detail", args=[vacant_unit.id])
        response = authenticated_client.get(url)
        
        assert response.status_code == 200
        assert response.data["is_occupied"] is False
        assert response.data["occupant_name"] is None
        assert response.data["occupant_phone"] is None