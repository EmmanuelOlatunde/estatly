# tests/helpers.py

"""
Shared test utilities for payments app.

Provides common assertion helpers and data builders.
"""

from rest_framework.test import APIClient


def assert_response_has_keys(response_data, required_keys):
    """Assert response contains all required keys."""
    for key in required_keys:
        assert key in response_data, f"Missing key: {key}"


def assert_error_response(response, status_code=400, field=None):
    """Assert response is an error with optional field check."""
    assert response.status_code == status_code
    if field:
        assert field in response.data, f"Expected error for field: {field}"


def assert_pagination_response(response_data):
    """Assert response has pagination structure."""
    required_keys = ["count", "next", "previous", "results"]
    assert_response_has_keys(response_data, required_keys)
    assert isinstance(response_data["results"], list)


def create_authenticated_client(user):
    """Create an authenticated API client for a user."""
    client = APIClient()
    client.force_authenticate(user=user)
    return client


def assert_fee_response_structure(fee_data):
    """Assert fee response has correct structure."""
    required_keys = [
        "id",
        "name",
        "description",
        "amount",
        "due_date",
        "estate",
        "estate_name",
        "created_by",
        "created_by_name",
        "total_assigned_units",
        "total_paid_count",
        "total_unpaid_count",
        "created_at",
        "updated_at",
    ]
    assert_response_has_keys(fee_data, required_keys)


def assert_fee_assignment_response_structure(assignment_data):
    """Assert fee assignment response has correct structure."""
    required_keys = [
        "id",
        "fee",
        "fee_name",
        "fee_amount",
        "fee_due_date",
        "unit",
        "unit_identifier",
        "status",
        "has_payment",
        "created_at",
        "updated_at",
    ]
    assert_response_has_keys(assignment_data, required_keys)


def assert_payment_response_structure(payment_data):
    """Assert payment response has correct structure."""
    required_keys = [
        "id",
        "fee_assignment",
        "fee_name",
        "unit_identifier",
        "estate_name",
        "amount",
        "payment_method",
        "payment_date",
        "recorded_by",
        "recorded_by_name",
        "has_receipt",
        "created_at",
        "updated_at",
    ]
    assert_response_has_keys(payment_data, required_keys)


def assert_receipt_response_structure(receipt_data):
    """Assert receipt response has correct structure."""
    required_keys = [
        "id",
        "receipt_number",
        "payment",
        "payment_id",
        "estate_name",
        "unit_identifier",
        "fee_name",
        "amount",
        "payment_date",
        "payment_method",
        "issued_at",
    ]
    assert_response_has_keys(receipt_data, required_keys)


def assert_no_sensitive_fields(response_data, sensitive_fields=None):
    """Assert response does not contain sensitive fields."""
    if sensitive_fields is None:
        sensitive_fields = ["password", "token", "secret"]
    
    for field in sensitive_fields:
        assert field not in response_data, f"Sensitive field exposed: {field}"