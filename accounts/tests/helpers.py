# tests/helpers.py
"""
Shared test utilities for accounts app tests.
"""

from rest_framework.test import APIClient


def assert_response_has_keys(response_data, required_keys):
    """Assert response contains all required keys."""
    for key in required_keys:
        assert key in response_data, f'Missing key: {key}'


def assert_error_response(response, status_code=400, field=None):
    """Assert response is an error with optional field check."""
    assert response.status_code == status_code
    if field:
        assert field in response.data


def create_authenticated_client(user):
    """Create an authenticated API client for a user."""
    client = APIClient()
    client.force_authenticate(user=user)
    return client


def assert_user_response_structure(user_data):
    """Assert user response has correct structure."""
    required_keys = [
        'id', 'email', 'first_name', 'last_name', 'full_name',
        'role', 'is_active', 'date_joined', 'created_at', 'updated_at'
    ]
    assert_response_has_keys(user_data, required_keys)
    assert 'password' not in user_data
    assert 'tokens' in user_data


def get_user_payload(email='test@example.com', password='TestPass123!', **kwargs):
    """Generate user creation payload."""
    payload = {
        'email': email,
        'first_name': kwargs.get('first_name', 'Test'),
        'last_name': kwargs.get('last_name', 'User'),
        'password': password,
        'password_confirm': password,
        'role': kwargs.get('role', 'ESTATE_MANAGER'),
    }
    payload.update(kwargs)
    return payload