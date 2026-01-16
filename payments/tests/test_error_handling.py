# tests/test_error_handling.py

"""
Tests for error responses and exception handling.

Coverage:
- 400 Bad Request errors
- 404 Not Found errors
- 405 Method Not Allowed errors
- Validation error formats
- Malformed requests
"""

import pytest
import json
from django.urls import reverse
from datetime import timedelta
from django.utils import timezone


@pytest.mark.django_db
class TestFeeErrorHandling:
    """Test error handling for fee endpoints."""
    
    def test_create_fee_with_malformed_json(self, authenticated_client):
        """Test malformed JSON returns 400."""
        url = reverse("fee-list")
        response = authenticated_client.post(
            url,
            data="{'invalid': json}",
            content_type="application/json"
        )
        
        assert response.status_code == 400
    
    def test_create_fee_with_invalid_uuid_estate(
        self, authenticated_client
    ):
        """Test invalid estate UUID returns 400."""
        url = reverse("fee-list")
        data = {
            "name": "Test Fee",
            "amount": "5000.00",
            "due_date": (timezone.now() + timedelta(days=30)).date().isoformat(),
            "estate": "invalid-uuid",
            "assign_to_all_units": True,
        }
        
        response = authenticated_client.post(url, data, format="json")
        
        assert response.status_code == 400
        assert "estate" in response.data
    
    def test_create_fee_with_nonexistent_estate(
        self, authenticated_client
    ):
        """Test non-existent estate UUID returns 400."""
        import uuid
        url = reverse("fee-list")
        data = {
            "name": "Test Fee",
            "amount": "5000.00",
            "due_date": (timezone.now() + timedelta(days=30)).date().isoformat(),
            "estate": str(uuid.uuid4()),
            "assign_to_all_units": True,
        }
        
        response = authenticated_client.post(url, data, format="json")
        
        assert response.status_code == 400
    
    def test_create_fee_with_string_amount(self, authenticated_client, estate):
        """Test invalid amount type returns 400."""
        url = reverse("fee-list")
        data = {
            "name": "Test Fee",
            "amount": "not-a-number",
            "due_date": (timezone.now() + timedelta(days=30)).date().isoformat(),
            "estate": str(estate.id),
            "assign_to_all_units": True,
        }
        
        response = authenticated_client.post(url, data, format="json")
        
        assert response.status_code == 400
        assert "amount" in response.data
    
    def test_create_fee_with_invalid_date_format(
        self, authenticated_client, estate
    ):
        """Test invalid date format returns 400."""
        url = reverse("fee-list")
        data = {
            "name": "Test Fee",
            "amount": "5000.00",
            "due_date": "invalid-date",
            "estate": str(estate.id),
            "assign_to_all_units": True,
        }
        
        response = authenticated_client.post(url, data, format="json")
        
        assert response.status_code == 400
        assert "due_date" in response.data
    
    def test_update_nonexistent_fee_returns_404(self, authenticated_client):
        """Test updating non-existent fee returns 404."""
        import uuid
        fake_id = uuid.uuid4()
        url = reverse("fee-detail", args=[fake_id])
        data = {"name": "Updated"}
        
        response = authenticated_client.patch(url, data, format="json")
        
        assert response.status_code == 404
    
    def test_error_response_structure(self, authenticated_client, estate):
        """Test error response has correct structure."""
        url = reverse("fee-list")
        data = {
            "amount": "5000.00",
        }
        
        response = authenticated_client.post(url, data, format="json")
        
        assert response.status_code == 400
        assert isinstance(response.data, dict)
        assert "name" in response.data or "non_field_errors" in response.data


@pytest.mark.django_db
class TestPaymentErrorHandling:
    """Test error handling for payment endpoints."""
    
    def test_create_payment_with_invalid_fee_assignment_uuid(
        self, authenticated_client
    ):
        """Test invalid fee_assignment UUID returns 400."""
        url = reverse("payment-list")
        data = {
            "fee_assignment": "invalid-uuid",
            "amount": "5000.00",
            "payment_method": "cash",
        }
        
        response = authenticated_client.post(url, data, format="json")
        
        assert response.status_code == 400
        assert "fee_assignment" in response.data
    
    def test_create_payment_with_nonexistent_assignment(
        self, authenticated_client
    ):
        """Test non-existent fee_assignment returns 400."""
        import uuid
        url = reverse("payment-list")
        data = {
            "fee_assignment": str(uuid.uuid4()),
            "amount": "5000.00",
            "payment_method": "cash",
        }
        
        response = authenticated_client.post(url, data, format="json")
        
        assert response.status_code == 400
    
    def test_create_payment_with_negative_amount(
        self, authenticated_client, fee_assignment
    ):
        """Test negative amount returns 400 with proper error."""
        url = reverse("payment-list")
        data = {
            "fee_assignment": str(fee_assignment.id),
            "amount": "-100.00",
            "payment_method": "cash",
        }
        
        response = authenticated_client.post(url, data, format="json")
        
        assert response.status_code == 400
        assert "amount" in response.data
    
    def test_create_payment_exceeding_amount_limit(
        self, authenticated_client, fee_assignment
    ):
        """Test amount exceeding max digits returns 400."""
        url = reverse("payment-list")
        data = {
            "fee_assignment": str(fee_assignment.id),
            "amount": "99999999999999.99",
            "payment_method": "cash",
        }
        
        response = authenticated_client.post(url, data, format="json")
        
        assert response.status_code == 400
    
    def test_create_payment_with_invalid_method(
        self, authenticated_client, fee_assignment
    ):
        """Test invalid payment method returns 400."""
        url = reverse("payment-list")
        data = {
            "fee_assignment": str(fee_assignment.id),
            "amount": str(fee_assignment.fee.amount),
            "payment_method": "cryptocurrency",
        }
        
        response = authenticated_client.post(url, data, format="json")
        
        assert response.status_code == 400
        assert "payment_method" in response.data
    
    def test_payment_validation_errors_are_descriptive(
        self, authenticated_client, paid_fee_assignment
    ):
        """Test validation errors include descriptive messages."""
        url = reverse("payment-list")
        data = {
            "fee_assignment": str(paid_fee_assignment.id),
            "amount": str(paid_fee_assignment.fee.amount),
            "payment_method": "cash",
        }

        response = authenticated_client.post(url, data, format="json")

        assert response.status_code == 400
        
        # ✓ The actual error message says: "This fee has already been marked as paid"
        error_str = str(response.data).lower()
        
        assert "this fee has already been marked as paid" in error_str or \
            "already been marked as paid" in error_str or \
            "already" in error_str and "paid" in error_str, \
            f"Expected descriptive error, got: {response.data}"
        

@pytest.mark.django_db
class TestMethodNotAllowedErrors:
    """Test 405 Method Not Allowed errors."""
    
    def test_post_to_fee_assignment_not_allowed(
        self, authenticated_client
    ):
        """Test POST to fee assignments returns 405."""
        url = reverse("fee-assignment-list")
        data = {}
        
        response = authenticated_client.post(url, data, format="json")
        
        assert response.status_code == 405
    
    def test_put_to_receipt_not_allowed(self, authenticated_client, receipt):
        """Test PUT to receipt returns 405."""
        url = reverse("receipt-detail", args=[receipt.id])
        data = {"amount": "999.99"}
        
        response = authenticated_client.put(url, data, format="json")
        
        assert response.status_code == 405
    
    def test_delete_payment_not_allowed(self, authenticated_client, payment):
        """Test DELETE to payment returns 405."""
        url = reverse("payment-detail", args=[payment.id])
        
        response = authenticated_client.delete(url)
        
        assert response.status_code == 405


@pytest.mark.django_db
class TestNotFoundErrors:
    """Test 404 Not Found errors."""
    
    def test_get_nonexistent_fee_returns_404(self, authenticated_client):
        """Test retrieving non-existent fee returns 404."""
        import uuid
        fake_id = uuid.uuid4()
        url = reverse("fee-detail", args=[fake_id])
        
        response = authenticated_client.get(url)
        
        assert response.status_code == 404
    
    def test_get_with_invalid_uuid_returns_404(self, authenticated_client):
        """Test invalid UUID format returns 404."""
        url = reverse("fee-detail", args=["not-a-uuid"])
        
        response = authenticated_client.get(url)
        
        assert response.status_code == 404
    
    def test_nonexistent_page_returns_404(
        self, authenticated_client, fee
    ):
        """Test requesting non-existent page returns 404."""
        url = reverse("fee-list")
        response = authenticated_client.get(url, {"page": 999})
        
        assert response.status_code == 404


@pytest.mark.django_db
class TestErrorMessageQuality:
    """Test quality and clarity of error messages."""
    
    def test_missing_field_error_is_clear(self, authenticated_client):
        """Test missing required field error is clear."""
        url = reverse("fee-list")
        data = {"name": "Test Fee"}
        
        response = authenticated_client.post(url, data, format="json")
        
        assert response.status_code == 400
        assert "amount" in response.data
        assert isinstance(response.data["amount"], list)
        assert len(response.data["amount"]) > 0
    
    def test_validation_error_messages_dont_leak_sensitive_info(
        self, authenticated_client, estate
    ):
        """Test error messages don't expose sensitive information."""
        url = reverse("fee-list")
        data = {
            "name": "Test Fee",
            "amount": "5000.00",
            "due_date": (timezone.now() + timedelta(days=30)).date().isoformat(),
            "estate": str(estate.id),
        }
        
        response = authenticated_client.post(url, data, format="json")
        
        assert response.status_code == 400
        error_str = json.dumps(response.data)
        assert "password" not in error_str.lower()
        assert "secret" not in error_str.lower()
        assert "token" not in error_str.lower()