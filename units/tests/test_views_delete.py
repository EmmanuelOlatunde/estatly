# tests/test_views_delete.py
"""
Tests for units app delete endpoints.

Coverage:
- Authentication/authorization for deletion
- Success paths
- Database side effects (hard delete)
- Cross-user access prevention
- Non-existent resource handling
"""

import pytest
from django.urls import reverse
import uuid
from units.models import Unit
from .factories import EstateFactory as estate_factory


@pytest.mark.django_db
class TestUnitDeleteEndpoint:
    """Test DELETE /units/{id}/ endpoint."""
    
    def test_unauthenticated_user_denied(self, api_client, unit):
        """Test that unauthenticated users cannot delete units."""
        url = reverse("units:unit-detail", args=[unit.id])
        response = api_client.delete(url)
        
        assert response.status_code == 401
        assert Unit.objects.filter(id=unit.id).exists()
    
    def test_owner_can_delete_own_unit(self, authenticated_client, unit):
        """Test that owner can delete their own unit."""
        unit_id = unit.id
        url = reverse("units:unit-detail", args=[unit_id])
        
        response = authenticated_client.delete(url)
        
        assert response.status_code == 204
        assert not Unit.objects.filter(id=unit_id).exists()
    
    def test_user_cannot_delete_other_users_unit(
        self, authenticated_client, other_users_unit
    ):
        """Test that user cannot delete another user's unit."""
        url = reverse("units:unit-detail", args=[other_users_unit.id])
        
        response = authenticated_client.delete(url)
        
        assert response.status_code in [403, 404]
        assert Unit.objects.filter(id=other_users_unit.id).exists()
    
    def test_delete_nonexistent_unit_returns_404(self, authenticated_client):
        """Test that deleting non-existent unit returns 404."""
        fake_id = uuid.uuid4()
        url = reverse("units:unit-detail", args=[fake_id])
        
        response = authenticated_client.delete(url)
        
        assert response.status_code == 404
    
    def test_delete_is_hard_delete(self, authenticated_client, unit):
        """Test that delete actually removes unit from database."""
        unit_id = unit.id
        url = reverse("units:unit-detail", args=[unit_id])
        
        authenticated_client.delete(url)
        
        assert not Unit.objects.filter(id=unit_id).exists()
        assert Unit.objects.all().count() == 0
    
    def test_delete_response_has_no_content(self, authenticated_client, unit):
        """Test that delete returns 204 with no content."""
        url = reverse("units:unit-detail", args=[unit.id])
        
        response = authenticated_client.delete(url)
        
        assert response.status_code == 204
        assert not response.data
    
    def test_jwt_authentication_works(self, jwt_client, user): 
        """Test that JWT authentication works for delete."""
        estate = estate_factory()
        unit = Unit.objects.create(
            owner=user,
            estate=estate,  
            identifier="Test",
            unit_type=Unit.UnitType.HOUSE
        )
        unit_id = unit.id
        url = reverse("units:unit-detail", args=[unit_id])
        
        response = jwt_client.delete(url)
        
        assert response.status_code == 204
        assert not Unit.objects.filter(id=unit_id).exists()
    
    def test_admin_cannot_delete_other_users_unit(
        self, admin_client, other_users_unit
    ):
        """Test that admin cannot delete other users' units."""
        url = reverse("units:unit-detail", args=[other_users_unit.id])
        
        response = admin_client.delete(url)
        
        assert response.status_code in [403, 404]
        assert Unit.objects.filter(id=other_users_unit.id).exists()
    
    def test_cannot_retrieve_deleted_unit(
        self, authenticated_client, unit
    ):
        """Test that deleted unit cannot be retrieved."""
        unit_id = unit.id
        url = reverse("units:unit-detail", args=[unit_id])
        
        authenticated_client.delete(url)
        
        response = authenticated_client.get(url)
        assert response.status_code == 404
    
    def test_delete_does_not_affect_other_units(
        self, authenticated_client, user
    ):
        """Test that deleting one unit doesn't affect others."""
        estate = estate_factory()
        unit1 = Unit.objects.create(
            owner=user,
            estate=estate,  # ADD THIS
            identifier="Unit 1",
            unit_type=Unit.UnitType.HOUSE
        )
        unit2 = Unit.objects.create(
            owner=user,
            estate=estate,
            identifier="Unit 2",
            unit_type=Unit.UnitType.FLAT
        )
        
        url = reverse("units:unit-detail", args=[unit1.id])
        authenticated_client.delete(url)
        
        assert not Unit.objects.filter(id=unit1.id).exists()
        assert Unit.objects.filter(id=unit2.id).exists()