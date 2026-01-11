# tests/test_views_create.py
"""
Tests for units app create endpoints.

Coverage:
- Authentication/authorization for create
- Success paths with valid data
- Validation failures
- Database side effects
- Field requirements
"""

import pytest
from django.urls import reverse
from units.models import Unit
from .helpers import assert_response_has_keys
from .factories import EstateFactory as estate_factory


@pytest.mark.django_db
class TestUnitCreateEndpoint:
    """Test POST /units/ endpoint."""
    
    def test_unauthenticated_user_denied(self, api_client):
        """Test that unauthenticated users cannot create units."""
        url = reverse("units:unit-list")
        data = {"identifier": "House 1", "unit_type": Unit.UnitType.HOUSE}
        response = api_client.post(url, data)
        
        assert response.status_code == 401
    
    def test_create_unit_with_minimal_data(self, authenticated_client, user):
        """Test creating unit with only required fields."""
        url = reverse("units:unit-list")
        # Create estate without owner parameter - Estate doesn't accept it
        estate = estate_factory() 
        
        data = {
            "identifier": "House 1",
            "unit_type": Unit.UnitType.HOUSE,
            "estate": str(estate.id),
        }
        response = authenticated_client.post(url, data, format="json")
        assert response.status_code == 201
        assert response.data["identifier"] == "House 1"
        assert response.data["unit_type"] == Unit.UnitType.HOUSE
        # Owner is returned as UUID object, not string
        assert str(response.data["owner"]) == str(user.id)
        
        unit = Unit.objects.get(id=response.data["id"])
        assert unit.owner == user
        assert unit.identifier == "House 1"
    
    def test_create_unit_with_all_fields(self, authenticated_client, user):
        """Test creating unit with all optional fields."""
        url = reverse("units:unit-list")
        # Create estate first
        estate = estate_factory()
        
        data = {
            "identifier": "Flat B3",
            "unit_type": Unit.UnitType.FLAT,
            "estate": str(estate.id),  # Required field
            "occupant_name": "John Doe",
            "occupant_phone": "+1234567890",
            "description": "Two bedroom flat",
            "is_occupied": True,
            "is_active": True,
        }
        
        response = authenticated_client.post(url, data, format="json")
        
        assert response.status_code == 201
        assert response.data["identifier"] == "Flat B3"
        assert response.data["occupant_name"] == "John Doe"
        assert response.data["occupant_phone"] == "+1234567890"
        assert response.data["is_occupied"] is True
        
        unit = Unit.objects.get(id=response.data["id"])
        assert unit.occupant_name == "John Doe"
        assert unit.is_occupied is True
    
    def test_missing_identifier_fails(self, authenticated_client):
        """Test that missing identifier returns 400."""
        url = reverse("units:unit-list")
        estate = estate_factory()
        data = {
            "unit_type": Unit.UnitType.HOUSE,
            "estate": str(estate.id),
        }
        
        response = authenticated_client.post(url, data, format="json")
        
        assert response.status_code == 400
        assert "identifier" in response.data
    
    def test_empty_identifier_fails(self, authenticated_client):
        """Test that empty identifier returns 400."""
        url = reverse("units:unit-list")
        estate = estate_factory()
        data = {
            "identifier": "   ",
            "unit_type": Unit.UnitType.HOUSE,
            "estate": str(estate.id),
        }
        
        response = authenticated_client.post(url, data, format="json")
        
        assert response.status_code == 400
        assert "identifier" in response.data
    
    def test_identifier_whitespace_stripped(self, authenticated_client, user):
        """Test that identifier whitespace is stripped."""
        url = reverse("units:unit-list")
        estate = estate_factory()
        data = {
            "identifier": "  House 1  ",
            "unit_type": Unit.UnitType.HOUSE,
            "estate": str(estate.id),
        }
        
        response = authenticated_client.post(url, data, format="json")
        
        assert response.status_code == 201
        
        unit = Unit.objects.get(id=response.data["id"])
        assert unit.identifier == "House 1"
    
    def test_identifier_too_long_fails(self, authenticated_client):
        """Test that identifier over 100 characters fails."""
        url = reverse("units:unit-list")
        estate = estate_factory()
        data = {
            "identifier": "x" * 101,
            "unit_type": Unit.UnitType.HOUSE,
            "estate": str(estate.id),
        }
        
        response = authenticated_client.post(url, data, format="json")
        
        assert response.status_code == 400
        assert "identifier" in response.data
    
    def test_occupant_info_without_occupied_fails(self, authenticated_client, user):
        """Test that occupant info without is_occupied=True fails."""
        url = reverse("units:unit-list")
        estate = estate_factory()

        data = {
            "identifier": "House 1",
            "unit_type": Unit.UnitType.HOUSE,
            "estate": str(estate.id),
            "is_occupied": False,
            "occupant_name": "Jane Doe",  # This should fail validation
        }
        
        response = authenticated_client.post(url, data, format="json")
        
        assert response.status_code == 400
        assert "non_field_errors" in response.data or "error" in response.data
    
    def test_duplicate_identifier_for_same_user_fails(
        self, authenticated_client, user
    ):
        """Test that duplicate identifier for same user fails."""
        url = reverse("units:unit-list")
        estate = estate_factory()
        
        data = {
            "identifier": "House 1",
            "unit_type": Unit.UnitType.HOUSE,
            "estate": str(estate.id),
        }
        
        # Create first unit
        authenticated_client.post(url, data, format="json")
        # Try to create duplicate
        response = authenticated_client.post(url, data, format="json")
        
        assert response.status_code == 400
        # Django unique constraint returns 'non_field_errors', not 'error'
        assert "non_field_errors" in response.data or "error" in response.data
    
    def test_duplicate_identifier_for_different_users_allowed(
        self, authenticated_client, other_user_client, user, other_user
    ):
        """Test that different users can use same identifier."""
        url = reverse("units:unit-list")
        # Create separate estates for each user
        estate1 = estate_factory()
        estate2 = estate_factory()
        
        data1 = {
            "identifier": "House 1",
            "unit_type": Unit.UnitType.HOUSE,
            "estate": str(estate1.id),
        }
        
        data2 = {
            "identifier": "House 1",
            "unit_type": Unit.UnitType.HOUSE,
            "estate": str(estate2.id),
        }
        
        response1 = authenticated_client.post(url, data1, format="json")
        response2 = other_user_client.post(url, data2, format="json")
        
        assert response1.status_code == 201
        assert response2.status_code == 201
        
        unit1 = Unit.objects.get(id=response1.data["id"])
        unit2 = Unit.objects.get(id=response2.data["id"])
        
        assert unit1.owner == user
        assert unit2.owner == other_user
        assert unit1.identifier == unit2.identifier
    
    def test_invalid_unit_type_fails(self, authenticated_client):
        """Test that invalid unit type fails."""
        url = reverse("units:unit-list")
        estate = estate_factory()
        data = {
            "identifier": "House 1",
            "unit_type": "INVALID_TYPE",
            "estate": str(estate.id),
        }
        
        response = authenticated_client.post(url, data, format="json")
        
        assert response.status_code == 400
        assert "unit_type" in response.data or "error" in response.data
    
    def test_create_sets_timestamps(self, authenticated_client, user):
        """Test that created_at and updated_at are set."""
        url = reverse("units:unit-list")
        estate = estate_factory()
        data = {
            "identifier": "House 1",
            "unit_type": Unit.UnitType.HOUSE,
            "estate": str(estate.id),
        }
        
        response = authenticated_client.post(url, data, format="json")
        
        assert response.status_code == 201
        
        unit = Unit.objects.get(id=response.data["id"])
        assert unit.created_at is not None
        assert unit.updated_at is not None
    
    def test_create_returns_full_unit_representation(
        self, authenticated_client, user
    ):
        """Test that create returns full unit serialization."""
        url = reverse("units:unit-list")
        estate = estate_factory()
        data = {
            "identifier": "House 1",
            "unit_type": Unit.UnitType.HOUSE,
            "estate": str(estate.id),
        }
        
        response = authenticated_client.post(url, data, format="json")
        
        assert response.status_code == 201
        
        expected_fields = [
            "id", "identifier", "unit_type", "unit_type_display",
            "owner", "owner_email", "occupant_name", "occupant_phone",
            "description", "is_occupied", "is_active",
            "has_occupant_info", "created_at", "updated_at"
        ]
        assert_response_has_keys(response.data, expected_fields)
    
    def test_jwt_authentication_works(self, jwt_client, user):
        """Test that JWT authentication works for create."""
        url = reverse("units:unit-list")
        estate = estate_factory()
        data = {
            "identifier": "House 1",
            "unit_type": Unit.UnitType.HOUSE,
            "estate": str(estate.id),
        }
        
        response = jwt_client.post(url, data, format="json")
        
        assert response.status_code == 201
        
        unit = Unit.objects.get(id=response.data["id"])
        assert unit.owner == user
    
    def test_malformed_json_fails(self, authenticated_client):
        """Test that malformed JSON returns 400."""
        url = reverse("units:unit-list")
        response = authenticated_client.post(
            url,
            data="{invalid json",
            content_type="application/json"
        )
        
        assert response.status_code == 400
    
    def test_create_with_invalid_phone_format_fails(self, authenticated_client):
        """Test that invalid phone format fails validation."""
        url = reverse("units:unit-list")
        estate = estate_factory()
        data = {
            "identifier": "House 1",
            "unit_type": Unit.UnitType.HOUSE,
            "estate": str(estate.id),
            "is_occupied": True,
            "occupant_phone": "invalid-phone",
        }
        
        response = authenticated_client.post(url, data, format="json")
        
        assert response.status_code == 400
    
    def test_create_defaults_is_active_to_true(self, authenticated_client, user):
        """Test that is_active defaults to True."""
        url = reverse("units:unit-list")
        estate = estate_factory()
        data = {
            "identifier": "House 1",
            "unit_type": Unit.UnitType.HOUSE,
            "estate": str(estate.id),
        }
        
        response = authenticated_client.post(url, data, format="json")
        
        assert response.status_code == 201
        
        unit = Unit.objects.get(id=response.data["id"])
        assert unit.is_active is True