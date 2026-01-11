# tests/conftest.py

"""
Global fixtures for payments app tests.

Provides authenticated clients, users, and common test data.
"""

import pytest
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import RefreshToken
from .factories import (
    UserFactory,
    EstateFactory,
    UnitFactory,
    FeeFactory,
    FeeAssignmentFactory,
    PaymentFactory,
    ReceiptFactory,
)


@pytest.fixture
def api_client():
    """Unauthenticated API client."""
    return APIClient()


@pytest.fixture
def user(db):
    """Standard authenticated user (estate manager)."""
    return UserFactory.create(is_estate_manager=True)


@pytest.fixture
def authenticated_client(user):
    """API client authenticated as standard user."""
    client = APIClient()
    client.force_authenticate(user=user)
    return client


@pytest.fixture
def other_user(db):
    """Another user for cross-user access tests."""
    return UserFactory.create(is_estate_manager=True)


@pytest.fixture
def other_user_client(other_user):
    """API client authenticated as other user."""
    client = APIClient()
    client.force_authenticate(user=other_user)
    return client


@pytest.fixture
def regular_user(db):
    """Regular user without estate manager permissions."""
    return UserFactory.create(is_estate_manager=False)


@pytest.fixture
def regular_user_client(regular_user):
    """API client authenticated as regular user."""
    client = APIClient()
    client.force_authenticate(user=regular_user)
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
    """JWT token for authenticated user."""
    refresh = RefreshToken.for_user(user)
    return str(refresh.access_token)


@pytest.fixture
def jwt_client(jwt_token):
    """API client with JWT authentication."""
    client = APIClient()
    client.credentials(HTTP_AUTHORIZATION=f"Bearer {jwt_token}")
    return client


@pytest.fixture
def estate(db, user):
    """Create a test estate owned by user."""
    return EstateFactory.create(created_by=user)


@pytest.fixture
def other_estate(db, other_user):
    """Create an estate for other_user."""
    return EstateFactory.create(created_by=other_user)


@pytest.fixture
def units(db, estate):
    """Create 5 units in the estate."""
    return [UnitFactory.create(estate=estate) for _ in range(5)]


@pytest.fixture
def other_units(db, other_estate):
    """Create units in other_estate."""
    return [UnitFactory.create(estate=other_estate) for _ in range(3)]


@pytest.fixture
def fee(db, estate, user):
    """Create a fee for the estate."""
    return FeeFactory.create(estate=estate, created_by=user)


@pytest.fixture
def fee_with_assignments(db, fee, units):
    """Create a fee with assignments to units."""
    for unit in units:
        FeeAssignmentFactory.create(fee=fee, unit=unit)
    return fee


@pytest.fixture
def fee_assignment(db, fee, units):
    """Create a single fee assignment."""
    return FeeAssignmentFactory.create(fee=fee, unit=units[0])


@pytest.fixture
def paid_fee_assignment(db, fee, units, user):
    """Create a paid fee assignment with payment and receipt."""
    assignment = FeeAssignmentFactory.create(
        fee=fee,
        unit=units[0],
        status='paid'
    )
    payment = PaymentFactory.create(
        fee_assignment=assignment,
        amount=fee.amount,
        recorded_by=user
    )
    receipt = ReceiptFactory.create(payment=payment)
    return assignment


@pytest.fixture
def payment(db, fee_assignment, user):
    """Create a payment for a fee assignment."""
    return PaymentFactory.create(
        fee_assignment=fee_assignment,
        amount=fee_assignment.fee.amount,
        recorded_by=user
    )


@pytest.fixture
def receipt(db, payment):
    """Create a receipt for a payment."""
    return ReceiptFactory.create(payment=payment)