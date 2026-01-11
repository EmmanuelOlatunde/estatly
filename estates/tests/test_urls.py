
# tests/test_urls.py
"""
Tests for estates app URL routing.

Coverage:
- URL pattern resolution
- Reverse URL generation
- Router registration
"""

import pytest
from django.urls import reverse, resolve
from estates.views import EstateViewSet


@pytest.mark.django_db
class TestEstateURLs:
    """Test URL routing for Estate endpoints."""
    
    def test_estate_list_url_resolves(self):
        """Test estate list URL resolves to correct view."""
        url = reverse("estates:estates-list")
        assert url == "/api/estates/"
        resolver = resolve(url)
        assert resolver.func.cls == EstateViewSet
    
    def test_estate_detail_url_resolves(self, estate):
        """Test estate detail URL resolves correctly."""
        url = reverse("estates:estates-detail", args=[estate.id])
        assert url == f"/api/estates/{estate.id}/"
        resolver = resolve(url)
        assert resolver.func.cls == EstateViewSet
    
    def test_estate_activate_url_resolves(self, estate):
        """Test estate activate URL resolves correctly."""
        url = reverse("estates:estates-activate", args=[estate.id])
        assert url == f"/api/estates/{estate.id}/activate/"
        resolver = resolve(url)
        assert resolver.func.cls == EstateViewSet
    
    def test_estate_deactivate_url_resolves(self, estate):
        """Test estate deactivate URL resolves correctly."""
        url = reverse("estates:estates-deactivate", args=[estate.id])
        assert url == f"/api/estates/{estate.id}/deactivate/"
        resolver = resolve(url)
        assert resolver.func.cls == EstateViewSet
    
    def test_estate_statistics_url_resolves(self):
        """Test estate statistics URL resolves correctly."""
        url = reverse("estates:estates-statistics")
        assert url == "/api/estates/statistics/"
        resolver = resolve(url)
        assert resolver.func.cls == EstateViewSet
    
    def test_estate_by_type_url_resolves(self):
        """Test estate by-type URL resolves correctly."""
        url = reverse("estates:estates-by-type", args=["PRIVATE"])
        assert url == "/api/estates/by-type/PRIVATE/"
        resolver = resolve(url)
        assert resolver.func.cls == EstateViewSet
