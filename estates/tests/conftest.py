
# tests/conftest.py
"""
Global fixtures for estates app tests.
"""

import pytest
from rest_framework.test import APIClient
from django.contrib.auth import get_user_model
from .factories import UserFactory, EstateFactory

User = get_user_model()


@pytest.fixture
def api_client():
    """Unauthenticated API client."""
    return APIClient()


@pytest.fixture
def user(db):
    """Standard authenticated user (non-staff)."""
    return UserFactory.create()


@pytest.fixture
def authenticated_client(user):
    """API client authenticated as standard user."""
    client = APIClient()
    client.force_authenticate(user=user)
    return client


@pytest.fixture
def other_user(db):
    """Another user for cross-user access tests."""
    return UserFactory.create()


@pytest.fixture
def staff_user(db):
    """Staff user with elevated permissions."""
    return UserFactory.create(is_staff=True, is_superuser=False)


@pytest.fixture
def staff_client(staff_user):
    """API client authenticated as staff user."""
    client = APIClient()
    client.force_authenticate(user=staff_user)
    return client


@pytest.fixture
def admin_user(db):
    """Admin/superuser for permission tests."""
    return UserFactory.create(is_staff=True, is_superuser=True)


@pytest.fixture
def admin_client(admin_user):
    """API client authenticated as admin."""
    client = APIClient()
    client.force_authenticate(user=admin_user)
    return client


@pytest.fixture
def estate(db):
    """Single estate instance."""
    return EstateFactory.create()


@pytest.fixture
def estates(db):
    """Multiple estate instances."""
    return EstateFactory.create_batch(5)


@pytest.fixture
def inactive_estate(db):
    """Inactive estate instance."""
    return EstateFactory.create(is_active=False)