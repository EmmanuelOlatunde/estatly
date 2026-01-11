# tests/test_views_list.py
"""
Tests for units app list endpoints.

Coverage:
- Authentication/authorization for list endpoint
- Success paths
- Filtering by owner
- Empty results
- Pagination
"""

import pytest
from django.urls import reverse
from .factories import UnitFactory
from .helpers import assert_paginated_response


@pytest.mark.django_db
class TestUnitListEndpoint:
    """Test GET /units/ endpoint."""
    
    def test_unauthenticated_user_denied(self, api_client):
        """Test that unauthenticated users get 401."""
        url = reverse("units:unit-list")
        response = api_client.get(url)
        assert response.status_code == 401
    
    def test_authenticated_user_can_list_own_units(self, authenticated_client, user):
        """Test that authenticated user can list their units."""
        UnitFactory.create_batch(3, owner=user)
        url = reverse("units:unit-list")
        
        response = authenticated_client.get(url)
        
        assert response.status_code == 200
        assert_paginated_response(response, expected_count=3)
        assert len(response.data["results"]) == 3
    
    def test_user_cannot_see_other_users_units(
        self, authenticated_client, user, other_user
    ):
        """Test that users only see their own units."""
        my_units = UnitFactory.create_batch(3, owner=user)
        UnitFactory.create_batch(2, owner=other_user)

        url = reverse("units:unit-list")
        response = authenticated_client.get(url)

        assert response.status_code == 200
        assert response.data["count"] == 3

        # Get IDs from response
        response_unit_ids = {unit["id"] for unit in response.data["results"]}

        # Expected IDs from DB
        expected_unit_ids = {str(u.id) for u in my_units}  # str because UUID in JSON

        assert response_unit_ids == expected_unit_ids
    
    def test_empty_list_returns_empty_results(self, authenticated_client):
        """Test that empty list returns empty results array."""
        url = reverse("units:unit-list")
        response = authenticated_client.get(url)
        
        assert response.status_code == 200
        assert response.data["count"] == 0
        assert response.data["results"] == []
    
    def test_list_excludes_inactive_units_by_default(
        self, authenticated_client, user
    ):
        """Test that inactive units are excluded by default."""
        UnitFactory.create_batch(2, owner=user, is_active=True)
        UnitFactory.create_batch(3, owner=user, is_active=False)
        
        url = reverse("units:unit-list")
        response = authenticated_client.get(url)
        
        assert response.status_code == 200
        assert response.data["count"] == 2
    
    def test_list_includes_inactive_with_query_param(
        self, authenticated_client, user
    ):
        """Test that inactive units are included with include_inactive=true."""
        UnitFactory.create_batch(2, owner=user, is_active=True)
        UnitFactory.create_batch(3, owner=user, is_active=False)
        
        url = reverse("units:unit-list")
        response = authenticated_client.get(url, {"include_inactive": "true"})
        
        assert response.status_code == 200
        assert response.data["count"] == 5
    
    def test_response_has_correct_structure(self, authenticated_client, user):
        """Test that response has correct pagination structure."""
        UnitFactory.create(owner=user)
        url = reverse("units:unit-list")
        
        response = authenticated_client.get(url)
        
        assert response.status_code == 200
        assert "count" in response.data
        assert "next" in response.data
        assert "previous" in response.data
        assert "results" in response.data
    
    def test_unit_fields_in_list_response(self, authenticated_client, user):
        """Test that list response includes correct fields."""
        unit = UnitFactory.create(owner=user)
        url = reverse("units:unit-list")
        
        response = authenticated_client.get(url)
        
        assert response.status_code == 200
        unit_data = response.data["results"][0]
        
        expected_fields = {
            "id", "identifier", "unit_type", "unit_type_display",
            "occupant_name", "is_occupied", "is_active", "created_at"
        }
        assert set(unit_data.keys()) == expected_fields
        assert unit_data["id"] == str(unit.id)
        assert unit_data["identifier"] == unit.identifier
    
    def test_jwt_authentication_works(self, jwt_client, user):
        """Test that JWT authentication works for list endpoint."""
        UnitFactory.create_batch(2, owner=user)
        url = reverse("units:unit-list")
        
        response = jwt_client.get(url)
        
        assert response.status_code == 200
        assert response.data["count"] == 2
    
    def test_admin_can_list_units(self, admin_client, admin_user):
        """Test that admin users can list their units."""
        UnitFactory.create_batch(2, owner=admin_user)
        url = reverse("units:unit-list")
        
        response = admin_client.get(url)
        
        assert response.status_code == 200
        assert response.data["count"] == 2
    
    def test_ordering_by_identifier_default(self, authenticated_client, user):
        """Test that results are ordered by identifier by default."""
        unit_a = UnitFactory.create(owner=user, identifier="A Unit")
        unit_b = UnitFactory.create(owner=user, identifier="B Unit")
        unit_c = UnitFactory.create(owner=user, identifier="C Unit")
        
        url = reverse("units:unit-list")
        response = authenticated_client.get(url)
        
        assert response.status_code == 200
        results = response.data["results"]
        assert results[0]["id"] == str(unit_a.id)
        assert results[1]["id"] == str(unit_b.id)
        assert results[2]["id"] == str(unit_c.id)


@pytest.mark.django_db
class TestOccupiedUnitsEndpoint:
    """Test GET /units/occupied/ endpoint."""
    
    def test_unauthenticated_user_denied(self, api_client):
        """Test that unauthenticated users get 401."""
        url = reverse("units:unit-occupied")
        response = api_client.get(url)
        assert response.status_code == 401
    
    def test_returns_only_occupied_units(self, authenticated_client, user):
        """Test that only occupied units are returned."""
        occupied = UnitFactory.create_batch(2, owner=user, is_occupied=True)
        vacant = UnitFactory.create_batch(3, owner=user, is_occupied=False)  # noqa: F841
        
        url = reverse("units:unit-occupied")
        response = authenticated_client.get(url)
        
        assert response.status_code == 200
        assert len(response.data) == 2
        
        returned_ids = {unit["id"] for unit in response.data}
        expected_ids = {str(unit.id) for unit in occupied}
        assert returned_ids == expected_ids
    
    def test_excludes_other_users_occupied_units(
        self, authenticated_client, user, other_user
    ):
        """Test that other users' occupied units are excluded."""
        UnitFactory.create_batch(2, owner=user, is_occupied=True)
        UnitFactory.create_batch(3, owner=other_user, is_occupied=True)
        
        url = reverse("units:unit-occupied")
        response = authenticated_client.get(url)
        
        assert response.status_code == 200
        assert len(response.data) == 2
    
    def test_empty_result_when_no_occupied_units(self, authenticated_client, user):
        """Test that empty list is returned when no occupied units."""
        UnitFactory.create_batch(3, owner=user, is_occupied=False)
        
        url = reverse("units:unit-occupied")
        response = authenticated_client.get(url)
        
        assert response.status_code == 200
        assert len(response.data) == 0


@pytest.mark.django_db
class TestVacantUnitsEndpoint:
    """Test GET /units/vacant/ endpoint."""
    
    def test_unauthenticated_user_denied(self, api_client):
        """Test that unauthenticated users get 401."""
        url = reverse("units:unit-vacant")
        response = api_client.get(url)
        assert response.status_code == 401
    
    def test_returns_only_vacant_units(self, authenticated_client, user):
        """Test that only vacant units are returned."""
        vacant = UnitFactory.create_batch(3, owner=user, is_occupied=False)
        occupied = UnitFactory.create_batch(2, owner=user, is_occupied=True)  # noqa: F841
        
        url = reverse("units:unit-vacant")
        response = authenticated_client.get(url)
        
        assert response.status_code == 200
        assert len(response.data) == 3
        
        returned_ids = {unit["id"] for unit in response.data}
        expected_ids = {str(unit.id) for unit in vacant}
        assert returned_ids == expected_ids
    
    def test_excludes_other_users_vacant_units(
        self, authenticated_client, user, other_user
    ):
        """Test that other users' vacant units are excluded."""
        UnitFactory.create_batch(3, owner=user, is_occupied=False)
        UnitFactory.create_batch(2, owner=other_user, is_occupied=False)
        
        url = reverse("units:unit-vacant")
        response = authenticated_client.get(url)
        
        assert response.status_code == 200
        assert len(response.data) == 3
    
    def test_empty_result_when_no_vacant_units(self, authenticated_client, user):
        """Test that empty list is returned when no vacant units."""
        UnitFactory.create_batch(3, owner=user, is_occupied=True)
        
        url = reverse("units:unit-vacant")
        response = authenticated_client.get(url)
        
        assert response.status_code == 200
        assert len(response.data) == 0