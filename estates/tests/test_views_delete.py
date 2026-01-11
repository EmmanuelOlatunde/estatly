
# tests/test_views_delete.py
"""
Tests for estate delete endpoint.

Coverage:
- Authentication/authorization
- Success paths
- Error cases
- Database effects
"""

import pytest
from .helpers import get_estate_detail_url
from estates.models import Estate


@pytest.mark.django_db
class TestEstateDeleteEndpoint:
    """Test estate delete endpoint DELETE /estates/{id}/."""
    
    def test_unauthenticated_user_cannot_delete_estate(self, api_client, estate):
        """Test unauthenticated users cannot delete estates."""
        url = get_estate_detail_url(estate.id)
        
        response = api_client.delete(url)
        assert response.status_code == 401
    
    def test_non_staff_user_cannot_delete_estate(self, authenticated_client, estate):
        """Test non-staff users cannot delete estates."""
        url = get_estate_detail_url(estate.id)
        
        response = authenticated_client.delete(url)
        assert response.status_code == 403
    
    def test_staff_user_can_delete_estate(self, staff_client, estate):
        """Test staff users can delete estates."""
        url = get_estate_detail_url(estate.id)
        
        response = staff_client.delete(url)
        assert response.status_code == 204
    
    def test_admin_user_can_delete_estate(self, admin_client, estate):
        """Test admin users can delete estates."""
        url = get_estate_detail_url(estate.id)
        
        response = admin_client.delete(url)
        assert response.status_code == 204
    
    def test_delete_removes_from_database(self, staff_client, estate):
        """Test delete actually removes estate from database."""
        estate_id = estate.id
        url = get_estate_detail_url(estate_id)
        
        response = staff_client.delete(url)
        
        assert response.status_code == 204
        assert not Estate.objects.filter(id=estate_id).exists()
    
    def test_delete_nonexistent_estate_returns_404(self, staff_client):
        """Test deleting non-existent estate returns 404."""
        import uuid
        fake_id = uuid.uuid4()
        url = get_estate_detail_url(fake_id)
        
        response = staff_client.delete(url)
        assert response.status_code == 404
    
    def test_delete_already_deleted_estate_returns_404(self, staff_client, estate):
        """Test deleting already deleted estate returns 404."""
        url = get_estate_detail_url(estate.id)
        
        first_response = staff_client.delete(url)
        assert first_response.status_code == 204
        
        second_response = staff_client.delete(url)
        assert second_response.status_code == 404