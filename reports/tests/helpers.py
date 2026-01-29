# reports/tests/helpers.py
"""
Shared test utilities and helper functions.

Provides reusable assertion helpers and data builders.
"""

from decimal import Decimal


def assert_response_has_keys(response_data, required_keys):
    """
    Assert response contains all required keys.
    
    Args:
        response_data: Response data dictionary
        required_keys: List of required key names
    """
    for key in required_keys:
        assert key in response_data, f'Missing key: {key}'


def assert_error_response(response, status_code=400, field=None):
    """
    Assert response is an error with optional field check.
    
    Args:
        response: DRF Response object
        status_code: Expected HTTP status code
        field: Optional field name to check in errors
    """
    assert response.status_code == status_code
    if field:
        assert field in response.data


def assert_fee_payment_status_structure(data):
    """
    Assert fee payment status response has correct structure.
    
    Args:
        data: Response data dictionary
    """
    required_keys = [
        'fee_id', 'fee_name', 'fee_type', 'total_expected',
        'total_collected', 'total_pending', 'payment_rate',
        'total_units', 'paid_units', 'unpaid_units_count',
        'unpaid_units'
    ]
    assert_response_has_keys(data, required_keys)
    
    assert isinstance(data['total_expected'], str) or isinstance(data['total_expected'], Decimal)
    assert isinstance(data['total_collected'], str) or isinstance(data['total_collected'], Decimal)
    assert isinstance(data['total_units'], int)
    assert isinstance(data['paid_units'], int)
    assert isinstance(data['unpaid_units'], list)


def assert_overall_summary_structure(data):
    """
    Assert overall summary response has correct structure.
    
    Args:
        data: Response data dictionary
    """
    required_keys = [
        'total_fees', 'total_expected_all_fees',
        'total_collected_all_fees', 'total_pending_all_fees',
        'overall_payment_rate', 'fees_summary'
    ]
    assert_response_has_keys(data, required_keys)
    
    assert isinstance(data['total_fees'], int)
    assert isinstance(data['fees_summary'], list)


def assert_unpaid_unit_structure(data):
    """
    Assert unpaid unit data has correct structure.
    
    Args:
        data: Unpaid unit dictionary
    """
    required_keys = [
        'unit_id', 'unit_name', 'tenant_name',
        'estate_name', 'amount_due', 'due_date', 'days_overdue'
    ]
    assert_response_has_keys(data, required_keys)


def create_authenticated_client(user):
    """
    Create an authenticated API client for a user.
    
    Args:
        user: User instance
        
    Returns:
        Authenticated APIClient instance
    """
    from rest_framework.test import APIClient
    client = APIClient()
    client.force_authenticate(user=user)
    return client