# tests/test_views_update.py

"""
Tests for payments app update/PATCH/PUT endpoints.

Coverage:
- Authentication/authorization for updates
- Successful updates modify database
- Invalid data returns 400
- Read-only resources cannot be updated
"""

import pytest
from datetime import timedelta
from django.urls import reverse
from django.utils import timezone
from payments.models import Fee


@pytest.mark.django_db
class TestFeeUpdateEndpoint:
    """Test PATCH/PUT /fees/{id}/ endpoint."""
    
    def test_unauthenticated_access_denied(self, api_client, fee):
        """Test unauthenticated users cannot update fees."""
        url = reverse("fee-detail", args=[fee.id])
        data = {"name": "Updated Name"}
        response = api_client.patch(url, data, format="json")
        
        assert response.status_code == 401
    
    def test_regular_user_cannot_update_fee(self, regular_user_client, fee):
        """Test regular users cannot update fees."""
        url = reverse("fee-detail", args=[fee.id])
        data = {"name": "Updated Name"}
        response = regular_user_client.patch(url, data, format="json")
        
        assert response.status_code == 403
    
    def test_estate_manager_can_update_fee(self, authenticated_client, fee):
        """Test estate manager can update fee."""
        url = reverse("fee-detail", args=[fee.id])
        data = {
            "name": "Updated Fee Name",
            "description": "Updated description",
        }
        
        response = authenticated_client.patch(url, data, format="json")
        
        assert response.status_code == 200
        assert response.data["name"] == "Updated Fee Name"
        assert response.data["description"] == "Updated description"
        
        fee.refresh_from_db()
        assert fee.name == "Updated Fee Name"
        assert fee.description == "Updated description"
    
    def test_update_fee_amount(self, authenticated_client, fee):
        """Test updating fee amount."""
        url = reverse("fee-detail", args=[fee.id])
        data = {"amount": "7500.00"}
        
        response = authenticated_client.patch(url, data, format="json")
        
        assert response.status_code == 200
        assert response.data["amount"] == "7500.00"
        
        fee.refresh_from_db()
        assert str(fee.amount) == "7500.00"
    
    def test_update_fee_due_date(self, authenticated_client, fee):
        """Test updating fee due date."""
        new_due_date = (timezone.now() + timedelta(days=60)).date()
        url = reverse("fee-detail", args=[fee.id])
        data = {"due_date": new_due_date.isoformat()}
        
        response = authenticated_client.patch(url, data, format="json")
        
        assert response.status_code == 200
        
        fee.refresh_from_db()
        assert fee.due_date == new_due_date
    
    def test_update_fee_past_due_date_rejected(self, authenticated_client, fee):
        """Test updating fee to past due date is rejected."""
        url = reverse("fee-detail", args=[fee.id])
        data = {"due_date": (timezone.now() - timedelta(days=1)).date().isoformat()}
        
        response = authenticated_client.patch(url, data, format="json")
        
        assert response.status_code == 400
        assert "due_date" in response.data
    
    def test_update_fee_negative_amount_rejected(self, authenticated_client, fee):
        """Test updating fee to negative amount is rejected."""
        url = reverse("fee-detail", args=[fee.id])
        data = {"amount": "-1000.00"}
        
        response = authenticated_client.patch(url, data, format="json")
        
        assert response.status_code == 400
        assert "amount" in response.data
    
    def test_full_update_with_put(self, authenticated_client, fee, estate):
        """Test full update using PUT method."""
        url = reverse("fee-detail", args=[fee.id])
        data = {
            "name": "Completely New Fee",
            "description": "New description",
            "amount": "12000.00",
            "due_date": (timezone.now() + timedelta(days=45)).date().isoformat(),
            "estate": str(estate.id),
        }
        
        response = authenticated_client.put(url, data, format="json")
        
        assert response.status_code == 200
        assert response.data["name"] == "Completely New Fee"
        assert response.data["amount"] == "12000.00"


@pytest.mark.django_db
class TestFeeAssignmentUpdateNotAllowed:
    """Test FeeAssignment endpoints do not allow updates."""
    
    def test_fee_assignment_update_not_allowed(
        self, authenticated_client, fee_assignment
    ):
        """Test fee assignments cannot be updated via API."""
        url = reverse("fee-assignment-detail", args=[fee_assignment.id])
        data = {"status": "paid"}
        response = authenticated_client.patch(url, data, format="json")
        
        assert response.status_code == 405


@pytest.mark.django_db
class TestPaymentUpdateNotAllowed:
    """Test Payment endpoints do not allow updates."""
    
    def test_payment_update_not_allowed(self, authenticated_client, payment):
        """Test payments cannot be updated after creation."""
        url = reverse("payment-detail", args=[payment.id])
        data = {"amount": "999.00"}
        response = authenticated_client.patch(url, data, format="json")
        
        assert response.status_code == 405
    
    def test_payment_put_not_allowed(self, authenticated_client, payment):
        """Test payments cannot be replaced using PUT."""
        url = reverse("payment-detail", args=[payment.id])
        data = {
            "fee_assignment": str(payment.fee_assignment.id),
            "amount": "999.00",
            "payment_method": "cash",
        }
        response = authenticated_client.put(url, data, format="json")
        
        assert response.status_code == 405


@pytest.mark.django_db
class TestReceiptUpdateNotAllowed:
    """Test Receipt endpoints do not allow updates."""
    
    def test_receipt_update_not_allowed(self, authenticated_client, receipt):
        """Test receipts cannot be updated."""
        url = reverse("receipt-detail", args=[receipt.id])
        data = {"amount": "999.00"}
        response = authenticated_client.patch(url, data, format="json")
        
        assert response.status_code == 405
    
    def test_receipt_put_not_allowed(self, authenticated_client, receipt):
        """Test receipts cannot be replaced using PUT."""
        url = reverse("receipt-detail", args=[receipt.id])
        data = {"receipt_number": "MODIFIED"}
        response = authenticated_client.put(url, data, format="json")
        
        assert response.status_code == 405