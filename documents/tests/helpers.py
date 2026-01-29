# tests/helpers.py
"""
Shared test utilities for documents app.
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
        assert key in response_data, f"Missing required key: {key}"


def assert_error_response(response, status_code=400, field=None, message=None):
    """
    Assert response is an error with optional field/message check.
    
    Args:
        response: DRF Response object
        status_code: Expected HTTP status code
        field: Optional field name that should have error
        message: Optional error message substring to check
    """
    assert response.status_code == status_code
    
    if field:
        assert field in response.data, f"Expected error for field: {field}"
    
    if message:
        error_text = str(response.data)
        assert message in error_text, f"Expected message '{message}' in {error_text}"


def create_authenticated_client(user):
    """
    Create an authenticated API client for a user.
    
    Args:
        user: User instance to authenticate
    
    Returns:
        Authenticated APIClient instance
    """
    client = APIClient()
    client.force_authenticate(user=user)
    return client


def assert_document_response_structure(data, full=True):
    """
    Assert document response has correct structure.
    
    Args:
        data: Response data dictionary
        full: Whether to check full or list serializer fields
    """
    required_keys = [
        'id',
        'document_type',
        'document_type_display',
        'title',
        'status',
        'status_display',
        'created_at',
    ]
    
    if full:
        required_keys.extend([
            'file',
            'file_url',
            'related_user',
            'related_user_email',
            'related_payment_id',
            'related_announcement_id',
            'file_size',
            'metadata',
            'error_message',
            'updated_at',
            'generated_at',
            'download_count',
        ])
    else:
        required_keys.extend([
            'file_url',
            'related_user',
            'file_size',
            'generated_at',
        ])
    
    assert_response_has_keys(data, required_keys)


def assert_download_response_structure(data):
    """
    Assert download record response has correct structure.
    
    Args:
        data: Response data dictionary
    """
    required_keys = [
        'id',
        'document',
        'document_title',
        'user',
        'user_email',
        'ip_address',
        'user_agent',
        'downloaded_at',
    ]
    assert_response_has_keys(data, required_keys)


def assert_paginated_response(data, expected_count=None):
    """
    Assert response is properly paginated.
    
    Args:
        data: Response data dictionary
        expected_count: Optional expected count value
    """
    required_keys = ['count', 'next', 'previous', 'results']
    assert_response_has_keys(data, required_keys)
    
    assert isinstance(data['results'], list)
    
    if expected_count is not None:
        assert data['count'] == expected_count