# tests/test_views_retrieve.py

"""
Tests for payments app detail/retrieve endpoints.

Coverage:
- Authentication/authorization
- Retrieving individual resources
- 404 for non-existent resources
- Object-level permissions
"""

import pytest
import uuid
from decimal import Decimal
from django.urls import reverse
from .helpers import (
    assert_fee_response_structure,
    assert_fee_assignment_response_structure,
    assert_payment_response_structure,
    assert_receipt_response_structure,
)


@pytest.mark.django_db
class TestFeeRetrieveEndpoint:
    """Test GET /fees/{id}/ endpoint."""
    
    def test_unauthenticated_access_denied(self, api_client, fee):
        """Test unauthenticated users cannot retrieve fee."""
        url = reverse("fee-detail", args=[fee.id])
        response = api_client.get(url)
        
        assert response.status_code == 401
    
    def test_authenticated_user_can_retrieve_fee(self, authenticated_client, fee):
        """Test authenticated user can retrieve fee details."""
        url = reverse("fee-detail", args=[fee.id])
        response = authenticated_client.get(url)
        
        assert response.status_code == 200
        assert response.data["id"] == str(fee.id)
        assert response.data["name"] == fee.name
        assert Decimal(response.data["amount"]) == fee.amount
    
    def test_fee_detail_includes_assignments(
        self, authenticated_client, fee_with_assignments
    ):
        """Test fee detail includes related assignments."""
        url = reverse("fee-detail", args=[fee_with_assignments.id])
        response = authenticated_client.get(url)
        
        assert response.status_code == 200
        assert "assignments" in response.data
        assert len(response.data["assignments"]) == 5
    
    def test_nonexistent_fee_returns_404(self, authenticated_client):
        """Test retrieving non-existent fee returns 404."""
        fake_id = uuid.uuid4()
        url = reverse("fee-detail", args=[fake_id])
        response = authenticated_client.get(url)
        
        assert response.status_code == 404
    
    def test_invalid_uuid_returns_404(self, authenticated_client):
        """Test invalid UUID format returns 404."""
        url = reverse("fee-detail", args=["invalid-uuid"])
        response = authenticated_client.get(url)
        
        assert response.status_code == 404
    
    def test_fee_detail_response_structure(self, authenticated_client, fee):
        """Test fee detail returns correct structure."""
        url = reverse("fee-detail", args=[fee.id])
        response = authenticated_client.get(url)
        
        assert response.status_code == 200
        assert "assignments" in response.data


@pytest.mark.django_db
class TestFeeAssignmentRetrieveEndpoint:
    """Test GET /assignments/{id}/ endpoint."""
    
    def test_unauthenticated_access_denied(self, api_client, fee_assignment):
        """Test unauthenticated users cannot retrieve assignment."""
        url = reverse("fee-assignment-detail", args=[fee_assignment.id])
        response = api_client.get(url)
        
        assert response.status_code == 401
    
    def test_authenticated_user_can_retrieve_assignment(
        self, authenticated_client, fee_assignment
    ):
        """Test authenticated user can retrieve assignment details."""
        url = reverse("fee-assignment-detail", args=[fee_assignment.id])
        response = authenticated_client.get(url)
        
        assert response.status_code == 200
        assert response.data["id"] == str(fee_assignment.id)
        assert response.data["status"] == fee_assignment.status
    
    def test_nonexistent_assignment_returns_404(self, authenticated_client):
        """Test retrieving non-existent assignment returns 404."""
        fake_id = uuid.uuid4()
        url = reverse("fee-assignment-detail", args=[fake_id])
        response = authenticated_client.get(url)
        
        assert response.status_code == 404
    
    def test_assignment_detail_response_structure(
        self, authenticated_client, fee_assignment
    ):
        """Test assignment detail returns correct structure."""
        url = reverse("fee-assignment-detail", args=[fee_assignment.id])
        response = authenticated_client.get(url)
        
        assert response.status_code == 200
        assert_fee_assignment_response_structure(response.data)


@pytest.mark.django_db
class TestPaymentRetrieveEndpoint:
    """Test GET /payments/{id}/ endpoint."""
    
    def test_unauthenticated_access_denied(self, api_client, payment):
        """Test unauthenticated users cannot retrieve payment."""
        url = reverse("payment-detail", args=[payment.id])
        response = api_client.get(url)
        
        assert response.status_code == 401
    
    def test_regular_user_access_denied(self, regular_user_client, payment):
        """Test regular users cannot retrieve payment."""
        url = reverse("payment-detail", args=[payment.id])
        response = regular_user_client.get(url)
        
        assert response.status_code == 403
    
    def test_estate_manager_can_retrieve_payment(
        self, authenticated_client, payment
    ):
        """Test estate manager can retrieve payment details."""
        url = reverse("payment-detail", args=[payment.id])
        response = authenticated_client.get(url)
        
        assert response.status_code == 200
        assert response.data["id"] == str(payment.id)
        assert Decimal(response.data["amount"]) == payment.amount
    
    def test_nonexistent_payment_returns_404(self, authenticated_client):
        """Test retrieving non-existent payment returns 404."""
        fake_id = uuid.uuid4()
        url = reverse("payment-detail", args=[fake_id])
        response = authenticated_client.get(url)
        
        assert response.status_code == 404
    
    def test_payment_detail_response_structure(
        self, authenticated_client, payment
    ):
        """Test payment detail returns correct structure."""
        url = reverse("payment-detail", args=[payment.id])
        response = authenticated_client.get(url)
        
        assert response.status_code == 200
        assert_payment_response_structure(response.data)


@pytest.mark.django_db
class TestReceiptRetrieveEndpoint:
    """Test GET /receipts/{id}/ endpoint."""
    
    def test_unauthenticated_access_denied(self, api_client, receipt):
        """Test unauthenticated users cannot retrieve receipt."""
        url = reverse("receipt-detail", args=[receipt.id])
        response = api_client.get(url)
        
        assert response.status_code == 401
    
    def test_authenticated_user_can_retrieve_receipt(
        self, authenticated_client, receipt
    ):
        """Test authenticated user can retrieve receipt details."""
        url = reverse("receipt-detail", args=[receipt.id])
        response = authenticated_client.get(url)
        
        assert response.status_code == 200
        assert response.data["id"] == str(receipt.id)
        assert response.data["receipt_number"] == receipt.receipt_number
    
    def test_nonexistent_receipt_returns_404(self, authenticated_client):
        """Test retrieving non-existent receipt returns 404."""
        fake_id = uuid.uuid4()
        url = reverse("receipt-detail", args=[fake_id])
        response = authenticated_client.get(url)
        
        assert response.status_code == 404
    
    def test_receipt_detail_response_structure(
        self, authenticated_client, receipt
    ):
        """Test receipt detail returns correct structure."""
        url = reverse("receipt-detail", args=[receipt.id])
        response = authenticated_client.get(url)
        
        assert response.status_code == 200
        assert_receipt_response_structure(response.data)
    
    def test_receipt_contains_all_payment_info(self, authenticated_client, receipt):
        """Test receipt contains all necessary payment information."""
        url = reverse("receipt-detail", args=[receipt.id])
        response = authenticated_client.get(url)

        assert response.status_code == 200
        data = response.data
        assert data["estate_name"] == receipt.estate_name
        assert data["unit_identifier"] == receipt.unit_identifier
        assert data["fee_name"] == receipt.fee_name
        
        # ← Compare as Decimal, not string
        assert Decimal(data["amount"]) == receipt.amount