# tests/conftest.py
"""
Pytest fixtures for units app tests.

Provides reusable fixtures for authentication, clients, and common test data.
"""

import pytest
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import RefreshToken
from .factories import UserFactory, UnitFactory, EstateFactory


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
    """API client authenticated as standard user using force_authenticate."""
    client = APIClient()
    client.force_authenticate(user=user)
    return client


@pytest.fixture
def other_user(db):
    """Another user for cross-user access tests."""
    return UserFactory.create()


@pytest.fixture
def other_user_client(other_user):
    """API client authenticated as other_user."""
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
    """API client with JWT authentication header."""
    client = APIClient()
    client.credentials(HTTP_AUTHORIZATION=f"Bearer {jwt_token}")
    return client


@pytest.fixture
def unit(user):
    """A unit owned by the authenticated user."""
    return UnitFactory.create(owner=user)


@pytest.fixture
def other_users_unit(other_user):
    """A unit owned by other_user for cross-user access tests."""
    return UnitFactory.create(owner=other_user)


@pytest.fixture
def multiple_units(user):
    """Multiple units owned by the authenticated user."""
    return UnitFactory.create_batch(5, owner=user)


@pytest.fixture
def occupied_unit(user):
    """An occupied unit with occupant information."""
    return UnitFactory.create(
        owner=user,
        is_occupied=True,
        occupant_name="John Doe",
        occupant_phone="+1234567890"
    )


@pytest.fixture
def vacant_unit(user):
    """A vacant unit without occupant information."""
    return UnitFactory.create(
        owner=user,
        is_occupied=False,
        occupant_name=None,
        occupant_phone=None
    )


@pytest.fixture
def inactive_unit(user):
    """An inactive unit."""
    return UnitFactory.create(owner=user, is_active=False)

@pytest.fixture
def user_estate(authenticated_user):
    return EstateFactory.create(manager=authenticated_user)  