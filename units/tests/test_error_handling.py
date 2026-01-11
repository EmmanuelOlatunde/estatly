# tests/test_error_handling.py
"""
Tests for error handling and exception responses.

Coverage:
- Malformed requests
- Invalid data types
- Missing required fields
- Invalid foreign keys
- Invalid UUIDs
- Server error scenarios
- Error response format
"""

import pytest
from django.urls import reverse
import uuid
from units.models import Unit
from .factories import UnitFactory
from .factories import EstateFactory as estate_factory


@pytest.mark.django_db
class TestMalformedRequests:
    """Test handling of malformed HTTP requests."""
    
    def test_malformed_json_body(self, authenticated_client):
        """Test that malformed JSON returns appropriate error."""
        url = reverse("units:unit-list")
        response = authenticated_client.post(
            url,
            data="{invalid json: no closing bracket",
            content_type="application/json"
        )
        
        assert response.status_code == 400
    
    def test_empty_json_body(self, authenticated_client):
        """Test POST with empty JSON body."""
        url = reverse("units:unit-list")
        response = authenticated_client.post(
            url,
            data={},
            format="json"
        )
        
        assert response.status_code == 400
        assert "identifier" in response.data
    
    def test_null_json_body(self, authenticated_client):
        """Test POST with null as body."""
        url = reverse("units:unit-list")
        response = authenticated_client.post(
            url,
            data=None,
            content_type="application/json"
        )
        
        assert response.status_code == 400


@pytest.mark.django_db
class TestInvalidDataTypes:
    """Test validation of incorrect data types."""
    
    def test_identifier_as_number(self, authenticated_client):
        """Test sending number instead of string for identifier."""
        url = reverse("units:unit-list")
        data = {
            "identifier": 12345,
            "unit_type": Unit.UnitType.HOUSE,
        }
        
        response = authenticated_client.post(url, data, format="json")
        
        assert response.status_code in [201, 400]
    
    def test_is_occupied_as_string(self, authenticated_client):
        """Test sending string instead of boolean."""
        url = reverse("units:unit-list")
        data = {
            "identifier": "House 1",
            "unit_type": Unit.UnitType.HOUSE,
            "is_occupied": "yes",
        }
        
        response = authenticated_client.post(url, data, format="json")
        
        assert response.status_code == 400
    
    def test_unit_type_as_number(self, authenticated_client):
        """Test sending invalid unit type."""
        url = reverse("units:unit-list")
        data = {
            "identifier": "House 1",
            "unit_type": 999,
        }
        
        response = authenticated_client.post(url, data, format="json")
        
        assert response.status_code == 400


@pytest.mark.django_db
class TestMissingRequiredFields:
    """Test validation of missing required fields."""
    
    def test_missing_identifier(self, authenticated_client):
        """Test creating unit without identifier."""
        url = reverse("units:unit-list")
        data = {
            "unit_type": Unit.UnitType.HOUSE,
        }
        
        response = authenticated_client.post(url, data, format="json")
        
        assert response.status_code == 400
        assert "identifier" in response.data
    
    def test_missing_unit_type(self, authenticated_client): 
        """Test creating unit without unit_type."""
        url = reverse("units:unit-list")
        estate = estate_factory() 
        
        data = {
            "identifier": "House 1",
            # "unit_type": Unit.UnitType.HOUSE,
            "estate": str(estate.id),
        }
        
        response = authenticated_client.post(url, data, format="json")
        
        assert response.status_code == 400
        assert "unit_type" in response.data
    
    def test_partial_update_missing_fields_ok(
        self, authenticated_client, unit
    ):
        """Test that partial update doesn't require all fields."""
        url = reverse("units:unit-detail", args=[unit.id])
        data = {"description": "Updated"}
        
        response = authenticated_client.patch(url, data, format="json")
        
        assert response.status_code == 200


@pytest.mark.django_db
class TestInvalidUUIDs:
    """Test handling of invalid UUID values."""
    
    def test_retrieve_with_invalid_uuid(self, authenticated_client):
        """Test retrieving unit with invalid UUID format."""
        url = reverse("units:unit-detail", args=["not-a-uuid"])
        response = authenticated_client.get(url)
        
        assert response.status_code == 404
    
    def test_update_with_invalid_uuid(self, authenticated_client):
        """Test updating unit with invalid UUID."""
        url = reverse("units:unit-detail", args=["invalid-uuid"])
        data = {"identifier": "New Name"}
        
        response = authenticated_client.patch(url, data, format="json")
        
        assert response.status_code == 404
    
    def test_delete_with_invalid_uuid(self, authenticated_client):
        """Test deleting unit with invalid UUID."""
        url = reverse("units:unit-detail", args=["bad-uuid"])
        response = authenticated_client.delete(url)
        
        assert response.status_code == 404
    
    def test_valid_uuid_nonexistent_resource(self, authenticated_client):
        """Test valid UUID but non-existent resource."""
        fake_id = uuid.uuid4()
        url = reverse("units:unit-detail", args=[fake_id])
        response = authenticated_client.get(url)
        
        assert response.status_code == 404


@pytest.mark.django_db
class TestBusinessRuleViolations:
    """Test validation of business rule violations."""
    
    def test_duplicate_identifier_same_owner(self, authenticated_client, user):
        """Test that duplicate identifier for same owner fails."""
        estate = estate_factory()
        
        Unit.objects.create(
            owner=user,
            identifier="House 1",
            unit_type=Unit.UnitType.HOUSE,
            estate=estate
        )
        
        url = reverse("units:unit-list")
        
        data = {
            "identifier": "House 1",
            "unit_type": Unit.UnitType.HOUSE,
            "estate": str(estate.id),
        }
        
        response = authenticated_client.post(url, data, format="json")
        
        assert response.status_code == 400
        # Check for DRF's standard unique validation error
        assert "non_field_errors" in response.data or "error" in response.data
        
        # More specific assertion
        if "non_field_errors" in response.data:
            error_msg = str(response.data["non_field_errors"][0])
            assert "unique" in error_msg.lower()



    def test_occupied_without_info_fails(self, authenticated_client):
        """Test that marking as occupied without info fails."""
        url = reverse("units:unit-list")
        data = {
            "identifier": "House 1",
            "unit_type": Unit.UnitType.HOUSE,
            "is_occupied": False,
            "occupant_name": "John Doe",
        }
        
        response = authenticated_client.post(url, data, format="json")
        
        assert response.status_code == 400


@pytest.mark.django_db
class TestErrorResponseFormat:
    """Test that error responses have consistent format."""
    
    def test_validation_error_has_field_names(self, authenticated_client):
        """Test that validation errors include field names."""
        url = reverse("units:unit-list")
        data = {
            "unit_type": Unit.UnitType.HOUSE,
        }
        
        response = authenticated_client.post(url, data, format="json")
        
        assert response.status_code == 400
        assert isinstance(response.data, dict)
        assert "identifier" in response.data
        
    def test_service_error_has_message(self, authenticated_client, user):
        """Test that service errors have descriptive messages."""
        estate = estate_factory()
        
        Unit.objects.create(
            owner=user,
            identifier="Duplicate",
            unit_type=Unit.UnitType.HOUSE,
            estate=estate
        )
        
        url = reverse("units:unit-list")
        
        data = {
            "identifier": "Duplicate",
            "unit_type": Unit.UnitType.HOUSE,
            "estate": str(estate.id),
        }
        
        response = authenticated_client.post(url, data, format="json")
        
        assert response.status_code == 400
        assert isinstance(response.data, dict)
        
        # Accept either error format
        if "error" in response.data:
            assert isinstance(response.data["error"], str)
        elif "non_field_errors" in response.data:
            assert len(response.data["non_field_errors"]) > 0
            assert isinstance(response.data["non_field_errors"][0], str)


    def test_not_found_error_message(self, authenticated_client):
        """Test that 404 errors have appropriate message."""
        fake_id = uuid.uuid4()
        url = reverse("units:unit-detail", args=[fake_id])
        response = authenticated_client.get(url)
        
        assert response.status_code == 404
    
    def test_authentication_error_format(self, api_client, unit):
        """Test that authentication errors are properly formatted."""
        url = reverse("units:unit-detail", args=[unit.id])
        response = api_client.get(url)
        
        assert response.status_code == 401
        assert "detail" in response.data


@pytest.mark.django_db
class TestConcurrentModification:
    """Test handling of concurrent modifications."""
    
    def test_update_after_delete(self, authenticated_client, unit):
        """Test updating a unit after it's been deleted."""
        unit_id = unit.id
        url = reverse("units:unit-detail", args=[unit_id])
        
        authenticated_client.delete(url)
        
        response = authenticated_client.patch(
            url,
            {"identifier": "New Name"},
            format="json"
        )
        
        assert response.status_code == 404
    
    def test_delete_after_delete(self, authenticated_client, unit):
        """Test deleting a unit that's already deleted."""
        url = reverse("units:unit-detail", args=[unit.id])
        
        authenticated_client.delete(url)
        response = authenticated_client.delete(url)
        
        assert response.status_code == 404


@pytest.mark.django_db
class TestInvalidQueryParameters:
    """Test handling of invalid query parameters."""
    
    def test_invalid_filter_value_ignored(self, authenticated_client, user):
        """Test that invalid filter values are handled gracefully."""
        UnitFactory.create_batch(2, owner=user)
        
        url = reverse("units:unit-list")
        response = authenticated_client.get(url, {"unit_type": "INVALID"})
        
        assert response.status_code == 200
    
    def test_invalid_boolean_filter(self, authenticated_client, user):
        """Test invalid boolean value in filter."""
        UnitFactory.create_batch(2, owner=user)
        
        url = reverse("units:unit-list")
        response = authenticated_client.get(url, {"is_occupied": "maybe"})
        
        assert response.status_code == 200
    
    def test_sql_injection_attempt_in_search(self, authenticated_client, user):
        """Test that SQL injection attempts are safely handled."""
        UnitFactory.create(owner=user, identifier="Safe Unit")
        
        url = reverse("units:unit-list")
        response = authenticated_client.get(
            url,
            {"search": "'; DROP TABLE units; --"}
        )
        
        assert response.status_code == 200
        assert Unit.objects.count() == 1