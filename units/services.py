"""
Business logic layer for the units app.

Contains all domain logic for unit management operations.
"""

from typing import Optional, TYPE_CHECKING
from django.contrib.auth import get_user_model
from django.db import transaction
from django.db.models import QuerySet
from django.core.exceptions import ValidationError
from estates.models import Estate
from django.utils import timezone


from .models import Unit
if TYPE_CHECKING:
    from django.contrib.auth.models import AbstractBaseUser

User = get_user_model()


# =====================================================
# Internal helpers (DRY)
# =====================================================

def _assert_owner(unit: Unit, user: "AbstractBaseUser", action: str) -> None:
    if unit.owner_id != user.id:
        raise ValueError(f'Only the unit owner can {action} this unit.')


def _validate_identifier(
    *,
    owner: "AbstractBaseUser",
    identifier: Optional[str],
    exclude_unit_id: Optional[int] = None
) -> str:
    if identifier is None:
        raise ValueError('Unit identifier is required.')

    identifier = identifier.strip()
    if not identifier:
        raise ValueError('Unit identifier cannot be empty.')

    queryset = Unit.objects.filter(owner=owner, identifier=identifier)
    if exclude_unit_id:
        queryset = queryset.exclude(id=exclude_unit_id)

    if queryset.exists():
        raise ValueError(
            f'Unit with identifier "{identifier}" already exists for this owner.'
        )

    return identifier


def _validate_unit_type(unit_type: str) -> None:
    valid_types = {choice[0] for choice in Unit.UnitType.choices}
    if unit_type not in valid_types:
        raise ValueError(f'Invalid unit type. Must be one of: {sorted(valid_types)}')


def _validate_occupancy(
    *,
    is_occupied: bool,
    occupant_name: Optional[str],
    occupant_phone: Optional[str]
) -> None:
    if (occupant_name or occupant_phone) and not is_occupied:
        raise ValueError(
            'Unit must be marked as occupied if occupant info is provided.'
        )

    # if is_occupied and not (occupant_name or occupant_phone):
    #     raise ValueError(
    #         'At least occupant name or phone is required when unit is occupied.'
    #     )


# =====================================================
# Public service functions
# =====================================================

def create_unit(
    *,
    owner: "AbstractBaseUser",
    estate: "Estate",           # ADD THIS PARAMETER
    identifier: str,
    unit_type: str,
    occupant_name: Optional[str] = None,
    occupant_phone: Optional[str] = None,
    description: Optional[str] = None,
    is_occupied: bool = False,
    is_active: bool = True,
) -> Unit:
    """
    Create a new unit.
    
    Args:
        owner: The user who owns this unit
        estate: The estate this unit belongs to (required)
        identifier: Unique identifier for the unit within the owner's units
        unit_type: Type of unit (HOUSE, FLAT, etc.)
        occupant_name: Name of current occupant (optional)
        occupant_phone: Phone number of current occupant (optional)
        description: Additional description (optional)
        is_occupied: Whether the unit is currently occupied
        is_active: Whether the unit is active
        
    Returns:
        The created Unit instance
        
    Raises:
        ValueError: If validation fails
    """
    if not owner:
        raise ValueError('Owner is required.')
    
    if not estate:
        raise ValueError('Estate is required.')

    identifier = _validate_identifier(owner=owner, identifier=identifier)
    _validate_unit_type(unit_type)
    _validate_occupancy(
        is_occupied=is_occupied,
        occupant_name=occupant_name,
        occupant_phone=occupant_phone,
    )

    try:
        with transaction.atomic():
            return Unit.objects.create(
                owner=owner,
                estate=estate,      # ADD THIS LINE
                identifier=identifier,
                unit_type=unit_type,
                occupant_name=occupant_name,
                occupant_phone=occupant_phone,
                description=description,
                is_occupied=is_occupied,
                is_active=is_active,
            )
    except ValidationError as exc:
        raise ValueError(str(exc))


def update_unit(
    *,
    unit: Unit,
    user: "AbstractBaseUser",
    **update_data
) -> Unit:
    """
    Update an existing unit.
    """
    _assert_owner(unit, user, 'update')

    # Identifier
    if 'identifier' in update_data:
        update_data['identifier'] = _validate_identifier(
            owner=user,
            identifier=update_data.get('identifier'),
            exclude_unit_id=unit.id,
        )

    # Unit type
    if 'unit_type' in update_data:
        _validate_unit_type(update_data['unit_type'])

    # Occupancy
    is_occupied = update_data.get('is_occupied', unit.is_occupied)
    occupant_name = update_data.get('occupant_name', unit.occupant_name)
    occupant_phone = update_data.get('occupant_phone', unit.occupant_phone)

    if not is_occupied:
        occupant_name = None
        occupant_phone = None
        update_data['occupant_name'] = None
        update_data['occupant_phone'] = None

    _validate_occupancy(
        is_occupied=is_occupied,
        occupant_name=occupant_name,
        occupant_phone=occupant_phone,
    )

    try:
        with transaction.atomic():
            for field, value in update_data.items():
                setattr(unit, field, value)
            unit.save()
            return unit
    except ValidationError as exc:
        raise ValueError(str(exc))


def delete_unit(
    *,
    unit: Unit,
    user: "AbstractBaseUser"
) -> None:
    """
    Hard delete a unit.
    """
    _assert_owner(unit, user, 'delete')

    with transaction.atomic():
        unit.delete()


def deactivate_unit(
    *,
    unit: Unit,
    user: "AbstractBaseUser"
) -> Unit:
    """
    Deactivate a unit.
    """
    _assert_owner(unit, user, 'deactivate')

    unit.is_active = False
    unit.save(update_fields=['is_active', 'updated_at'])
    return unit


def activate_unit(
    *,
    unit: Unit,
    user: "AbstractBaseUser"
) -> Unit:
    """
    Activate a unit.
    """
    _assert_owner(unit, user, 'activate')

    unit.is_active = True
    unit.updated_at = timezone.now()
    unit.save(update_fields=['is_active', 'updated_at'])
    return unit


def update_occupancy(
    *,
    unit: Unit,
    user: "AbstractBaseUser",
    is_occupied: bool,
    occupant_name: Optional[str] = None,
    occupant_phone: Optional[str] = None
) -> Unit:
    """
    Update unit occupancy.
    """
    _assert_owner(unit, user, 'update occupancy')

    if not is_occupied:
        occupant_name = None
        occupant_phone = None

    _validate_occupancy(
        is_occupied=is_occupied,
        occupant_name=occupant_name,
        occupant_phone=occupant_phone,
    )

    with transaction.atomic():
        unit.is_occupied = is_occupied
        unit.occupant_name = occupant_name
        unit.occupant_phone = occupant_phone
        unit.updated_at = timezone.now()
        unit.save(update_fields=[
            'is_occupied',
            'occupant_name',
            'occupant_phone',
            'updated_at',
        ])
        return unit


# =====================================================
# Query helpers
# =====================================================

def get_user_units(
    *,
    user: "AbstractBaseUser",
    include_inactive: bool = False
) -> QuerySet[Unit]:
    queryset = Unit.objects.filter(owner=user)

    if not include_inactive:
        queryset = queryset.filter(is_active=True)

    return queryset


def get_occupied_units(
    *,
    user: "AbstractBaseUser"
) -> QuerySet[Unit]:
    return Unit.objects.filter(
        owner=user,
        is_occupied=True,
        is_active=True,
    )


def get_vacant_units(
    *,
    user: "AbstractBaseUser"
) -> QuerySet[Unit]:
    return Unit.objects.filter(
        owner=user,
        is_occupied=False,
        is_active=True,
    )


def search_units(
    *,
    user: "AbstractBaseUser",
    search_term: str
) -> QuerySet[Unit]:
    from django.db.models import Q

    return Unit.objects.filter(
        Q(owner=user),
        Q(is_active=True),
        Q(
            identifier__icontains=search_term
            | Q(occupant_name__icontains=search_term)
            | Q(description__icontains=search_term)
        )
    )
