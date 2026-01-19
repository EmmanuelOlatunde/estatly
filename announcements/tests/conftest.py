# tests/conftest.py

"""
Global pytest fixtures for announcements app tests.

Provides fixtures for:
- API clients (authenticated and unauthenticated)
- Users (standard, admin, other users)
- JWT tokens
- Common test data
"""

import pytest
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import RefreshToken
from .factories import UserFactory, AnnouncementFactory


@pytest.fixture
def api_client():
    """Unauthenticated API client."""
    return APIClient()


@pytest.fixture
def authenticated_user(db):
    """Standard authenticated user (manager/staff)."""
    return UserFactory.create(is_staff=True)


@pytest.fixture
def authenticated_client(authenticated_user):
    """API client authenticated as standard user."""
    client = APIClient()
    client.force_authenticate(user=authenticated_user)
    return client


@pytest.fixture
def regular_user(db):
    """Regular user without manager privileges."""
    return UserFactory.create(is_staff=False)


@pytest.fixture
def regular_client(regular_user):
    """API client authenticated as regular user."""
    client = APIClient()
    client.force_authenticate(user=regular_user)
    return client


@pytest.fixture
def other_user(db):
    """Another manager user for cross-user access tests."""
    return UserFactory.create(is_staff=True)


@pytest.fixture
def other_client(other_user):
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
    """JWT access token for authenticated user."""
    refresh = RefreshToken.for_user(authenticated_user)
    return str(refresh.access_token)


@pytest.fixture
def jwt_client(jwt_token):
    """API client with JWT authentication."""
    client = APIClient()
    client.credentials(HTTP_AUTHORIZATION=f"Bearer {jwt_token}")
    return client


@pytest.fixture
def announcement(authenticated_user):
    """Create a single announcement owned by authenticated user."""
    return AnnouncementFactory.create(created_by=authenticated_user)


@pytest.fixture
def inactive_announcement(authenticated_user):
    """Create an inactive announcement."""
    return AnnouncementFactory.create(created_by=authenticated_user, is_active=False)


@pytest.fixture
def other_user_announcement(other_user):
    """Create an announcement owned by other user."""
    return AnnouncementFactory.create(created_by=other_user)


@pytest.fixture
def announcement_list(authenticated_user):
    """Create multiple announcements for list tests."""
    return [AnnouncementFactory.create(created_by=authenticated_user) for _ in range(5)]


@pytest.fixture
def mixed_announcements(authenticated_user, other_user):
    """Create announcements from multiple users."""
    return {
        'own': [AnnouncementFactory.create(created_by=authenticated_user) for _ in range(3)],
        'other': [AnnouncementFactory.create(created_by=other_user) for _ in range(3)],
    }