# tests/conftest.py
"""
Global test fixtures for accounts app.
"""

import pytest
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import RefreshToken

from .factories import UserFactory


@pytest.fixture
def api_client():
    """Unauthenticated API client."""
    return APIClient()


@pytest.fixture
def user(db):
    """Standard authenticated user (estate manager)."""
    return UserFactory.create()


@pytest.fixture
def authenticated_user(db):
    """Standard authenticated user (estate manager)."""
    return UserFactory.create()


@pytest.fixture
def authenticated_client(authenticated_user):
    """API client authenticated as standard user."""
    client = APIClient()
    client.force_authenticate(user=authenticated_user)
    return client


@pytest.fixture
def other_user(db):
    """Another user for cross-user access tests."""
    return UserFactory.create()


@pytest.fixture
def super_admin(db):
    """Super admin user."""
    return UserFactory.create(
        role='SUPER_ADMIN',
        is_staff=True,
        is_superuser=True
    )


@pytest.fixture
def super_admin_client(super_admin):
    """API client authenticated as super admin."""
    client = APIClient()
    client.force_authenticate(user=super_admin)
    return client


@pytest.fixture
def jwt_token(authenticated_user):
    """JWT access token for authenticated user."""
    refresh = RefreshToken.for_user(authenticated_user)
    return str(refresh.access_token)


@pytest.fixture
def jwt_refresh_token(authenticated_user):
    """JWT refresh token for authenticated user."""
    refresh = RefreshToken.for_user(authenticated_user)
    return str(refresh)


@pytest.fixture
def jwt_client(jwt_token):
    """API client with JWT authentication."""
    client = APIClient()
    client.credentials(HTTP_AUTHORIZATION=f'Bearer {jwt_token}')
    return client


@pytest.fixture
def inactive_user(db):
    """Inactive user for testing deactivation."""
    return UserFactory.create(is_active=False)


@pytest.fixture
def multiple_users(db):
    """Create multiple users for list/pagination tests."""
    return UserFactory.create_batch(10)