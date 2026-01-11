# tests/test_serializers.py

"""
Tests for payments app serializers.

Coverage:
- Field validation
- Required fields
- Read-only fields
- Custom validation logic
- Nested serialization
"""

import pytest
from decimal import Decimal
from datetime import timedelta
from django.utils import timezone
from payments.serializers import (
    FeeSerializer,
    FeeCreateSerializer,
    FeeAssignmentSerializer,
    PaymentSerializer,
    PaymentCreateSerializer,
    ReceiptSerializer,
)
from payments.models import FeeAssignment


@pytest.mark.django_db
class TestFeeSerializer:
    """Test FeeSerializer for reading fee data."""
    
    def test_serialize_fee(self, fee):
        """Test fee serialization includes all fields."""
        serializer = FeeSerializer(fee)
        data = serializer.data
        
        assert data["id"] == str(fee.id)
        assert data["name"] == fee.name
        assert data["amount"] == str(fee.amount)
        assert data["estate"] == str(fee.estate.id)
        assert "created_at" in data
        assert "updated_at" in data
    
    def test_computed_fields_included(self, fee_with_assignments):
        """Test computed fields are included in serialization."""
        serializer = FeeSerializer(fee_with_assignments)
        data = serializer.data
        
        assert "total_assigned_units" in data
        assert "total_paid_count" in data
        assert "total_unpaid_count" in data
        assert data["total_assigned_units"] == 5


@pytest.mark.django_db
class TestFeeCreateSerializer:
    """Test FeeCreateSerializer for creating fees."""
    
    def test_valid_fee_creation_with_all_units(self, estate, user):
        """Test creating fee with assign_to_all_units flag."""
        data = {
            "name": "Test Fee",
            "description": "Test description",
            "amount": "5000.00",
            "due_date": (timezone.now() + timedelta(days=30)).date(),
            "estate": str(estate.id),
            "assign_to_all_units": True,
        }
        
        serializer = FeeCreateSerializer(data=data)
        assert serializer.is_valid(), serializer.errors
    
    def test_valid_fee_creation_with_unit_ids(self, estate, units):
        """Test creating fee with specific unit IDs."""
        data = {
            "name": "Test Fee",
            "amount": "5000.00",
            "due_date": (timezone.now() + timedelta(days=30)).date(),
            "estate": str(estate.id),
            "unit_ids": [str(unit.id) for unit in units[:2]],
        }
        
        serializer = FeeCreateSerializer(data=data)
        assert serializer.is_valid(), serializer.errors
    
    def test_past_due_date_rejected(self, estate):
        """Test fee with past due date is rejected."""
        data = {
            "name": "Test Fee",
            "amount": "5000.00",
            "due_date": (timezone.now() - timedelta(days=1)).date(),
            "estate": str(estate.id),
            "assign_to_all_units": True,
        }
        
        serializer = FeeCreateSerializer(data=data)
        assert not serializer.is_valid()
        assert "due_date" in serializer.errors
    
    def test_missing_assignment_method_rejected(self, estate):
        """Test fee without assignment method is rejected."""
        data = {
            "name": "Test Fee",
            "amount": "5000.00",
            "due_date": (timezone.now() + timedelta(days=30)).date(),
            "estate": str(estate.id),
        }
        
        serializer = FeeCreateSerializer(data=data)
        assert not serializer.is_valid()
        assert "non_field_errors" in serializer.errors
    
    def test_both_assignment_methods_rejected(self, estate, units):
        """Test providing both assignment methods is rejected."""
        data = {
            "name": "Test Fee",
            "amount": "5000.00",
            "due_date": (timezone.now() + timedelta(days=30)).date(),
            "estate": str(estate.id),
            "assign_to_all_units": True,
            "unit_ids": [str(units[0].id)],
        }
        
        serializer = FeeCreateSerializer(data=data)
        assert not serializer.is_valid()
        assert "non_field_errors" in serializer.errors
    
    def test_missing_required_fields(self):
        """Test missing required fields are rejected."""
        data = {}
        serializer = FeeCreateSerializer(data=data)
        
        assert not serializer.is_valid()
        assert "name" in serializer.errors
        assert "amount" in serializer.errors
        assert "due_date" in serializer.errors
        assert "estate" in serializer.errors


@pytest.mark.django_db
class TestFeeAssignmentSerializer:
    """Test FeeAssignmentSerializer."""
    
    def test_serialize_fee_assignment(self, fee_assignment):
        """Test fee assignment serialization."""
        serializer = FeeAssignmentSerializer(fee_assignment)
        data = serializer.data
        
        assert data["id"] == str(fee_assignment.id)
        assert data["fee"] == str(fee_assignment.fee.id)
        assert data["unit"] == str(fee_assignment.unit.id)
        assert data["status"] == fee_assignment.status
        assert "fee_name" in data
        assert "fee_amount" in data
        assert "unit_identifier" in data
    
    def test_has_payment_field_false(self, fee_assignment):
        """Test has_payment field is False when no payment exists."""
        serializer = FeeAssignmentSerializer(fee_assignment)
        assert serializer.data["has_payment"] is False
    
    def test_has_payment_field_true(self, paid_fee_assignment):
        """Test has_payment field is True when payment exists."""
        serializer = FeeAssignmentSerializer(paid_fee_assignment)
        assert serializer.data["has_payment"] is True


@pytest.mark.django_db
class TestPaymentCreateSerializer:
    """Test PaymentCreateSerializer for recording payments."""
    
    def test_valid_payment_creation(self, fee_assignment):
        """Test creating payment with valid data."""
        data = {
            "fee_assignment": str(fee_assignment.id),
            "amount": str(fee_assignment.fee.amount),
            "payment_method": "bank_transfer",
            "reference_number": "REF123",
            "notes": "Test payment",
        }
        
        serializer = PaymentCreateSerializer(data=data)
        assert serializer.is_valid(), serializer.errors
    
    def test_amount_must_match_fee_amount(self, fee_assignment):
        """Test payment amount must match fee amount."""
        data = {
            "fee_assignment": str(fee_assignment.id),
            "amount": str(fee_assignment.fee.amount + Decimal("100.00")),
            "payment_method": "cash",
        }
        
        serializer = PaymentCreateSerializer(data=data)
        assert not serializer.is_valid()
        assert "amount" in serializer.errors
    
    def test_already_paid_assignment_rejected(self, paid_fee_assignment):
        """Test cannot create payment for already paid assignment."""
        data = {
            "fee_assignment": str(paid_fee_assignment.id),
            "amount": str(paid_fee_assignment.fee.amount),
            "payment_method": "cash",
        }
        
        serializer = PaymentCreateSerializer(data=data)
        assert not serializer.is_valid()
        assert "fee_assignment" in serializer.errors
    
    def test_negative_amount_rejected(self, fee_assignment):
        """Test negative payment amount is rejected."""
        data = {
            "fee_assignment": str(fee_assignment.id),
            "amount": "-100.00",
            "payment_method": "cash",
        }
        
        serializer = PaymentCreateSerializer(data=data)
        assert not serializer.is_valid()
        assert "amount" in serializer.errors
    
    def test_zero_amount_rejected(self, fee_assignment):
        """Test zero payment amount is rejected."""
        data = {
            "fee_assignment": str(fee_assignment.id),
            "amount": "0.00",
            "payment_method": "cash",
        }
        
        serializer = PaymentCreateSerializer(data=data)
        assert not serializer.is_valid()
        assert "amount" in serializer.errors
    
    def test_invalid_payment_method_rejected(self, fee_assignment):
        """Test invalid payment method is rejected."""
        data = {
            "fee_assignment": str(fee_assignment.id),
            "amount": str(fee_assignment.fee.amount),
            "payment_method": "invalid_method",
        }
        
        serializer = PaymentCreateSerializer(data=data)
        assert not serializer.is_valid()
        assert "payment_method" in serializer.errors


@pytest.mark.django_db
class TestPaymentSerializer:
    """Test PaymentSerializer for reading payment data."""
    
    def test_serialize_payment(self, payment):
        """Test payment serialization includes all fields."""
        serializer = PaymentSerializer(payment)
        data = serializer.data
        
        assert data["id"] == str(payment.id)
        assert data["amount"] == str(payment.amount)
        assert data["payment_method"] == payment.payment_method
        assert "fee_name" in data
        assert "unit_identifier" in data
        assert "estate_name" in data
        assert "recorded_by_name" in data
    
    def test_has_receipt_field(self, payment, receipt):
        """Test has_receipt field indicates receipt existence."""
        serializer = PaymentSerializer(payment)
        assert serializer.data["has_receipt"] is True


@pytest.mark.django_db
class TestReceiptSerializer:
    """Test ReceiptSerializer."""
    
    def test_serialize_receipt(self, receipt):
        """Test receipt serialization includes all fields."""
        serializer = ReceiptSerializer(receipt)
        data = serializer.data
        
        assert data["id"] == str(receipt.id)
        assert data["receipt_number"] == receipt.receipt_number
        assert data["estate_name"] == receipt.estate_name
        assert data["unit_identifier"] == receipt.unit_identifier
        assert data["fee_name"] == receipt.fee_name
        assert data["amount"] == str(receipt.amount)
        assert "payment_date" in data
        assert "issued_at" in data
    
    def test_all_fields_read_only(self, receipt):
        """Test all receipt fields are read-only."""
        data = {
            "receipt_number": "MODIFIED",
            "amount": "999999.99",
        }
        
        serializer = ReceiptSerializer(receipt, data=data, partial=True)
        assert serializer.is_valid()