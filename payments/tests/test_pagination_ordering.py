# tests/test_pagination.py

"""
Tests for pagination behavior across all list endpoints.

Coverage:
- Default pagination
- Page size parameter
- Page navigation
- Edge cases (empty, single page, last page)
"""

import pytest
from django.urls import reverse
from .factories import FeeFactory, FeeAssignmentFactory, PaymentFactory, ReceiptFactory


@pytest.mark.django_db
class TestFeePagination:
    """Test pagination for /fees/ endpoint."""
    
    def test_default_pagination_structure(self, authenticated_client, estate, user):
        """Test default pagination includes count, next, previous, results."""
        FeeFactory.create_batch(3, estate=estate, created_by=user)
        
        url = reverse("fee-list")
        response = authenticated_client.get(url)
        
        assert response.status_code == 200
        assert "count" in response.data
        assert "next" in response.data
        assert "previous" in response.data
        assert "results" in response.data
        assert response.data["count"] == 3
    
    def test_pagination_with_many_items(self, authenticated_client, estate, user):
        """Test pagination with more items than default page size."""
        FeeFactory.create_batch(25, estate=estate, created_by=user)
        
        url = reverse("fee-list")
        response = authenticated_client.get(url)
        
        assert response.status_code == 200
        assert response.data["count"] == 25
        assert len(response.data["results"]) <= 25
    
    def test_page_size_parameter(self, authenticated_client, estate, user):
        """Test custom page size parameter."""
        FeeFactory.create_batch(15, estate=estate, created_by=user)
        
        url = reverse("fee-list")
        response = authenticated_client.get(url, {"page_size": 5})
        
        assert response.status_code == 200
        assert len(response.data["results"]) == 5
        assert response.data["count"] == 15
    
    def test_navigate_to_second_page(self, authenticated_client, estate, user):
        """Test navigating to second page."""
        FeeFactory.create_batch(15, estate=estate, created_by=user)
        
        url = reverse("fee-list")
        response = authenticated_client.get(url, {"page_size": 10, "page": 2})
        
        assert response.status_code == 200
        assert len(response.data["results"]) == 5
    
    def test_first_page_has_no_previous(self, authenticated_client, estate, user):
        """Test first page has no previous link."""
        FeeFactory.create_batch(15, estate=estate, created_by=user)
        
        url = reverse("fee-list")
        response = authenticated_client.get(url, {"page": 1})
        
        assert response.status_code == 200
        assert response.data["previous"] is None
    
    def test_last_page_has_no_next(self, authenticated_client, estate, user):
        """Test last page has no next link."""
        FeeFactory.create_batch(15, estate=estate, created_by=user)
        
        url = reverse("fee-list")
        response = authenticated_client.get(url, {"page_size": 10, "page": 2})
        
        assert response.status_code == 200
        assert response.data["next"] is None
    
    def test_invalid_page_number(self, authenticated_client, estate, user):
        """Test requesting invalid page number."""
        FeeFactory.create_batch(5, estate=estate, created_by=user)
        
        url = reverse("fee-list")
        response = authenticated_client.get(url, {"page": 999})
        
        assert response.status_code == 404
    
    def test_page_zero_invalid(self, authenticated_client, estate, user):
        """Test page zero is invalid."""
        FeeFactory.create_batch(5, estate=estate, created_by=user)
        
        url = reverse("fee-list")
        response = authenticated_client.get(url, {"page": 0})
        
        assert response.status_code == 404
    
    def test_empty_results_pagination(self, authenticated_client):
        """Test pagination with no results."""
        url = reverse("fee-list")
        response = authenticated_client.get(url)
        
        assert response.status_code == 200
        assert response.data["count"] == 0
        assert response.data["results"] == []
        assert response.data["next"] is None
        assert response.data["previous"] is None


@pytest.mark.django_db
class TestPaymentPagination:
    """Test pagination for /payments/ endpoint."""
    
    def test_payment_pagination_structure(
        self, authenticated_client, fee_assignment, user
    ):
        """Test payment list has pagination structure."""
        for _ in range(5):
            PaymentFactory.create(
                fee_assignment=FeeAssignmentFactory.create(),
                recorded_by=user
            )
        
        url = reverse("payment-list")
        response = authenticated_client.get(url)
        
        assert response.status_code == 200
        assert "count" in response.data
        assert "results" in response.data
        assert response.data["count"] == 5
    
    def test_payment_custom_page_size(
        self, authenticated_client, fee_assignment, user
    ):
        """Test custom page size for payments."""
        for _ in range(10):
            PaymentFactory.create(
                fee_assignment=FeeAssignmentFactory.create(),
                recorded_by=user
            )
        
        url = reverse("payment-list")
        response = authenticated_client.get(url, {"page_size": 3})
        
        assert response.status_code == 200
        assert len(response.data["results"]) == 3
        assert response.data["count"] == 10


@pytest.mark.django_db
class TestReceiptPagination:
    """Test pagination for /receipts/ endpoint."""
    
    def test_receipt_pagination_structure(self, authenticated_client):
        """Test receipt list has pagination structure."""
        for _ in range(5):
            ReceiptFactory.create(payment=PaymentFactory.create())
        
        url = reverse("receipt-list")
        response = authenticated_client.get(url)
        
        assert response.status_code == 200
        assert "count" in response.data
        assert "results" in response.data
    
    def test_receipt_page_navigation(self, authenticated_client):
        """Test navigating receipt pages."""
        for _ in range(15):
            ReceiptFactory.create(payment=PaymentFactory.create())
        
        url = reverse("receipt-list")
        response = authenticated_client.get(url, {"page_size": 10})
        
        assert response.status_code == 200
        assert response.data["count"] == 15
        assert len(response.data["results"]) == 10
        assert response.data["next"] is not None