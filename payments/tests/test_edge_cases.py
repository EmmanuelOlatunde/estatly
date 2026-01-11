# tests/test_edge_cases.py

"""
Tests for edge cases and boundary conditions.

Coverage:
- Empty strings vs null
- Boundary values (max amounts, dates)
- Unicode and special characters
- Concurrent operations
- Large datasets
"""

import pytest
from decimal import Decimal
from datetime import timedelta
from django.urls import reverse
from django.utils import timezone
from .factories import FeeFactory, FeeAssignmentFactory


@pytest.mark.django_db
class TestFeeEdgeCases:
    """Test edge cases for fee operations."""
    
    def test_fee_with_empty_description(self, authenticated_client, estate):
        """Test creating fee with empty description is allowed."""
        url = reverse("fee-list")
        data = {
            "name": "Test Fee",
            "description": "",
            "amount": "5000.00",
            "due_date": (timezone.now() + timedelta(days=30)).date().isoformat(),
            "estate": str(estate.id),
            "assign_to_all_units": True,
        }
        
        response = authenticated_client.post(url, data, format="json")
        
        assert response.status_code == 201
        assert response.data["description"] == ""
    
    def test_fee_with_very_long_name(self, authenticated_client, estate):
        """Test fee with name near max length."""
        long_name = "A" * 250
        url = reverse("fee-list")
        data = {
            "name": long_name,
            "amount": "5000.00",
            "due_date": (timezone.now() + timedelta(days=30)).date().isoformat(),
            "estate": str(estate.id),
            "assign_to_all_units": True,
        }
        
        response = authenticated_client.post(url, data, format="json")
        
        assert response.status_code == 201
        assert response.data["name"] == long_name
    
    def test_fee_with_unicode_characters(self, authenticated_client, estate):
        """Test fee with unicode characters in name."""
        url = reverse("fee-list")
        data = {
            "name": "Frais de sécurité 2025 🏠",
            "amount": "5000.00",
            "due_date": (timezone.now() + timedelta(days=30)).date().isoformat(),
            "estate": str(estate.id),
            "assign_to_all_units": True,
        }
        
        response = authenticated_client.post(url, data, format="json")
        
        assert response.status_code == 201
        assert "🏠" in response.data["name"]
    
    def test_fee_with_special_characters(self, authenticated_client, estate):
        """Test fee with special characters in name."""
        url = reverse("fee-list")
        data = {
            "name": "Fee & Charges (2025) - 50%",
            "amount": "5000.00",
            "due_date": (timezone.now() + timedelta(days=30)).date().isoformat(),
            "estate": str(estate.id),
            "assign_to_all_units": True,
        }
        
        response = authenticated_client.post(url, data, format="json")
        
        assert response.status_code == 201
        assert "&" in response.data["name"]
    
    def test_fee_with_very_large_amount(self, authenticated_client, estate):
        """Test fee with very large amount."""
        url = reverse("fee-list")
        data = {
            "name": "Large Fee",
            "amount": "9999999999.99",
            "due_date": (timezone.now() + timedelta(days=30)).date().isoformat(),
            "estate": str(estate.id),
            "assign_to_all_units": True,
        }
        
        response = authenticated_client.post(url, data, format="json")
        
        assert response.status_code == 201
        assert Decimal(response.data["amount"]) == Decimal("9999999999.99")
    
    def test_fee_with_minimum_amount(self, authenticated_client, estate):
        """Test fee with minimum valid amount."""
        url = reverse("fee-list")
        data = {
            "name": "Minimum Fee",
            "amount": "0.01",
            "due_date": (timezone.now() + timedelta(days=30)).date().isoformat(),
            "estate": str(estate.id),
            "assign_to_all_units": True,
        }
        
        response = authenticated_client.post(url, data, format="json")
        
        assert response.status_code == 201
        assert Decimal(response.data["amount"]) == Decimal("0.01")
    
    def test_fee_with_many_decimal_places(self, authenticated_client, estate):
        """Test fee amount is rounded to 2 decimal places."""
        url = reverse("fee-list")
        data = {
            "name": "Test Fee",
            "amount": "5000.12345",
            "due_date": (timezone.now() + timedelta(days=30)).date().isoformat(),
            "estate": str(estate.id),
            "assign_to_all_units": True,
        }
        
        response = authenticated_client.post(url, data, format="json")
        
        assert response.status_code == 201
        assert Decimal(response.data["amount"]) == Decimal("5000.12")
    
    def test_assign_fee_to_no_units_when_estate_empty(
        self, authenticated_client, estate
    ):
        """Test assigning fee to all units when estate has no units."""
        url = reverse("fee-list")
        data = {
            "name": "Test Fee",
            "amount": "5000.00",
            "due_date": (timezone.now() + timedelta(days=30)).date().isoformat(),
            "estate": str(estate.id),
            "assign_to_all_units": True,
        }
        
        response = authenticated_client.post(url, data, format="json")
        
        assert response.status_code == 201
    
    def test_list_fees_with_large_dataset(
        self, authenticated_client, estate, user
    ):
        """Test listing fees with large dataset."""
        FeeFactory.create_batch(100, estate=estate, created_by=user)
        
        url = reverse("fee-list")
        response = authenticated_client.get(url)
        
        assert response.status_code == 200
        assert response.data["count"] == 100


@pytest.mark.django_db
class TestPaymentEdgeCases:
    """Test edge cases for payment operations."""
    
    def test_payment_with_empty_reference_number(
        self, authenticated_client, fee_assignment
    ):
        """Test payment with empty reference number is allowed."""
        url = reverse("payment-list")
        data = {
            "fee_assignment": str(fee_assignment.id),
            "amount": str(fee_assignment.fee.amount),
            "payment_method": "cash",
            "reference_number": "",
        }
        
        response = authenticated_client.post(url, data, format="json")
        
        assert response.status_code == 201
        assert response.data["reference_number"] == ""
    
    def test_payment_with_very_long_reference(
        self, authenticated_client, fee_assignment
    ):
        """Test payment with long reference number."""
        long_ref = "REF" * 30
        url = reverse("payment-list")
        data = {
            "fee_assignment": str(fee_assignment.id),
            "amount": str(fee_assignment.fee.amount),
            "payment_method": "bank_transfer",
            "reference_number": long_ref,
        }
        
        response = authenticated_client.post(url, data, format="json")
        
        assert response.status_code == 201
    
    def test_payment_with_unicode_notes(
        self, authenticated_client, fee_assignment
    ):
        """Test payment with unicode characters in notes."""
        url = reverse("payment-list")
        data = {
            "fee_assignment": str(fee_assignment.id),
            "amount": str(fee_assignment.fee.amount),
            "payment_method": "cash",
            "notes": "Payment reçu avec succès 💰",
        }
        
        response = authenticated_client.post(url, data, format="json")
        
        assert response.status_code == 201
        assert "💰" in response.data["notes"]
    
    def test_multiple_payments_different_assignments(
        self, authenticated_client, user, units, fee
    ):
        """Test creating multiple payments for different assignments."""
        assignments = [
            FeeAssignmentFactory.create(fee=fee, unit=unit)
            for unit in units[:3]
        ]
        
        url = reverse("payment-list")
        for assignment in assignments:
            data = {
                "fee_assignment": str(assignment.id),
                "amount": str(assignment.fee.amount),
                "payment_method": "cash",
            }
            response = authenticated_client.post(url, data, format="json")
            assert response.status_code == 201


@pytest.mark.django_db
class TestReceiptEdgeCases:
    """Test edge cases for receipts."""
    
    def test_receipt_number_uniqueness(
        self, authenticated_client, fee_assignment, user
    ):
        """Test receipt numbers are unique."""
        url = reverse("payment-list")
        
        receipts = []
        for _ in range(5):
            assignment = FeeAssignmentFactory.create()
            data = {
                "fee_assignment": str(assignment.id),
                "amount": str(assignment.fee.amount),
                "payment_method": "cash",
            }
            response = authenticated_client.post(url, data, format="json")
            assert response.status_code == 201
            
            payment_id = response.data["id"]
            receipt_url = reverse("receipt-list")
            receipt_response = authenticated_client.get(
                receipt_url,
                {"payment": payment_id}
            )
            receipts.append(receipt_response.data["results"][0]["receipt_number"])
        
        assert len(set(receipts)) == 5
    
    def test_list_receipts_with_many_records(self, authenticated_client):
        """Test listing receipts with large dataset."""
        from .factories import ReceiptFactory, PaymentFactory
        
        for _ in range(50):
            ReceiptFactory.create(payment=PaymentFactory.create())
        
        url = reverse("receipt-list")
        response = authenticated_client.get(url)
        
        assert response.status_code == 200
        assert response.data["count"] == 50