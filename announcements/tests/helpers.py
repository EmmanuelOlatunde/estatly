# tests/helpers.py

"""
Shared test utilities and helper functions.
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
        field: Optional field name to check in error response
    """
    assert response.status_code == status_code
    if field:
        assert field in response.data, f"Expected error for field: {field}"


def create_authenticated_client(user):
    """
    Create an authenticated API client for a user.
    
    Args:
        user: User instance
    
    Returns:
        Authenticated APIClient
    """
    client = APIClient()
    client.force_authenticate(user=user)
    return client


def assert_announcement_matches_data(announcement_data, expected_announcement):
    """
    Assert announcement data matches expected announcement.
    
    Args:
        announcement_data: Announcement data from response
        expected_announcement: Expected Announcement instance
    """
    assert announcement_data['id'] == str(expected_announcement.id)
    assert announcement_data['title'] == expected_announcement.title
    assert announcement_data['message'] == expected_announcement.message
    assert announcement_data['is_active'] == expected_announcement.is_active
    assert 'created_by' in announcement_data
    assert 'created_at' in announcement_data
    assert 'updated_at' in announcement_data


def assert_announcement_list_response(response, expected_count=None):
    """
    Assert announcement list response structure.
    
    Args:
        response: DRF Response object
        expected_count: Optional expected count of results
    """
    assert response.status_code == 200
    assert 'results' in response.data
    
    if expected_count is not None:
        assert len(response.data['results']) == expected_count


def assert_no_sensitive_fields(data, sensitive_fields=None):
    """
    Assert response doesn't contain sensitive fields.
    
    Args:
        data: Response data
        sensitive_fields: List of sensitive field names
    """
    if sensitive_fields is None:
        sensitive_fields = ['password', 'token', 'secret', 'api_key']
    
    for field in sensitive_fields:
        assert field not in data, f"Sensitive field exposed: {field}"