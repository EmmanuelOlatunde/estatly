# tests/test_urls.py
"""
Tests for units app URL routing and reversing.

Coverage:
- URL pattern matching
- reverse() functionality for all endpoints
- Router registration
"""

import pytest
from django.urls import reverse, resolve
from units.views import UnitViewSet


@pytest.mark.django_db
class TestUnitURLs:
    """Test URL routing for unit endpoints."""
    
    def test_unit_list_url_resolves(self):
        """Test that unit-list URL resolves correctly."""
        url = reverse("units:unit-list")
        assert url == "/api/units/"
        resolver = resolve(url)
        assert resolver.func.cls == UnitViewSet
    
    def test_unit_detail_url_resolves(self):
        """Test that unit-detail URL resolves correctly."""
        unit_id = "123e4567-e89b-12d3-a456-426614174000"
        url = reverse("units:unit-detail", args=[unit_id])
        assert url == f"/api/units/{unit_id}/"
        resolver = resolve(url)
        assert resolver.func.cls == UnitViewSet
    
    def test_unit_occupied_url_resolves(self):
        """Test that occupied units URL resolves correctly."""
        url = reverse("units:unit-occupied")
        assert url == "/api/units/occupied/"
        resolver = resolve(url)
        assert resolver.func.cls == UnitViewSet
    
    def test_unit_vacant_url_resolves(self):
        """Test that vacant units URL resolves correctly."""
        url = reverse("units:unit-vacant")
        assert url == "/api/units/vacant/"
        resolver = resolve(url)
        assert resolver.func.cls == UnitViewSet
    
    def test_unit_deactivate_url_resolves(self):
        """Test that deactivate unit URL resolves correctly."""
        unit_id = "123e4567-e89b-12d3-a456-426614174000"
        url = reverse("units:unit-deactivate", args=[unit_id])
        assert url == f"/api/units/{unit_id}/deactivate/"
        resolver = resolve(url)
        assert resolver.func.cls == UnitViewSet
    
    def test_unit_activate_url_resolves(self):
        """Test that activate unit URL resolves correctly."""
        unit_id = "123e4567-e89b-12d3-a456-426614174000"
        url = reverse("units:unit-activate", args=[unit_id])
        assert url == f"/api/units/{unit_id}/activate/"
        resolver = resolve(url)
        assert resolver.func.cls == UnitViewSet
    
    def test_unit_update_occupancy_url_resolves(self):
        """Test that update occupancy URL resolves correctly."""
        unit_id = "123e4567-e89b-12d3-a456-426614174000"
        url = reverse("units:unit-update-occupancy", args=[unit_id])
        assert url == f"/api/units/{unit_id}/update_occupancy/"
        resolver = resolve(url)
        assert resolver.func.cls == UnitViewSet