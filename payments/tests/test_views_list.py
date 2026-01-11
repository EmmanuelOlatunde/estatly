# tests/test_views_list.py

"""
Tests for payments app list/search endpoints.

Coverage:
- Authentication/authorization
- List endpoints return correct data
- Empty result sets
- Pagination
- Search functionality
"""

import pytest
from django.urls import reverse
from .helpers import (
    assert_pagination_response,
    assert_fee_response_structure,
    assert_fee_assignment_response_structure,
    assert_payment_response_structure,
    assert_receipt_response_structure,
)
from .factories import (
    FeeFactory,
    FeeAssignmentFactory,
    PaymentFactory,
    ReceiptFactory,
)


@pytest.mark.django_db
class TestFeeListEndpoint:
    """Test GET /fees/ endpoint."""
    
    def test_unauthenticated_access_denied(self, api_client):
        """Test unauthenticated users cannot list fees."""
        url = reverse("fee-list")
        response = api_client.get(url)
        
        assert response.status_code == 401
    
    def test_authenticated_user_can_list_fees(self, authenticated_client, fee):
        """Test authenticated user can list fees."""
        url = reverse("fee-list")
        response = authenticated_client.get(url)
        
        assert response.status_code == 200
        assert_pagination_response(response.data)
        assert len(response.data["results"]) >= 1
    
    def test_empty_fee_list_returns_empty_array(self, authenticated_client):
        """Test listing fees when none exist returns empty results."""
        url = reverse("fee-list")
        response = authenticated_client.get(url)
        
        assert response.status_code == 200
        assert response.data["results"] == []
        assert response.data["count"] == 0
    
    def test_fee_list_response_structure(self, authenticated_client, fee):
        """Test fee list returns correct response structure."""
        url = reverse("fee-list")
        response = authenticated_client.get(url)
        
        assert response.status_code == 200
        assert len(response.data["results"]) > 0
        assert_fee_response_structure(response.data["results"][0])
    
    def test_multiple_fees_returned(self, authenticated_client, estate, user):
        """Test listing multiple fees."""
        fees = [FeeFactory.create(estate=estate, created_by=user) for _ in range(3)]
        
        url = reverse("fee-list")
        response = authenticated_client.get(url)
        
        assert response.status_code == 200
        assert len(response.data["results"]) == 3
    
    def test_fees_ordered_by_created_at_desc(self, authenticated_client, estate, user):
        """Test fees are ordered by creation date (newest first)."""
        fee1 = FeeFactory.create(estate=estate, created_by=user, name="First")
        fee2 = FeeFactory.create(estate=estate, created_by=user, name="Second")
        
        url = reverse("fee-list")
        response = authenticated_client.get(url)
        
        assert response.status_code == 200
        results = response.data["results"]
        assert results[0]["id"] == str(fee2.id)
        assert results[1]["id"] == str(fee1.id)
    
    def test_search_fees_by_name(self, authenticated_client, estate, user):
        """Test searching fees by name."""
        FeeFactory.create(estate=estate, created_by=user, name="Security Levy")
        FeeFactory.create(estate=estate, created_by=user, name="Water Bill")
        
        url = reverse("fee-list")
        response = authenticated_client.get(url, {"search": "Security"})
        
        assert response.status_code == 200
        assert len(response.data["results"]) == 1
        assert "Security" in response.data["results"][0]["name"]


@pytest.mark.django_db
class TestFeeAssignmentListEndpoint:
    """Test GET /assignments/ endpoint."""
    
    def test_unauthenticated_access_denied(self, api_client):
        """Test unauthenticated users cannot list assignments."""
        url = reverse("fee-assignment-list")
        response = api_client.get(url)
        
        assert response.status_code == 401
    
    def test_authenticated_user_can_list_assignments(
        self, authenticated_client, fee_assignment
    ):
        """Test authenticated user can list fee assignments."""
        url = reverse("fee-assignment-list")
        response = authenticated_client.get(url)
        
        assert response.status_code == 200
        assert_pagination_response(response.data)
        assert len(response.data["results"]) >= 1
    
    def test_empty_assignment_list(self, authenticated_client):
        """Test listing assignments when none exist."""
        url = reverse("fee-assignment-list")
        response = authenticated_client.get(url)
        
        assert response.status_code == 200
        assert response.data["results"] == []
    
    def test_assignment_response_structure(self, authenticated_client, fee_assignment):
        """Test assignment list returns correct structure."""
        url = reverse("fee-assignment-list")
        response = authenticated_client.get(url)
        
        assert response.status_code == 200
        assert_fee_assignment_response_structure(response.data["results"][0])
    
    def test_multiple_assignments_returned(
        self, authenticated_client, fee, units
    ):
        """Test listing multiple assignments."""
        for unit in units:
            FeeAssignmentFactory.create(fee=fee, unit=unit)
        
        url = reverse("fee-assignment-list")
        response = authenticated_client.get(url)
        
        assert response.status_code == 200
        assert len(response.data["results"]) == len(units)


@pytest.mark.django_db
class TestPaymentListEndpoint:
    """Test GET /payments/ endpoint."""
    
    def test_unauthenticated_access_denied(self, api_client):
        """Test unauthenticated users cannot list payments."""
        url = reverse("payment-list")
        response = api_client.get(url)
        
        assert response.status_code == 401
    
    def test_regular_user_access_denied(self, regular_user_client):
        """Test regular users cannot list payments."""
        url = reverse("payment-list")
        response = regular_user_client.get(url)
        
        assert response.status_code == 403
    
    def test_estate_manager_can_list_payments(
        self, authenticated_client, payment
    ):
        """Test estate manager can list payments."""
        url = reverse("payment-list")
        response = authenticated_client.get(url)
        
        assert response.status_code == 200
        assert_pagination_response(response.data)
    
    def test_empty_payment_list(self, authenticated_client):
        """Test listing payments when none exist."""
        url = reverse("payment-list")
        response = authenticated_client.get(url)
        
        assert response.status_code == 200
        assert response.data["results"] == []
    
    def test_payment_response_structure(self, authenticated_client, payment):
        """Test payment list returns correct structure."""
        url = reverse("payment-list")
        response = authenticated_client.get(url)
        
        assert response.status_code == 200
        assert_payment_response_structure(response.data["results"][0])
    
    def test_payments_ordered_by_payment_date_desc(
        self, authenticated_client, fee_assignment, user
    ):
        """Test payments are ordered by payment date (newest first)."""
        payment1 = PaymentFactory.create(
            fee_assignment=fee_assignment, recorded_by=user
        )
        payment2 = PaymentFactory.create(
            fee_assignment=FeeAssignmentFactory.create(), recorded_by=user
        )
        
        url = reverse("payment-list")
        response = authenticated_client.get(url)
        
        assert response.status_code == 200
        assert len(response.data["results"]) >= 2
    
    def test_search_payments_by_reference(
        self, authenticated_client, fee_assignment, user
    ):
        """Test searching payments by reference number."""
        PaymentFactory.create(
            fee_assignment=fee_assignment,
            recorded_by=user,
            reference_number="REF123"
        )
        
        url = reverse("payment-list")
        response = authenticated_client.get(url, {"search": "REF123"})
        
        assert response.status_code == 200
        assert len(response.data["results"]) == 1
        assert "REF123" in response.data["results"][0]["reference_number"]


@pytest.mark.django_db
class TestReceiptListEndpoint:
    """Test GET /receipts/ endpoint."""
    
    def test_unauthenticated_access_denied(self, api_client):
        """Test unauthenticated users cannot list receipts."""
        url = reverse("receipt-list")
        response = api_client.get(url)
        
        assert response.status_code == 401
    
    def test_authenticated_user_can_list_receipts(
        self, authenticated_client, receipt
    ):
        """Test authenticated user can list receipts."""
        url = reverse("receipt-list")
        response = authenticated_client.get(url)
        
        assert response.status_code == 200
        assert_pagination_response(response.data)
    
    def test_empty_receipt_list(self, authenticated_client):
        """Test listing receipts when none exist."""
        url = reverse("receipt-list")
        response = authenticated_client.get(url)
        
        assert response.status_code == 200
        assert response.data["results"] == []
    
    def test_receipt_response_structure(self, authenticated_client, receipt):
        """Test receipt list returns correct structure."""
        url = reverse("receipt-list")
        response = authenticated_client.get(url)
        
        assert response.status_code == 200
        assert_receipt_response_structure(response.data["results"][0])
    
    def test_receipts_ordered_by_issued_date_desc(
        self, authenticated_client, payment
    ):
        """Test receipts are ordered by issue date (newest first)."""
        receipt1 = ReceiptFactory.create(payment=payment)
        receipt2 = ReceiptFactory.create(
            payment=PaymentFactory.create()
        )
        
        url = reverse("receipt-list")
        response = authenticated_client.get(url)
        
        assert response.status_code == 200
        assert len(response.data["results"]) >= 2
    
    def test_search_receipts_by_number(self, authenticated_client, receipt):
        """Test searching receipts by receipt number."""
        url = reverse("receipt-list")
        response = authenticated_client.get(url, {"search": receipt.receipt_number})
        
        assert response.status_code == 200
        assert len(response.data["results"]) == 1
        assert response.data["results"][0]["receipt_number"] == receipt.receipt_number