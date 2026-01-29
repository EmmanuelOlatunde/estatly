# tests/conftest.py
"""
Global fixtures for documents app tests.
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
    """Standard authenticated user."""
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
def other_user_client(other_user):
    """API client authenticated as other user."""
    client = APIClient()
    client.force_authenticate(user=other_user)
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
def jwt_token(user):
    """JWT access token for authenticated user."""
    refresh = RefreshToken.for_user(user)
    return str(refresh.access_token)


@pytest.fixture
def jwt_client(jwt_token):
    """API client with JWT authentication in headers."""
    client = APIClient()
    client.credentials(HTTP_AUTHORIZATION=f"Bearer {jwt_token}")
    return client


@pytest.fixture
def admin_jwt_token(admin_user):
    """JWT access token for admin user."""
    refresh = RefreshToken.for_user(admin_user)
    return str(refresh.access_token)


@pytest.fixture
def admin_jwt_client(admin_jwt_token):
    """API client with admin JWT authentication."""
    client = APIClient()
    client.credentials(HTTP_AUTHORIZATION=f"Bearer {admin_jwt_token}")
    return client