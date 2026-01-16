# tests/test_views_create.py

"""
Tests for payments app create/POST endpoints.

Coverage:
- Authentication/authorization for creation
- Valid data creates resources
- Invalid data returns 400 with errors
- Database side effects verified
- Location headers
"""

import pytest
from decimal import Decimal
from datetime import timedelta
from django.urls import reverse
from django.utils import timezone
from payments.models import Fee, FeeAssignment, Payment, Receipt


@pytest.mark.django_db
class TestFeeCreateEndpoint:
    """Test POST /fees/ endpoint."""
    
    def test_unauthenticated_access_denied(self, api_client, estate):
        """Test unauthenticated users cannot create fees."""
        url = reverse("fee-list")
        data = {
            "name": "Test Fee",
            "amount": "5000.00",
            "due_date": (timezone.now() + timedelta(days=30)).date().isoformat(),
            "estate": str(estate.id),
            "assign_to_all_units": True,
        }
        response = api_client.post(url, data, format="json")
        
        assert response.status_code == 401
    
    def test_regular_user_cannot_create_fee(self, regular_user_client, estate):
        """Test regular users cannot create fees."""
        url = reverse("fee-list")
        data = {
            "name": "Test Fee",
            "amount": "5000.00",
            "due_date": (timezone.now() + timedelta(days=30)).date().isoformat(),
            "estate": str(estate.id),
            "assign_to_all_units": True,
        }
        response = regular_user_client.post(url, data, format="json")
        
        assert response.status_code == 403
    
    def test_estate_manager_can_create_fee_all_units(
        self, authenticated_client, estate, units
    ):
        """Test estate manager can create fee assigned to all units."""
        url = reverse("fee-list")
        data = {
            "name": "Security Levy 2025",
            "description": "Annual security levy",
            "amount": "10000.00",
            "due_date": (timezone.now() + timedelta(days=30)).date().isoformat(),
            "estate": str(estate.id),
            "assign_to_all_units": True,
        }
        
        response = authenticated_client.post(url, data, format="json")
        
        assert response.status_code == 201
        assert response.data["name"] == "Security Levy 2025"
        assert response.data["amount"] == "10000.00"
        
        fee = Fee.objects.get(id=response.data["id"])
        assert fee.name == "Security Levy 2025"
        assert fee.amount == Decimal("10000.00")
        assert fee.fee_assignments.count() == len(units)
    
    def test_create_fee_with_specific_units(
        self, authenticated_client, estate, units
    ):
        """Test creating fee assigned to specific units."""
        url = reverse("fee-list")
        unit_ids = [str(unit.id) for unit in units[:2]]
        data = {
            "name": "Water Bill",
            "amount": "2500.00",
            "due_date": (timezone.now() + timedelta(days=15)).date().isoformat(),
            "estate": str(estate.id),
            "unit_ids": unit_ids,
        }
        
        response = authenticated_client.post(url, data, format="json")
        
        assert response.status_code == 201
        
        fee = Fee.objects.get(id=response.data["id"])
        assert fee.fee_assignments.count() == 2
        assignment_unit_ids = set(
            str(a.unit_id) for a in fee.fee_assignments.all()
        )
        assert assignment_unit_ids == set(unit_ids)
    
    def test_create_fee_missing_required_fields(self, authenticated_client):
        """Test creating fee without required fields fails."""
        url = reverse("fee-list")
        data = {}
        
        response = authenticated_client.post(url, data, format="json")
        
        assert response.status_code == 400
        assert "name" in response.data
        assert "amount" in response.data
        assert "due_date" in response.data
        assert "estate" in response.data
    
    def test_create_fee_past_due_date_rejected(
        self, authenticated_client, estate
    ):
        """Test creating fee with past due date is rejected."""
        url = reverse("fee-list")
        data = {
            "name": "Test Fee",
            "amount": "5000.00",
            "due_date": (timezone.now() - timedelta(days=1)).date().isoformat(),
            "estate": str(estate.id),
            "assign_to_all_units": True,
        }
        
        response = authenticated_client.post(url, data, format="json")
        
        assert response.status_code == 400
        assert "due_date" in response.data
    
    def test_create_fee_negative_amount_rejected(
        self, authenticated_client, estate
    ):
        """Test creating fee with negative amount is rejected."""
        url = reverse("fee-list")
        data = {
            "name": "Test Fee",
            "amount": "-1000.00",
            "due_date": (timezone.now() + timedelta(days=30)).date().isoformat(),
            "estate": str(estate.id),
            "assign_to_all_units": True,
        }
        
        response = authenticated_client.post(url, data, format="json")
        
        assert response.status_code == 400
        assert "amount" in response.data
    
    def test_create_fee_zero_amount_rejected(self, authenticated_client, estate):
        """Test creating fee with zero amount is rejected."""
        url = reverse("fee-list")
        data = {
            "name": "Test Fee",
            "amount": "0.00",
            "due_date": (timezone.now() + timedelta(days=30)).date().isoformat(),
            "estate": str(estate.id),
            "assign_to_all_units": True,
        }
        
        response = authenticated_client.post(url, data, format="json")
        
        assert response.status_code == 400
    
    def test_create_fee_without_assignment_method_rejected(
        self, authenticated_client, estate
    ):
        """Test creating fee without assignment method is rejected."""
        url = reverse("fee-list")
        data = {
            "name": "Test Fee",
            "amount": "5000.00",
            "due_date": (timezone.now() + timedelta(days=30)).date().isoformat(),
            "estate": str(estate.id),
        }
        
        response = authenticated_client.post(url, data, format="json")
        
        assert response.status_code == 400
        assert "non_field_errors" in response.data
    
    def test_create_fee_sets_created_by(self, authenticated_client, user, estate):
        """Test creating fee sets created_by to authenticated user."""
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
        
        fee = Fee.objects.get(id=response.data["id"])
        assert fee.created_by == user
    
    def test_create_fee_with_invalid_unit_ids(
        self, authenticated_client, estate
    ):
        """Test creating fee with invalid unit IDs fails."""
        url = reverse("fee-list")
        data = {
            "name": "Test Fee",
            "amount": "5000.00",
            "due_date": (timezone.now() + timedelta(days=30)).date().isoformat(),
            "estate": str(estate.id),
            "unit_ids": ["invalid-uuid", "another-invalid"],
        }
        
        response = authenticated_client.post(url, data, format="json")
        
        assert response.status_code == 400


@pytest.mark.django_db
class TestPaymentCreateEndpoint:
    """Test POST /payments/ endpoint."""
    
    def test_unauthenticated_access_denied(self, api_client, fee_assignment):
        """Test unauthenticated users cannot create payments."""
        url = reverse("payment-list")
        data = {
            "fee_assignment": str(fee_assignment.id),
            "amount": str(fee_assignment.fee.amount),
            "payment_method": "cash",
        }
        response = api_client.post(url, data, format="json")
        
        assert response.status_code == 401
    
    def test_regular_user_cannot_create_payment(
        self, regular_user_client, fee_assignment
    ):
        """Test regular users cannot record payments."""
        url = reverse("payment-list")
        data = {
            "fee_assignment": str(fee_assignment.id),
            "amount": str(fee_assignment.fee.amount),
            "payment_method": "cash",
        }
        response = regular_user_client.post(url, data, format="json")
        
        assert response.status_code == 403
    
    def test_estate_manager_can_create_payment(
        self, authenticated_client, fee_assignment, user
    ):
        """Test estate manager can record payment."""
        url = reverse("payment-list")
        data = {
            "fee_assignment": str(fee_assignment.id),
            "amount": str(fee_assignment.fee.amount),
            "payment_method": "bank_transfer",
            "reference_number": "REF123",
            "notes": "Payment received",
        }
        
        response = authenticated_client.post(url, data, format="json")
        
        assert response.status_code == 201
        assert Decimal(response.data["amount"]) == fee_assignment.fee.amount
        assert response.data["payment_method"] == "bank_transfer"
        
        payment = Payment.objects.get(id=response.data['id'])
        assert payment.recorded_by == user
        assert payment.reference_number == "REF123"
    
    def test_payment_creation_updates_assignment_status(
        self, authenticated_client, fee_assignment
    ):
        """Test creating payment updates fee assignment to paid."""
        url = reverse("payment-list")
        data = {
            "fee_assignment": str(fee_assignment.id),
            "amount": str(fee_assignment.fee.amount),
            "payment_method": "cash",
        }
        
        initial_status = fee_assignment.status
        assert initial_status == "unpaid"
        
        response = authenticated_client.post(url, data, format="json")
        
        assert response.status_code == 201
        
        fee_assignment.refresh_from_db()
        assert fee_assignment.status == "paid"
    
    def test_payment_creation_generates_receipt(
        self, authenticated_client, fee_assignment
    ):
        """Test creating payment automatically generates receipt."""
        url = reverse("payment-list")
        data = {
            "fee_assignment": str(fee_assignment.id),
            "amount": str(fee_assignment.fee.amount),
            "payment_method": "bank_transfer",
        }
        
        response = authenticated_client.post(url, data, format="json")
        
        assert response.status_code == 201
        
        payment = Payment.objects.get(id=response.data['id'])
        assert hasattr(payment, 'receipt')
        
        receipt = payment.receipt
        assert receipt.receipt_number.startswith("RCP-")
        assert receipt.amount == payment.amount
        assert receipt.estate_name == fee_assignment.fee.estate.name
    
    def test_cannot_pay_already_paid_assignment(
        self, authenticated_client, paid_fee_assignment
    ):
        """Test cannot create payment for already paid assignment."""
        url = reverse("payment-list")
        data = {
            "fee_assignment": str(paid_fee_assignment.id),
            "amount": str(paid_fee_assignment.fee.amount),
            "payment_method": "cash",
        }
        
        response = authenticated_client.post(url, data, format="json")
        
        assert response.status_code == 400
        assert "fee_assignment" in response.data
    
    def test_payment_amount_must_match_fee_amount(
        self, authenticated_client, fee_assignment
    ):
        """Test payment amount must exactly match fee amount."""
        url = reverse("payment-list")
        wrong_amount = fee_assignment.fee.amount + Decimal("100.00")
        data = {
            "fee_assignment": str(fee_assignment.id),
            "amount": str(wrong_amount),
            "payment_method": "cash",
        }
        
        response = authenticated_client.post(url, data, format="json")
        
        assert response.status_code == 400
        assert "amount" in response.data
    
    def test_payment_with_invalid_method_rejected(
        self, authenticated_client, fee_assignment
    ):
        """Test payment with invalid payment method is rejected."""
        url = reverse("payment-list")
        data = {
            "fee_assignment": str(fee_assignment.id),
            "amount": str(fee_assignment.fee.amount),
            "payment_method": "invalid_method",
        }
        
        response = authenticated_client.post(url, data, format="json")
        
        assert response.status_code == 400
        assert "payment_method" in response.data
    
    def test_payment_missing_required_fields(self, authenticated_client):
        """Test payment creation with missing fields fails."""
        url = reverse("payment-list")
        data = {}
        
        response = authenticated_client.post(url, data, format="json")
        
        assert response.status_code == 400
        assert "fee_assignment" in response.data
        assert "amount" in response.data
        assert "payment_method" in response.data