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
        status_code: Expected HTTP status code
        field: Optional field name to check in error response
    """
    assert response.status_code == status_code
    if field:
        assert field in response.data


def assert_paginated_response(response, expected_count=None):
    """
    Assert response is a paginated DRF response.
    
    Args:
        response: DRF Response object
        expected_count: Optional expected count of results
    """
    assert response.status_code == 200
    assert "results" in response.data
    assert "count" in response.data
    if expected_count is not None:
        assert response.data["count"] == expected_count


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


def get_unit_list_url():
    """Get URL for unit list endpoint."""
    from django.urls import reverse
    return reverse("units:unit-list")


def get_unit_detail_url(unit_id):
    """Get URL for unit detail endpoint."""
    from django.urls import reverse
    return reverse("units:unit-detail", args=[unit_id])


def get_unit_occupied_url():
    """Get URL for occupied units endpoint."""
    from django.urls import reverse
    return reverse("units:unit-occupied")


def get_unit_vacant_url():
    """Get URL for vacant units endpoint."""
    from django.urls import reverse
    return reverse("units:unit-vacant")


def get_unit_deactivate_url(unit_id):
    """Get URL for deactivate unit endpoint."""
    from django.urls import reverse
    return reverse("units:unit-deactivate", args=[unit_id])


def get_unit_activate_url(unit_id):
    """Get URL for activate unit endpoint."""
    from django.urls import reverse
    return reverse("units:unit-activate", args=[unit_id])


def get_unit_update_occupancy_url(unit_id):
    """Get URL for update occupancy endpoint."""
    from django.urls import reverse
    return reverse("units:unit-update-occupancy", args=[unit_id])