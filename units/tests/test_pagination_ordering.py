# tests/test_pagination_ordering.py
"""
Tests for pagination and ordering functionality.

Coverage:
- Pagination metadata
- Page navigation
- Page size limits
- Ordering by different fields
- Ascending/descending order
"""

import pytest
from django.urls import reverse
from units.models import Unit
from .factories import UnitFactory


@pytest.mark.django_db
class TestPagination:
    """Test pagination for units list endpoint."""
    
    def test_pagination_metadata_present(self, authenticated_client, user):
        """Test that pagination metadata is included in response."""
        UnitFactory.create_batch(5, owner=user)
        
        url = reverse("units:unit-list")
        response = authenticated_client.get(url)
        
        assert response.status_code == 200
        assert "count" in response.data
        assert "next" in response.data
        assert "previous" in response.data
        assert "results" in response.data
    
    def test_pagination_count_accurate(self, authenticated_client, user):
        """Test that count field reflects actual number of results."""
        UnitFactory.create_batch(7, owner=user)
        
        url = reverse("units:unit-list")
        response = authenticated_client.get(url)
        
        assert response.status_code == 200
        assert response.data["count"] == 7
    
    def test_first_page_has_no_previous(self, authenticated_client, user):
        """Test that first page has no previous link."""
        UnitFactory.create_batch(30, owner=user)
        
        url = reverse("units:unit-list")
        response = authenticated_client.get(url)
        
        assert response.status_code == 200
        assert response.data["previous"] is None
    
    def test_pagination_page_parameter(self, authenticated_client, user):
        """Test navigating to specific page."""
        UnitFactory.create_batch(30, owner=user)
        
        url = reverse("units:unit-list")
        response = authenticated_client.get(url, {"page": "2"})
        
        assert response.status_code == 200
        assert response.data["previous"] is not None
    
    def test_invalid_page_number(self, authenticated_client, user):
        """Test requesting invalid page number."""
        UnitFactory.create_batch(5, owner=user)
        
        url = reverse("units:unit-list")
        response = authenticated_client.get(url, {"page": "999"})
        
        assert response.status_code == 404
    
    def test_page_size_parameter(self, authenticated_client, user):
        """Test custom page size parameter."""
        UnitFactory.create_batch(10, owner=user)
        
        url = reverse("units:unit-list")
        response = authenticated_client.get(url, {"page_size": "5"})
        
        assert response.status_code == 200
        assert len(response.data["results"]) == 5
    
    def test_page_zero_invalid(self, authenticated_client, user):
        """Test that page 0 is invalid."""
        UnitFactory.create_batch(5, owner=user)
        
        url = reverse("units:unit-list")
        response = authenticated_client.get(url, {"page": "0"})
        
        assert response.status_code == 404
    
    def test_negative_page_invalid(self, authenticated_client, user):
        """Test that negative page numbers are invalid."""
        UnitFactory.create_batch(5, owner=user)
        
        url = reverse("units:unit-list")
        response = authenticated_client.get(url, {"page": "-1"})
        
        assert response.status_code == 404


@pytest.mark.django_db
class TestOrdering:
    """Test ordering functionality for units list endpoint."""
    
    def test_default_ordering_by_identifier(self, authenticated_client, user):
        """Test that default ordering is by identifier."""
        unit_c = UnitFactory.create(owner=user, identifier="C Unit")
        unit_a = UnitFactory.create(owner=user, identifier="A Unit")
        unit_b = UnitFactory.create(owner=user, identifier="B Unit")
        
        url = reverse("units:unit-list")
        response = authenticated_client.get(url)
        
        assert response.status_code == 200
        results = response.data["results"]
        assert results[0]["id"] == str(unit_a.id)
        assert results[1]["id"] == str(unit_b.id)
        assert results[2]["id"] == str(unit_c.id)
    
    def test_ordering_by_created_at_ascending(self, authenticated_client, user):
        """Test ordering by created_at in ascending order."""
        from datetime import timedelta
        from django.utils import timezone
        
        old = UnitFactory.create(owner=user, identifier="Old")
        old.created_at = timezone.now() - timedelta(days=2)
        old.save()
        
        new = UnitFactory.create(owner=user, identifier="New")
        
        url = reverse("units:unit-list")
        response = authenticated_client.get(url, {"ordering": "created_at"})
        
        assert response.status_code == 200
        results = response.data["results"]
        assert results[0]["id"] == str(old.id)
        assert results[1]["id"] == str(new.id)
    
    def test_ordering_by_created_at_descending(
        self, authenticated_client, user
    ):
        """Test ordering by created_at in descending order."""
        from datetime import timedelta
        from django.utils import timezone
        
        old = UnitFactory.create(owner=user, identifier="Old")
        old.created_at = timezone.now() - timedelta(days=2)
        old.save()
        
        new = UnitFactory.create(owner=user, identifier="New")
        
        url = reverse("units:unit-list")
        response = authenticated_client.get(url, {"ordering": "-created_at"})
        
        assert response.status_code == 200
        results = response.data["results"]
        assert results[0]["id"] == str(new.id)
        assert results[1]["id"] == str(old.id)
    
    def test_ordering_by_identifier_descending(
        self, authenticated_client, user
    ):
        """Test ordering by identifier in descending order."""
        unit_a = UnitFactory.create(owner=user, identifier="A Unit")
        unit_b = UnitFactory.create(owner=user, identifier="B Unit")
        unit_c = UnitFactory.create(owner=user, identifier="C Unit")
        
        url = reverse("units:unit-list")
        response = authenticated_client.get(url, {"ordering": "-identifier"})
        
        assert response.status_code == 200
        results = response.data["results"]
        assert results[0]["id"] == str(unit_c.id)
        assert results[1]["id"] == str(unit_b.id)
        assert results[2]["id"] == str(unit_a.id)
    
    def test_ordering_by_updated_at(self, authenticated_client, user):
        """Test ordering by updated_at."""

        
        unit1 = UnitFactory.create(owner=user)
        unit2 = UnitFactory.create(owner=user)
        
        unit1.description = "Updated"
        unit1.save()
        
        url = reverse("units:unit-list")
        response = authenticated_client.get(url, {"ordering": "-updated_at"})
        
        assert response.status_code == 200
        results = response.data["results"]
        assert results[0]["id"] == str(unit1.id)
    
    def test_ordering_by_is_occupied(self, authenticated_client, user):
        """Test ordering by is_occupied field."""
        vacant = UnitFactory.create(owner=user, is_occupied=False)
        occupied = UnitFactory.create(owner=user, is_occupied=True)
        
        url = reverse("units:unit-list")
        response = authenticated_client.get(url, {"ordering": "-is_occupied"})
        
        assert response.status_code == 200
        results = response.data["results"]
        assert results[0]["is_occupied"] is True
        assert results[1]["is_occupied"] is False
    
    def test_invalid_ordering_field_ignored(self, authenticated_client, user):
        """Test that invalid ordering field is ignored gracefully."""
        UnitFactory.create_batch(2, owner=user)
        
        url = reverse("units:unit-list")
        response = authenticated_client.get(url, {"ordering": "invalid_field"})
        
        assert response.status_code == 200
        assert response.data["count"] == 2
    
    def test_ordering_combined_with_filter(self, authenticated_client, user):
        """Test ordering works with filters."""
        house_b = UnitFactory.create(
            owner=user,
            unit_type=Unit.UnitType.HOUSE,
            identifier="B House"
        )
        house_a = UnitFactory.create(
            owner=user,
            unit_type=Unit.UnitType.HOUSE,
            identifier="A House"
        )
        flat = UnitFactory.create(
            owner=user,
            unit_type=Unit.UnitType.FLAT,
            identifier="Flat"
        )
        
        url = reverse("units:unit-list")
        response = authenticated_client.get(url, {
            "unit_type": Unit.UnitType.HOUSE,
            "ordering": "identifier"
        })
        
        assert response.status_code == 200
        assert response.data["count"] == 2
        results = response.data["results"]
        assert results[0]["id"] == str(house_a.id)
        assert results[1]["id"] == str(house_b.id)