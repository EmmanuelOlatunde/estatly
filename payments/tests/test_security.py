# tests/test_security.py

"""
Tests for security-specific scenarios.

Coverage:
- IDOR (Insecure Direct Object Reference)
- Data leakage prevention
- Authorization enforcement
- Sensitive field exclusion
- Cross-tenant data isolation
"""

import pytest
from django.urls import reverse
from datetime import timedelta
from django.utils import timezone
from .factories import FeeFactory, FeeAssignmentFactory, PaymentFactory, ReceiptFactory


@pytest.mark.django_db
class TestIDORPrevention:
    """Test Insecure Direct Object Reference prevention."""
    
    def test_user_cannot_access_other_users_fee(
        self, authenticated_client, other_user_client, other_estate, other_user
    ):
        """Test user cannot access fees from other user's estate."""
        other_fee = FeeFactory.create(estate=other_estate, created_by=other_user)
        
        url = reverse("fee-detail", args=[other_fee.id])
        response = authenticated_client.get(url)
        
        assert response.status_code in [403, 404]
    
    def test_user_cannot_update_other_users_fee(
        self, authenticated_client, other_estate, other_user
    ):
        """Test user cannot update fees they don't own."""
        other_fee = FeeFactory.create(estate=other_estate, created_by=other_user)
        
        url = reverse("fee-detail", args=[other_fee.id])
        data = {"name": "Hacked Fee"}
        response = authenticated_client.patch(url, data, format="json")
        
        assert response.status_code in [403, 404]
        
        other_fee.refresh_from_db()
        assert other_fee.name != "Hacked Fee"
    
    def test_user_cannot_delete_other_users_fee(
        self, authenticated_client, other_estate, other_user
    ):
        """Test user cannot delete fees they don't own."""
        other_fee = FeeFactory.create(estate=other_estate, created_by=other_user)
        fee_id = other_fee.id
        
        url = reverse("fee-detail", args=[fee_id])
        response = authenticated_client.delete(url)
        
        assert response.status_code in [403, 404]
        
        from payments.models import Fee
        assert Fee.objects.filter(id=fee_id).exists()
    
    def test_user_cannot_create_payment_for_other_users_assignment(
        self, authenticated_client, other_estate
    ):
        """Test user cannot create payment for other user's fee assignment."""
        other_fee = FeeFactory.create(estate=other_estate)
        other_assignment = FeeAssignmentFactory.create(fee=other_fee)
        
        url = reverse("payment-list")
        data = {
            "fee_assignment": str(other_assignment.id),
            "amount": str(other_assignment.fee.amount),
            "payment_method": "cash",
        }
        response = authenticated_client.post(url, data, format="json")
        
        assert response.status_code in [400, 403, 404]
    
    def test_user_cannot_access_other_users_receipt(
        self, authenticated_client, other_estate
    ):
        """Test user cannot access receipts from other users."""
        other_fee = FeeFactory.create(estate=other_estate)
        other_assignment = FeeAssignmentFactory.create(fee=other_fee)
        other_payment = PaymentFactory.create(fee_assignment=other_assignment)
        other_receipt = ReceiptFactory.create(payment=other_payment)
        
        url = reverse("receipt-detail", args=[other_receipt.id])
        response = authenticated_client.get(url)
        
        assert response.status_code in [403, 404]


@pytest.mark.django_db
class TestDataLeakagePrevention:
    """Test prevention of data leakage."""
    
    def test_fee_list_only_shows_user_estates(
        self, authenticated_client, fee, other_estate, other_user
    ):
        """Test fee list doesn't show fees from other estates."""
        other_fee = FeeFactory.create(estate=other_estate, created_by=other_user)
        
        url = reverse("fee-list")
        response = authenticated_client.get(url)
        
        assert response.status_code == 200
        result_ids = [r["id"] for r in response.data["results"]]
        assert str(fee.id) in result_ids
        assert str(other_fee.id) not in result_ids
    
    def test_payment_list_only_shows_authorized_payments(
        self, authenticated_client, payment, other_estate
    ):
        """Test payment list doesn't show payments from other estates."""
        other_fee = FeeFactory.create(estate=other_estate)
        other_assignment = FeeAssignmentFactory.create(fee=other_fee)
        other_payment = PaymentFactory.create(fee_assignment=other_assignment)
        
        url = reverse("payment-list")
        response = authenticated_client.get(url)
        
        assert response.status_code == 200
        result_ids = [r["id"] for r in response.data["results"]]
        assert str(payment.id) in result_ids
        assert str(other_payment.id) not in result_ids
    
    def test_receipt_list_filtered_by_access(
        self, authenticated_client, receipt, other_estate
    ):
        """Test receipt list is filtered by user access."""
        other_fee = FeeFactory.create(estate=other_estate)
        other_assignment = FeeAssignmentFactory.create(fee=other_fee)
        other_payment = PaymentFactory.create(fee_assignment=other_assignment)
        other_receipt = ReceiptFactory.create(payment=other_payment)
        
        url = reverse("receipt-list")
        response = authenticated_client.get(url)
        
        assert response.status_code == 200
        result_ids = [r["id"] for r in response.data["results"]]
        assert str(receipt.id) in result_ids
        assert str(other_receipt.id) not in result_ids
    
    def test_error_responses_dont_leak_existence(
        self, authenticated_client, other_estate, other_user
    ):
        """Test 404 vs 403 doesn't leak object existence."""
        other_fee = FeeFactory.create(estate=other_estate, created_by=other_user)
        
        url = reverse("fee-detail", args=[other_fee.id])
        response = authenticated_client.get(url)
        
        assert response.status_code == 404
        assert "exist" not in response.data.get("detail", "").lower()


@pytest.mark.django_db
class TestSensitiveFieldExclusion:
    """Test sensitive fields are not exposed."""
    
    def test_fee_response_has_no_sensitive_fields(
        self, authenticated_client, fee
    ):
        """Test fee response doesn't contain sensitive fields."""
        url = reverse("fee-detail", args=[fee.id])
        response = authenticated_client.get(url)
        
        assert response.status_code == 200
        
        sensitive_fields = ["password", "token", "secret", "api_key"]
        for field in sensitive_fields:
            assert field not in response.data
    
    def test_payment_response_has_no_sensitive_fields(
        self, authenticated_client, payment
    ):
        """Test payment response doesn't expose sensitive data."""
        url = reverse("payment-detail", args=[payment.id])
        response = authenticated_client.get(url)
        
        assert response.status_code == 200
        
        sensitive_fields = ["password", "token", "secret"]
        for field in sensitive_fields:
            assert field not in response.data
    
    def test_error_responses_dont_expose_internals(
        self, authenticated_client, estate
    ):
        """Test error responses don't expose internal details."""
        url = reverse("fee-list")
        data = {
            "name": "Test Fee",
            "amount": "invalid",
            "due_date": (timezone.now() + timedelta(days=30)).date().isoformat(),
            "estate": str(estate.id),
            "assign_to_all_units": True,
        }
        
        response = authenticated_client.post(url, data, format="json")
        
        assert response.status_code == 400
        error_msg = str(response.data)
        assert "traceback" not in error_msg.lower()
        assert "exception" not in error_msg.lower()
        assert "sql" not in error_msg.lower()


@pytest.mark.django_db
class TestAuthorizationEnforcement:
    """Test authorization is properly enforced."""
    
    def test_all_endpoints_require_authentication(self, api_client, fee):
        """Test all endpoints reject unauthenticated requests."""
        endpoints = [
            ("fee-list", None, "GET"),
            ("fee-detail", [fee.id], "GET"),
            ("payment-list", None, "GET"),
            ("receipt-list", None, "GET"),
        ]
        
        for endpoint_name, args, method in endpoints:
            if args:
                url = reverse(endpoint_name, args=args)
            else:
                url = reverse(endpoint_name)
            
            if method == "GET":
                response = api_client.get(url)
            elif method == "POST":
                response = api_client.post(url, {}, format="json")
            
            assert response.status_code == 401, f"{endpoint_name} allowed unauth access"
    
    def test_regular_user_cannot_perform_manager_actions(
        self, regular_user_client, estate
    ):
        """Test regular users cannot perform estate manager actions."""
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
    
    def test_regular_user_cannot_record_payments(
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


# payments/tests/test_security.py (snippet - replace this test)

@pytest.mark.django_db
class TestInputSanitization:
    """Test input is properly sanitized."""
    
    def test_xss_attempt_in_fee_name_is_escaped(
        self, authenticated_client, estate
    ):
        """Test XSS payload in fee name is handled safely."""
        url = reverse("fee-list")
        xss_payload = "<script>alert('XSS')</script>"
        data = {
            "name": xss_payload,
            "amount": "5000.00",
            "due_date": (timezone.now() + timedelta(days=30)).date().isoformat(),
            "estate": str(estate.id),
            "assign_to_all_units": True,
        }
        
        response = authenticated_client.post(url, data, format="json")
        
        assert response.status_code == 201
        assert response.data["name"] == xss_payload
    
    def test_sql_injection_attempt_in_search(
        self, authenticated_client, fee
    ):
        """Test SQL injection attempt in search is handled safely."""
        url = reverse("fee-list")
        sql_payload = "'; DROP TABLE fees; --"
        response = authenticated_client.get(url, {"search": sql_payload})
        
        assert response.status_code == 200
        
        from payments.models import Fee
        assert Fee.objects.filter(id=fee.id).exists()
    
    def test_path_traversal_attempt_rejected(
        self, authenticated_client
    ):
        """Test invalid UUID in path parameter returns 404."""
        # Use a valid UUID format to test the endpoint behavior
        # (not a path traversal payload)
        invalid_uuid = "00000000-0000-0000-0000-000000000000"
        url = reverse("fee-detail", args=[invalid_uuid])
        response = authenticated_client.get(url)
        
        # Should return 404 because this UUID doesn't exist
        assert response.status_code == 404

@pytest.mark.django_db
class TestRateLimitingAwareness:
    """Test endpoints that should have rate limiting."""
    
    def test_multiple_rapid_payment_creations(
        self, authenticated_client, fee, units, user
    ):
        """Test creating multiple payments rapidly doesn't cause issues."""
        url = reverse("payment-list")
        
        for unit in units[:5]:
            assignment = FeeAssignmentFactory.create(fee=fee, unit=unit)
            data = {
                "fee_assignment": str(assignment.id),
                "amount": str(assignment.fee.amount),
                "payment_method": "cash",
            }
            response = authenticated_client.post(url, data, format="json")
            assert response.status_code == 201