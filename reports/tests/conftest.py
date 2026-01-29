# reports/tests/conftest.py
"""
Pytest fixtures for reports app tests.

Provides reusable fixtures for authentication, test data, and API clients.
"""

import pytest
from decimal import Decimal
from datetime import date, timedelta
from rest_framework.test import APIClient
from django.utils import timezone
import factory

from payments.models import FeeAssignment

from .factories import (
    UserFactory,
    EstateFactory,
    UnitFactory,
    FeeFactory,
    PaymentFactory,
    FeeAssignmentFactory
)


@pytest.fixture
def api_client():
    """Unauthenticated API client."""
    return APIClient()


@pytest.fixture
def super_admin_user(db):
    """Super admin user for permission tests."""
    return UserFactory.create(is_superuser=True, role='super_admin')


@pytest.fixture
def estate_manager_user(db):
    """Estate manager user with assigned estate."""
    estate = EstateFactory.create()
    return UserFactory.create(role='estate_manager', estate_id=estate.id)


@pytest.fixture
def estate_manager_user_no_estate(db):
    """Estate manager user without assigned estate."""
    return UserFactory.create(role='estate_manager', estate_id=None)


@pytest.fixture
def other_estate_manager_user(db):
    """Another estate manager for cross-user access tests."""
    estate = EstateFactory.create()
    return UserFactory.create(role='estate_manager', estate_id=estate.id)


@pytest.fixture
def tenant_user(db):
    """Standard tenant user."""
    return UserFactory.create(role='tenant')


@pytest.fixture
def admin_user(db):
    """Admin/superuser for permission tests."""
    return UserFactory.create(is_staff=True, is_superuser=True)


@pytest.fixture
def super_admin_client(super_admin_user):
    """API client authenticated as super admin."""
    client = APIClient()
    client.force_authenticate(user=super_admin_user)
    return client


@pytest.fixture
def estate_manager_client(estate_manager_user):
    """API client authenticated as estate manager."""
    client = APIClient()
    client.force_authenticate(user=estate_manager_user)
    return client


@pytest.fixture
def estate_manager_no_estate_client(estate_manager_user_no_estate):
    """API client authenticated as estate manager without estate."""
    client = APIClient()
    client.force_authenticate(user=estate_manager_user_no_estate)
    return client


@pytest.fixture
def other_estate_manager_client(other_estate_manager_user):
    """API client authenticated as another estate manager."""
    client = APIClient()
    client.force_authenticate(user=other_estate_manager_user)
    return client


@pytest.fixture
def tenant_client(tenant_user):
    """API client authenticated as tenant."""
    client = APIClient()
    client.force_authenticate(user=tenant_user)
    return client


@pytest.fixture
def admin_client(admin_user):
    """API client authenticated as admin."""
    client = APIClient()
    client.force_authenticate(user=admin_user)
    return client


@pytest.fixture
def jwt_token(estate_manager_user):
    """JWT token for estate manager user."""
    from rest_framework_simplejwt.tokens import RefreshToken
    refresh = RefreshToken.for_user(estate_manager_user)
    return str(refresh.access_token)


@pytest.fixture
def jwt_client(jwt_token):
    """API client with JWT authentication."""
    client = APIClient()
    client.credentials(HTTP_AUTHORIZATION=f'Bearer {jwt_token}')
    return client


@pytest.fixture
def estate(estate_manager_user):
    """
    Return the estate already assigned to the estate manager.
    Do NOT create a new one.
    """
    return estate_manager_user.estate


@pytest.fixture
def other_estate(other_estate_manager_user):
    """
    Return the estate already assigned to the other estate manager.
    """
    return other_estate_manager_user.estate



@pytest.fixture
def unassigned_estate(db):
    """Create an estate not assigned to any manager."""
    return EstateFactory.create()


@pytest.fixture
def units(estate):
    """Create multiple units in the estate."""
    return [
        UnitFactory.create(estate=estate, is_occupied=True) for _ in range(5)
    ]


@pytest.fixture
def fee(estate):
    """Create a fee for the estate."""
    return FeeFactory.create(
        estate=estate,
        amount=Decimal('1000.00'),
        due_date=date.today() + timedelta(days=7)
    )


@pytest.fixture
def overdue_fee(estate):
    """Create an overdue fee."""
    return FeeFactory.create(
        estate=estate,
        amount=Decimal('500.00'),
        due_date=date.today() - timedelta(days=10)
    )


# reports/tests/conftest.py

@pytest.fixture
def payments(fee, units):
    """Create payments for some units."""
    payments_list = []
    for i in range(3):
        # First create the assignment
        assignment = FeeAssignmentFactory.create(
            fee=fee,
            unit=units[i],
            status=FeeAssignment.PaymentStatus.PAID
        )
        # Then create payment for that assignment
        payment = PaymentFactory.create(
            fee_assignment=assignment,
            amount=fee.amount
        )
        payments_list.append(payment)
    
    return payments_list

@pytest.fixture
def estate_with_complete_data(estate_manager_user):
    estate = EstateFactory.create()
    estate_manager_user.estate = estate
    estate_manager_user.save()

    units = [UnitFactory.create(estate=estate, is_occupied=True) for _ in range(10)]

    fee1 = FeeFactory.create(estate=estate)
    fee2 = FeeFactory.create(estate=estate)

    # 7 paid for fee1
    for i in range(7):
        assignment = FeeAssignmentFactory.create(
            fee=fee1,
            unit=units[i],
            status=FeeAssignment.PaymentStatus.PAID
        )
        PaymentFactory.create(fee_assignment=assignment)

    # 5 paid for fee2
    for i in range(5):
        assignment = FeeAssignmentFactory.create(
            fee=fee2,
            unit=units[i],
            status=FeeAssignment.PaymentStatus.PAID
        )
        PaymentFactory.create(fee_assignment=assignment)

    return {
        "estate": estate,
        "units": units,
        "fees": [fee1, fee2],
        "fee1": fee1,
        "fee2": fee2,
    }

@pytest.fixture
def super_admin_jwt_token(super_admin_user):
    """JWT token for super admin user."""
    from rest_framework_simplejwt.tokens import RefreshToken
    refresh = RefreshToken.for_user(super_admin_user)
    return str(refresh.access_token)


@pytest.fixture
def super_admin_jwt_client(super_admin_jwt_token):
    """API client with JWT authentication for super admin."""
    client = APIClient()
    client.credentials(HTTP_AUTHORIZATION=f'Bearer {super_admin_jwt_token}')
    return client


@pytest.fixture
def tenant_jwt_token(tenant_user):
    """JWT token for tenant user."""
    from rest_framework_simplejwt.tokens import RefreshToken
    refresh = RefreshToken.for_user(tenant_user)
    return str(refresh.access_token)


@pytest.fixture
def tenant_jwt_client(tenant_jwt_token):
    """API client with JWT authentication for tenant."""
    client = APIClient()
    client.credentials(HTTP_AUTHORIZATION=f'Bearer {tenant_jwt_token}')
    return client