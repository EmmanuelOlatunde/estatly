# tests/test_views_delete.py

"""
Tests for payments app delete/DELETE endpoints.

Coverage:
- Authentication/authorization for deletion
- Successful deletion removes from database
- Deletion constraints (cannot delete paid fees)
- 404 for non-existent resources
"""

import pytest
from django.urls import reverse
from payments.models import Fee, FeeAssignment, Payment, Receipt


@pytest.mark.django_db
class TestFeeDeleteEndpoint:
    """Test DELETE /fees/{id}/ endpoint."""
    
    def test_unauthenticated_access_denied(self, api_client, fee):
        """Test unauthenticated users cannot delete fees."""
        url = reverse("fee-detail", args=[fee.id])
        response = api_client.delete(url)
        
        assert response.status_code == 401
        assert Fee.objects.filter(id=fee.id).exists()
    
    def test_regular_user_cannot_delete_fee(self, regular_user_client, fee):
        """Test regular users cannot delete fees."""
        url = reverse("fee-detail", args=[fee.id])
        response = regular_user_client.delete(url)
        
        assert response.status_code == 403
        assert Fee.objects.filter(id=fee.id).exists()
    
    def test_estate_manager_can_delete_fee(self, authenticated_client, fee):
        """Test estate manager can delete fee."""
        fee_id = fee.id
        url = reverse("fee-detail", args=[fee_id])
        
        response = authenticated_client.delete(url)
        
        assert response.status_code == 204
        assert not Fee.objects.filter(id=fee_id).exists()
    
    def test_delete_fee_deletes_unpaid_assignments(
        self, authenticated_client, fee_with_assignments
    ):
        """Test deleting fee also deletes its unpaid assignments."""
        fee_id = fee_with_assignments.id
        assignment_ids = list(
            fee_with_assignments.fee_assignments.values_list('id', flat=True)
        )
        
        url = reverse("fee-detail", args=[fee_id])
        response = authenticated_client.delete(url)
        
        assert response.status_code == 204
        assert not Fee.objects.filter(id=fee_id).exists()
        assert not FeeAssignment.objects.filter(id__in=assignment_ids).exists()
    
    def test_delete_nonexistent_fee_returns_404(self, authenticated_client):
        """Test deleting non-existent fee returns 404."""
        import uuid
        fake_id = uuid.uuid4()
        url = reverse("fee-detail", args=[fake_id])
        
        response = authenticated_client.delete(url)
        
        assert response.status_code == 404


@pytest.mark.django_db
class TestFeeAssignmentDeleteNotAllowed:
    """Test FeeAssignment cannot be deleted via API."""
    
    def test_fee_assignment_delete_not_allowed(
        self, authenticated_client, fee_assignment
    ):
        """Test fee assignments cannot be deleted via API."""
        url = reverse("fee-assignment-detail", args=[fee_assignment.id])
        response = authenticated_client.delete(url)
        
        assert response.status_code == 405
        assert FeeAssignment.objects.filter(id=fee_assignment.id).exists()


@pytest.mark.django_db
class TestPaymentDeleteNotAllowed:
    """Test Payment cannot be deleted via API."""
    
    def test_payment_delete_not_allowed(self, authenticated_client, payment):
        """Test payments cannot be deleted via API."""
        url = reverse("payment-detail", args=[payment.id])
        response = authenticated_client.delete(url)
        
        assert response.status_code == 405
        assert Payment.objects.filter(id=payment.id).exists()
    
    def test_admin_also_cannot_delete_payment(self, admin_client, payment):
        """Test even admins cannot delete payments via API."""
        url = reverse("payment-detail", args=[payment.id])
        response = admin_client.delete(url)
        
        assert response.status_code == 405
        assert Payment.objects.filter(id=payment.id).exists()


@pytest.mark.django_db
class TestReceiptDeleteNotAllowed:
    """Test Receipt cannot be deleted via API."""
    
    def test_receipt_delete_not_allowed(self, authenticated_client, receipt):
        """Test receipts cannot be deleted via API."""
        url = reverse("receipt-detail", args=[receipt.id])
        response = authenticated_client.delete(url)
        
        assert response.status_code == 405
        assert Receipt.objects.filter(id=receipt.id).exists()
    
    def test_admin_also_cannot_delete_receipt(self, admin_client, receipt):
        """Test even admins cannot delete receipts via API."""
        url = reverse("receipt-detail", args=[receipt.id])
        response = admin_client.delete(url)
        
        assert response.status_code == 405
        assert Receipt.objects.filter(id=receipt.id).exists()