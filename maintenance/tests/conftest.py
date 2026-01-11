# tests/conftest.py

"""
Global pytest fixtures for maintenance app tests.

Provides reusable fixtures for authentication, API clients, and test data.
"""

import pytest
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import RefreshToken
from .factories import UserFactory, MaintenanceTicketFactory, EstateFactory, UnitFactory


@pytest.fixture
def api_client():
    """Unauthenticated API client."""
    return APIClient()


@pytest.fixture
def user(db):
    """Standard authenticated user."""
    return UserFactory.create()


@pytest.fixture
def authenticated_user(db):
    """Alias for user fixture for clarity."""
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
def jwt_token(authenticated_user):
    """JWT token for authenticated user."""
    refresh = RefreshToken.for_user(authenticated_user)
    return str(refresh.access_token)


@pytest.fixture
def jwt_client(jwt_token):
    """API client with JWT authentication."""
    client = APIClient()
    client.credentials(HTTP_AUTHORIZATION=f"Bearer {jwt_token}")
    return client


@pytest.fixture
def estate(db):
    """Create a test estate."""
    return EstateFactory.create()


@pytest.fixture
def unit(db, estate):
    """Create a test unit within an estate."""
    return UnitFactory.create(estate=estate)


@pytest.fixture
def ticket(db, authenticated_user, estate):
    """Create a test maintenance ticket."""
    return MaintenanceTicketFactory.create(
        created_by=authenticated_user,
        estate=estate
    )


@pytest.fixture
def other_user_ticket(db, other_user, estate):
    """Create a ticket owned by other user."""
    return MaintenanceTicketFactory.create(
        created_by=other_user,
        estate=estate
    )


@pytest.fixture
def multiple_tickets(db, authenticated_user, estate):
    """Create multiple tickets for list/filter tests."""
    return MaintenanceTicketFactory.create_batch(
        5,
        created_by=authenticated_user,
        estate=estate
    )


@pytest.fixture
def resolved_ticket(db, authenticated_user, estate):
    """Create a resolved maintenance ticket."""
    from django.utils import timezone
    return MaintenanceTicketFactory.create(
        created_by=authenticated_user,
        estate=estate,
        status='RESOLVED',
        resolved_at=timezone.now()
    )