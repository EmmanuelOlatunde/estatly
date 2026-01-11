

# tests/helpers.py
"""
Shared test utilities for estates app.
"""

from rest_framework.test import APIClient


def assert_response_keys(response_data, required_keys):
    """Assert response contains all required keys."""
    for key in required_keys:
        assert key in response_data, f"Missing key: {key}"


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


def get_estate_list_url():
    """Get URL for estate list endpoint."""
    from django.urls import reverse
    return reverse("estates:estates-list")


def get_estate_detail_url(estate_id):
    """Get URL for estate detail endpoint."""
    from django.urls import reverse
    return reverse("estates:estates-detail", args=[estate_id])


def get_estate_activate_url(estate_id):
    """Get URL for estate activate action."""
    from django.urls import reverse
    return reverse("estates:estates-activate", args=[estate_id])


def get_estate_deactivate_url(estate_id):
    """Get URL for estate deactivate action."""
    from django.urls import reverse
    return reverse("estates:estates-deactivate", args=[estate_id])


def get_estate_statistics_url():
    """Get URL for estate statistics action."""
    from django.urls import reverse
    return reverse("estates:estates-statistics")


def get_estate_by_type_url(estate_type):
    """Get URL for estate by-type action."""
    from django.urls import reverse
    return reverse("estates:estates-by-type", args=[estate_type])

