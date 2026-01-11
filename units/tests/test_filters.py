# tests/test_filters.py
"""
Tests for units app filtering functionality.

Coverage:
- Filter by unit_type
- Filter by is_occupied
- Filter by is_active
- Search by identifier
- Search by occupant_name
- Combined filters
- Case-insensitive search
"""

import pytest
from django.urls import reverse
from units.models import Unit
from .factories import UnitFactory


@pytest.mark.django_db
class TestUnitFilters:
    """Test filtering functionality for units list endpoint."""
    
    def test_filter_by_unit_type(self, authenticated_client, user):
        """Test filtering units by unit_type."""
        houses = UnitFactory.create_batch(
            2, owner=user, unit_type=Unit.UnitType.HOUSE
        )
        flats = UnitFactory.create_batch(
            3, owner=user, unit_type=Unit.UnitType.FLAT
        )
        
        url = reverse("units:unit-list")
        response = authenticated_client.get(
            url, {"unit_type": Unit.UnitType.HOUSE}
        )
        
        assert response.status_code == 200
        assert response.data["count"] == 2
        
        returned_ids = {result["id"] for result in response.data["results"]}
        expected_ids = {str(house.id) for house in houses}
        assert returned_ids == expected_ids
    
    def test_filter_by_is_occupied_true(self, authenticated_client, user):
        """Test filtering for occupied units."""
        occupied = UnitFactory.create_batch(
            2, owner=user, is_occupied=True
        )
        vacant = UnitFactory.create_batch(
            3, owner=user, is_occupied=False
        )
        
        url = reverse("units:unit-list")
        response = authenticated_client.get(url, {"is_occupied": "true"})
        
        assert response.status_code == 200
        assert response.data["count"] == 2
    
    def test_filter_by_is_occupied_false(self, authenticated_client, user):
        """Test filtering for vacant units."""
        occupied = UnitFactory.create_batch(
            2, owner=user, is_occupied=True
        )
        vacant = UnitFactory.create_batch(
            3, owner=user, is_occupied=False
        )
        
        url = reverse("units:unit-list")
        response = authenticated_client.get(url, {"is_occupied": "false"})
        
        assert response.status_code == 200
        assert response.data["count"] == 3
    
    def test_filter_by_is_active(self, authenticated_client, user):
        """Test filtering by active status."""
        active = UnitFactory.create_batch(
            2, owner=user, is_active=True
        )
        
        url = reverse("units:unit-list")
        response = authenticated_client.get(url, {"is_active": "true"})
        
        assert response.status_code == 200
        assert response.data["count"] == 2
    
    def test_search_by_identifier(self, authenticated_client, user):
        """Test searching units by identifier."""
        matching = UnitFactory.create(owner=user, identifier="House 123")
        non_matching = UnitFactory.create(owner=user, identifier="Flat ABC")
        
        url = reverse("units:unit-list")
        response = authenticated_client.get(url, {"identifier": "House"})
        
        assert response.status_code == 200
        assert response.data["count"] == 1
        assert response.data["results"][0]["id"] == str(matching.id)
    
    def test_search_by_identifier_case_insensitive(
        self, authenticated_client, user
    ):
        """Test that identifier search is case-insensitive."""
        matching = UnitFactory.create(owner=user, identifier="House 123")
        
        url = reverse("units:unit-list")
        response = authenticated_client.get(url, {"identifier": "house"})
        
        assert response.status_code == 200
        assert response.data["count"] == 1
        assert response.data["results"][0]["id"] == str(matching.id)
    
    def test_search_by_occupant_name(self, authenticated_client, user):
        """Test searching units by occupant name."""
        matching = UnitFactory.create(
            owner=user,
            is_occupied=True,
            occupant_name="John Doe"
        )
        non_matching = UnitFactory.create(
            owner=user,
            is_occupied=True,
            occupant_name="Jane Smith"
        )
        
        url = reverse("units:unit-list")
        response = authenticated_client.get(url, {"occupant_name": "John"})
        
        assert response.status_code == 200
        assert response.data["count"] == 1
        assert response.data["results"][0]["id"] == str(matching.id)
    
    def test_search_by_occupant_name_case_insensitive(
        self, authenticated_client, user
    ):
        """Test that occupant name search is case-insensitive."""
        matching = UnitFactory.create(
            owner=user,
            is_occupied=True,
            occupant_name="John Doe"
        )
        
        url = reverse("units:unit-list")
        response = authenticated_client.get(url, {"occupant_name": "john"})
        
        assert response.status_code == 200
        assert response.data["count"] == 1
    
    def test_general_search_across_fields(self, authenticated_client, user):
        """Test general search across multiple fields."""
        unit1 = UnitFactory.create(
            owner=user,
            identifier="House Alpha",
            description="Nice property"
        )
        unit2 = UnitFactory.create(
            owner=user,
            identifier="Flat Beta",
            occupant_name="Alpha Johnson",
            is_occupied=True
        )
        unit3 = UnitFactory.create(
            owner=user,
            identifier="Studio Gamma",
            description="Modern space"
        )
        
        url = reverse("units:unit-list")
        response = authenticated_client.get(url, {"search": "Alpha"})
        
        assert response.status_code == 200
        assert response.data["count"] == 2
    
    def test_combined_filters(self, authenticated_client, user):
        """Test using multiple filters together."""
        matching = UnitFactory.create(
            owner=user,
            unit_type=Unit.UnitType.HOUSE,
            is_occupied=True
        )
        non_matching_type = UnitFactory.create(
            owner=user,
            unit_type=Unit.UnitType.FLAT,
            is_occupied=True
        )
        non_matching_occupancy = UnitFactory.create(
            owner=user,
            unit_type=Unit.UnitType.HOUSE,
            is_occupied=False
        )
        
        url = reverse("units:unit-list")
        response = authenticated_client.get(url, {
            "unit_type": Unit.UnitType.HOUSE,
            "is_occupied": "true"
        })
        
        assert response.status_code == 200
        assert response.data["count"] == 1
        assert response.data["results"][0]["id"] == str(matching.id)
    
    def test_filter_with_no_matches(self, authenticated_client, user):
        """Test filter that returns no results."""
        UnitFactory.create_batch(3, owner=user, unit_type=Unit.UnitType.HOUSE)
        
        url = reverse("units:unit-list")
        response = authenticated_client.get(
            url, {"unit_type": Unit.UnitType.STUDIO}
        )
        
        assert response.status_code == 200
        assert response.data["count"] == 0
        assert response.data["results"] == []
    
    def test_invalid_filter_ignored(self, authenticated_client, user):
        """Test that invalid filter parameters are handled gracefully."""
        UnitFactory.create_batch(2, owner=user)
        
        url = reverse("units:unit-list")
        response = authenticated_client.get(url, {"invalid_param": "value"})
        
        assert response.status_code == 200
        assert response.data["count"] == 2
    
    def test_date_range_filter_created_after(self, authenticated_client, user):
        """Test filtering by created_after date."""
        from datetime import  timedelta
        from django.utils import timezone
        
        old_unit = UnitFactory.create(owner=user)
        old_unit.created_at = timezone.now() - timedelta(days=10)
        old_unit.save()
        
        recent_unit = UnitFactory.create(owner=user)
        
        cutoff = (timezone.now() - timedelta(days=5)).isoformat()
        
        url = reverse("units:unit-list")
        response = authenticated_client.get(url, {"created_after": cutoff})
        
        assert response.status_code == 200
        assert response.data["count"] >= 1


@pytest.mark.django_db
class TestSearchFilter:
    """Test DRF SearchFilter functionality."""
    
    def test_search_query_param(self, authenticated_client, user):
        """Test using ?search= query parameter."""
        matching = UnitFactory.create(owner=user, identifier="Special Unit")
        non_matching = UnitFactory.create(owner=user, identifier="Regular")
        
        url = reverse("units:unit-list")
        response = authenticated_client.get(url, {"search": "Special"})
        
        assert response.status_code == 200
        assert response.data["count"] >= 1
    
    def test_search_partial_match(self, authenticated_client, user):
        """Test that search matches partial strings."""
        matching = UnitFactory.create(owner=user, identifier="House 123")
        
        url = reverse("units:unit-list")
        response = authenticated_client.get(url, {"search": "123"})
        
        assert response.status_code == 200
        assert response.data["count"] == 1