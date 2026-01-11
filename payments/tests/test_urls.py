# tests/test_urls.py

"""
Tests for payments app URL routing.

Coverage:
- URL patterns resolve correctly
- URL names are registered
- Reverse URL lookup works
"""

import pytest
from django.urls import reverse, resolve
from payments import views


@pytest.mark.django_db
class TestFeeURLs:
    """Test URL routing for Fee endpoints."""
    
    def test_fee_list_url_resolves(self):
        """Test fee list URL resolves to correct view."""
        url = reverse("fee-list")
        assert url == "/payments/fees/"
        
        resolver = resolve(url)
        assert resolver.func.cls == views.FeeViewSet
    
    def test_fee_detail_url_resolves(self, fee):
        """Test fee detail URL resolves correctly."""
        url = reverse("fee-detail", args=[fee.id])
        assert url == f"/payments/fees/{fee.id}/"
        
        resolver = resolve(url)
        assert resolver.func.cls == views.FeeViewSet
    
    def test_fee_payment_summary_url_resolves(self, fee):
        """Test fee payment summary custom action URL."""
        url = reverse("fee-payment-summary", args=[fee.id])
        assert url == f"/payments/fees/{fee.id}/payment_summary/"
    
    def test_fee_assign_to_units_url_resolves(self, fee):
        """Test fee assign to units custom action URL."""
        url = reverse("fee-assign-to-units", args=[fee.id])
        assert url == f"/payments/fees/{fee.id}/assign_to_units/"


@pytest.mark.django_db
class TestFeeAssignmentURLs:
    """Test URL routing for FeeAssignment endpoints."""
    
    def test_fee_assignment_list_url_resolves(self):
        """Test fee assignment list URL resolves correctly."""
        url = reverse("fee-assignment-list")
        assert url == "/payments/assignments/"
        
        resolver = resolve(url)
        assert resolver.func.cls == views.FeeAssignmentViewSet
    
    def test_fee_assignment_detail_url_resolves(self, fee_assignment):
        """Test fee assignment detail URL resolves correctly."""
        url = reverse("fee-assignment-detail", args=[fee_assignment.id])
        assert url == f"/payments/assignments/{fee_assignment.id}/"
        
        resolver = resolve(url)
        assert resolver.func.cls == views.FeeAssignmentViewSet


@pytest.mark.django_db
class TestPaymentURLs:
    """Test URL routing for Payment endpoints."""
    
    def test_payment_list_url_resolves(self):
        """Test payment list URL resolves correctly."""
        url = reverse("payment-list")
        assert url == "/payments/payments/"
        
        resolver = resolve(url)
        assert resolver.func.cls == views.PaymentViewSet
    
    def test_payment_detail_url_resolves(self, payment):
        """Test payment detail URL resolves correctly."""
        url = reverse("payment-detail", args=[payment.id])
        assert url == f"/payments/payments/{payment.id}/"
        
        resolver = resolve(url)
        assert resolver.func.cls == views.PaymentViewSet


@pytest.mark.django_db
class TestReceiptURLs:
    """Test URL routing for Receipt endpoints."""
    
    def test_receipt_list_url_resolves(self):
        """Test receipt list URL resolves correctly."""
        url = reverse("receipt-list")
        assert url == "/payments/receipts/"
        
        resolver = resolve(url)
        assert resolver.func.cls == views.ReceiptViewSet
    
    def test_receipt_detail_url_resolves(self, receipt):
        """Test receipt detail URL resolves correctly."""
        url = reverse("receipt-detail", args=[receipt.id])
        assert url == f"/payments/receipts/{receipt.id}/"
        
        resolver = resolve(url)
        assert resolver.func.cls == views.ReceiptViewSet
    
    def test_receipt_download_url_resolves(self, receipt):
        """Test receipt download custom action URL."""
        url = reverse("receipt-download", args=[receipt.id])
        assert url == f"/payments/receipts/{receipt.id}/download/"