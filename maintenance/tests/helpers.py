# tests/helpers.py

"""
Shared test utilities and helper functions.

Provides reusable assertion helpers and data builders for tests.
"""

from rest_framework.test import APIClient


def assert_response_has_keys(response_data, required_keys):
    """
    Assert response contains all required keys.
    
    Args:
        response_data: Response data dictionary
        required_keys: List of required key names
    """
    for key in required_keys:
        assert key in response_data, f"Missing key: {key}"


def assert_error_response(response, status_code=400, field=None):
    """
    Assert response is an error with optional field check.
    
    Args:
        response: DRF Response object
        status_code: Expected status code
        field: Optional field name to check in errors
    """
    assert response.status_code == status_code
    if field:
        assert field in response.data, f"Expected error for field: {field}"


def assert_pagination_response(response_data):
    """
    Assert response has correct pagination structure.
    
    Args:
        response_data: Response data dictionary
    """
    assert_response_has_keys(response_data, ['count', 'next', 'previous', 'results'])
    assert isinstance(response_data['results'], list)
    assert isinstance(response_data['count'], int)


def create_authenticated_client(user):
    """
    Create an authenticated API client for a user.
    
    Args:
        user: User instance to authenticate
        
    Returns:
        Authenticated APIClient
    """
    client = APIClient()
    client.force_authenticate(user=user)
    return client


def assert_ticket_data_matches(response_data, ticket):
    """
    Assert ticket response data matches ticket model instance.
    
    Args:
        response_data: Response data dictionary
        ticket: MaintenanceTicket instance
    """
    assert response_data['id'] == str(ticket.id)
    assert response_data['title'] == ticket.title
    assert response_data['description'] == ticket.description
    assert response_data['category'] == ticket.category
    assert response_data['status'] == ticket.status
    assert response_data['estate_name'] == ticket.estate.name


def assert_no_sensitive_data_in_response(response_data):
    """
    Assert response does not contain sensitive fields.
    
    Args:
        response_data: Response data dictionary or list
    """
    if isinstance(response_data, list):
        for item in response_data:
            assert_no_sensitive_data_in_response(item)
    elif isinstance(response_data, dict):
        sensitive_fields = ['password', 'token', 'secret', 'api_key']
        for field in sensitive_fields:
            assert field not in response_data, f"Sensitive field exposed: {field}"