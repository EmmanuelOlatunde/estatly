# tests/test_ordering.py

"""
Tests for ordering/sorting functionality.

Coverage:
- Default ordering
- Custom ordering parameters
- Multiple field ordering
- Ascending/descending order
"""

import pytest
from decimal import Decimal
from datetime import timedelta
from django.urls import reverse
from django.utils import timezone
from .factories import FeeFactory, PaymentFactory, ReceiptFactory


@pytest.mark.django_db
class TestFeeOrdering:
    """Test ordering for /fees/ endpoint."""
    
    def test_default_ordering_by_created_at_desc(
        self, authenticated_client, estate, user
    ):
        """Test fees are ordered by created_at descending by default."""
        from datetime import timedelta
        import time
        # Create with explicit timestamps to guarantee ordering
        base_time = timezone.now()
        
        fee1 = FeeFactory.create(
            estate=estate,
            created_by=user,
            name="First",
            created_at=base_time - timedelta(hours=2)
        )
        time.sleep(0.1)
        fee2 = FeeFactory.create(
            estate=estate,
            created_by=user,
            name="Second",
            created_at=base_time - timedelta(hours=1)
        )
        time.sleep(0.2)
        fee3 = FeeFactory.create(
            estate=estate,
            created_by=user,
            name="Third",
            created_at=base_time
        )

        url = reverse("fee-list")
        response = authenticated_client.get(url)

        assert response.status_code == 200
        results = response.data["results"]
        assert results[0]["id"] == str(fee3.id)  # Most recent first
        assert results[1]["id"] == str(fee2.id)
        assert results[2]["id"] == str(fee1.id)
    
    def test_order_by_amount_ascending(self, authenticated_client, estate, user):
        """Test ordering fees by amount ascending."""
        fee1 = FeeFactory.create(
            estate=estate, created_by=user, amount=Decimal("10000.00")
        )
        fee2 = FeeFactory.create(
            estate=estate, created_by=user, amount=Decimal("5000.00")
        )
        fee3 = FeeFactory.create(
            estate=estate, created_by=user, amount=Decimal("15000.00")
        )
        
        url = reverse("fee-list")
        response = authenticated_client.get(url, {"ordering": "amount"})
        
        assert response.status_code == 200
        results = response.data["results"]
        assert results[0]["id"] == str(fee2.id)
        assert results[1]["id"] == str(fee1.id)
        assert results[2]["id"] == str(fee3.id)
    
    def test_order_by_amount_descending(self, authenticated_client, estate, user):
        """Test ordering fees by amount descending."""
        fee1 = FeeFactory.create(
            estate=estate, created_by=user, amount=Decimal("10000.00")
        )
        fee2 = FeeFactory.create(
            estate=estate, created_by=user, amount=Decimal("5000.00")
        )
        fee3 = FeeFactory.create(
            estate=estate, created_by=user, amount=Decimal("15000.00")
        )
        
        url = reverse("fee-list")
        response = authenticated_client.get(url, {"ordering": "-amount"})
        
        assert response.status_code == 200
        results = response.data["results"]
        assert results[0]["id"] == str(fee3.id)
        assert results[1]["id"] == str(fee1.id)
        assert results[2]["id"] == str(fee2.id)
    
    def test_order_by_due_date(self, authenticated_client, estate, user):
        """Test ordering fees by due date."""
        today = timezone.now().date()
        fee1 = FeeFactory.create(
            estate=estate, created_by=user, due_date=today + timedelta(days=30)
        )
        fee2 = FeeFactory.create(
            estate=estate, created_by=user, due_date=today + timedelta(days=10)
        )
        fee3 = FeeFactory.create(
            estate=estate, created_by=user, due_date=today + timedelta(days=60)
        )
        
        url = reverse("fee-list")
        response = authenticated_client.get(url, {"ordering": "due_date"})
        
        assert response.status_code == 200
        results = response.data["results"]
        assert results[0]["id"] == str(fee2.id)
        assert results[1]["id"] == str(fee1.id)
        assert results[2]["id"] == str(fee3.id)
    
    def test_invalid_ordering_field_ignored(
        self, authenticated_client, estate, user
    ):
        """Test invalid ordering field is ignored."""
        FeeFactory.create_batch(3, estate=estate, created_by=user)
        
        url = reverse("fee-list")
        response = authenticated_client.get(url, {"ordering": "invalid_field"})
        
        assert response.status_code == 200


@pytest.mark.django_db
class TestPaymentOrdering:
    """Test ordering for /payments/ endpoint."""
    
    def test_default_ordering_by_payment_date_desc(
        self, authenticated_client, user
    ):
        """Test payments are ordered by payment_date descending by default."""
        today = timezone.now()
        payment1 = PaymentFactory.create(
            recorded_by=user, payment_date=today - timedelta(days=10)
        )
        payment2 = PaymentFactory.create(
            recorded_by=user, payment_date=today
        )
        payment3 = PaymentFactory.create(
            recorded_by=user, payment_date=today - timedelta(days=5)
        )
        
        url = reverse("payment-list")
        response = authenticated_client.get(url)
        
        assert response.status_code == 200
        results = response.data["results"]
        assert results[0]["id"] == str(payment2.id)
        assert results[1]["id"] == str(payment3.id)
        assert results[2]["id"] == str(payment1.id)
    
    def test_order_by_amount(self, authenticated_client, user):
        """Test ordering payments by amount."""
        payment1 = PaymentFactory.create(
            recorded_by=user,
            fee_assignment__fee__amount=Decimal("5000.00"),
            amount=Decimal("5000.00")
        )
        payment2 = PaymentFactory.create(
            recorded_by=user,
            fee_assignment__fee__amount=Decimal("10000.00"),
            amount=Decimal("10000.00")
        )
        
        url = reverse("payment-list")
        response = authenticated_client.get(url, {"ordering": "amount"})
        
        assert response.status_code == 200
        results = response.data["results"]
        assert results[0]["id"] == str(payment1.id)
        assert results[1]["id"] == str(payment2.id)
    
    def test_order_by_created_at(self, authenticated_client, user):
        """Test ordering payments by creation date."""
        payment1 = PaymentFactory.create(recorded_by=user)
        payment2 = PaymentFactory.create(recorded_by=user)
        
        url = reverse("payment-list")
        response = authenticated_client.get(url, {"ordering": "created_at"})
        
        assert response.status_code == 200
        assert len(response.data["results"]) == 2


@pytest.mark.django_db
class TestReceiptOrdering:
    """Test ordering for /receipts/ endpoint."""
    
    def test_default_ordering_by_issued_at_desc(self, authenticated_client):
        """Test receipts are ordered by issued_at descending by default."""
        receipt1 = ReceiptFactory.create()
        receipt2 = ReceiptFactory.create()
        receipt3 = ReceiptFactory.create()
        
        url = reverse("receipt-list")
        response = authenticated_client.get(url)
        
        assert response.status_code == 200
        results = response.data["results"]
        assert results[0]["id"] == str(receipt3.id)
        assert results[1]["id"] == str(receipt2.id)
        assert results[2]["id"] == str(receipt1.id)
    
    def test_order_by_payment_date(self, authenticated_client):
        """Test ordering receipts by payment date."""
        today = timezone.now()
        receipt1 = ReceiptFactory.create(
            payment__payment_date=today - timedelta(days=5),
            payment_date=today - timedelta(days=5)
        )
        receipt2 = ReceiptFactory.create(
            payment__payment_date=today,
            payment_date=today
        )
        
        url = reverse("receipt-list")
        response = authenticated_client.get(url, {"ordering": "payment_date"})
        
        assert response.status_code == 200
        results = response.data["results"]
        assert results[0]["id"] == str(receipt1.id)
        assert results[1]["id"] == str(receipt2.id)