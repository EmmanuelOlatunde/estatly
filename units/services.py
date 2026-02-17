"""
Business logic layer for the units app.

Contains all domain logic for unit management operations.
"""

from typing import Optional, TYPE_CHECKING, Tuple, List, Union
from django.contrib.auth import get_user_model
from django.db import transaction
from django.db.models import QuerySet
from django.core.exceptions import ValidationError
from estates.models import Estate
from django.utils import timezone
import uuid


from .models import Unit
if TYPE_CHECKING:
    from django.contrib.auth.models import AbstractBaseUser

User = get_user_model()


# =====================================================
# Internal helpers (DRY)
# =====================================================

def _assert_owner(unit: Unit, user: "AbstractBaseUser", action: str) -> None:
    """
    Verify that the user owns the unit.
    
    Raises:
        PermissionError: If user is not the owner
    """
    if unit.owner_id != user.id:
        raise PermissionError(f'Only the unit owner can {action} this unit.')


def _validate_identifier(
    *,
    owner: "AbstractBaseUser",
    identifier: Optional[str],
    exclude_unit_id: Optional[int] = None
) -> str:
    """
    Validate unit identifier uniqueness and format.
    
    Args:
        owner: The owner to check uniqueness for
        identifier: The identifier to validate
        exclude_unit_id: Optional unit ID to exclude from uniqueness check
        
    Returns:
        The cleaned identifier
        
    Raises:
        ValueError: If identifier is invalid or not unique
    """
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
    """
    Validate that unit type is valid.
    
    Args:
        unit_type: The unit type to validate
        
    Raises:
        ValueError: If unit type is invalid
    """
    valid_types = {choice[0] for choice in Unit.UnitType.choices}
    if unit_type not in valid_types:
        raise ValueError(f'Invalid unit type. Must be one of: {sorted(valid_types)}')


def _validate_occupancy(
    *,
    is_occupied: bool,
    occupant_name: Optional[str],
    occupant_phone: Optional[str]
) -> None:
    """
    Validate occupancy information consistency.
    
    Args:
        is_occupied: Whether the unit is occupied
        occupant_name: Occupant's name
        occupant_phone: Occupant's phone
        
    Raises:
        ValueError: If occupancy information is inconsistent
    """
    if (occupant_name or occupant_phone) and not is_occupied:
        raise ValueError(
            'Unit must be marked as occupied if occupant info is provided.'
        )


def _validate_estate_ownership(estate: Estate, owner: "AbstractBaseUser") -> None:
    """
    Validate that the user owns the estate.
    
    Args:
        estate: The estate to validate
        owner: The expected owner
        
    Raises:
        ValueError: If user doesn't own the estate
    """
    if estate.manager != owner:
        raise ValueError('You can only add units to estates you own.')


# =====================================================
# Public service functions
# =====================================================

def create_unit(
    *,
    owner: "AbstractBaseUser",
    estate: "Estate",
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
    
    _validate_estate_ownership(estate, owner)
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
                estate=estate,
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
    
    Args:
        unit: The unit to update
        user: The user performing the update
        **update_data: Fields to update
        
    Returns:
        The updated Unit instance
        
    Raises:
        PermissionError: If user is not the owner
        ValueError: If validation fails
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
    
    Args:
        unit: The unit to delete
        user: The user performing the deletion
        
    Raises:
        PermissionError: If user is not the owner
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
    Deactivate a unit (soft delete).
    
    Args:
        unit: The unit to deactivate
        user: The user performing the deactivation
        
    Returns:
        The deactivated Unit instance
        
    Raises:
        PermissionError: If user is not the owner
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
    Activate a previously deactivated unit.
    
    Args:
        unit: The unit to activate
        user: The user performing the activation
        
    Returns:
        The activated Unit instance
        
    Raises:
        PermissionError: If user is not the owner
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
    Update unit occupancy status and information.
    
    Args:
        unit: The unit to update
        user: The user performing the update
        is_occupied: Whether the unit is occupied
        occupant_name: Occupant's name (optional)
        occupant_phone: Occupant's phone (optional)
        
    Returns:
        The updated Unit instance
        
    Raises:
        PermissionError: If user is not the owner
        ValueError: If validation fails
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


def bulk_update_units(
    *,
    user: "AbstractBaseUser",
    unit_ids: List[Union[str, uuid.UUID]],
    **update_fields
) -> Tuple[int, List[str]]:
    """
    Bulk update multiple units owned by the user.
    
    Args:
        user: The user performing the updates
        unit_ids: List of unit IDs (can be strings or UUIDs)
        **update_fields: Fields to update (is_active, is_occupied, etc.)
        
    Returns:
        Tuple of (number of units updated, list of updated unit IDs as strings)
        
    Raises:
        ValueError: If no units found or validation fails
    """
    if not unit_ids:
        raise ValueError('No unit IDs provided.')
    
    # Convert string IDs to UUIDs if necessary
    converted_ids = []
    for uid in unit_ids:
        if isinstance(uid, str):
            try:
                converted_ids.append(uuid.UUID(uid))
            except ValueError:
                raise ValueError(f'Invalid UUID format: {uid}')
        else:
            converted_ids.append(uid)
    
    # Get units owned by user
    units = Unit.objects.filter(
        id__in=converted_ids,
        owner=user
    )
    
    if not units.exists():
        raise ValueError('No units found matching the provided IDs.')
    
    # Validate update fields
    allowed_fields = {'is_active', 'is_occupied', 'occupant_name', 'occupant_phone'}
    invalid_fields = set(update_fields.keys()) - allowed_fields
    if invalid_fields:
        raise ValueError(f'Invalid fields: {invalid_fields}')
    
    # Perform bulk update
    with transaction.atomic():
        update_fields['updated_at'] = timezone.now()
        updated_count = units.update(**update_fields)
        # Convert UUIDs to strings for JSON serialization
        updated_ids = [str(uid) for uid in units.values_list('id', flat=True)]
    
    return updated_count, updated_ids


# =====================================================
# Query helpers
# =====================================================

def get_user_units(
    *,
    user: "AbstractBaseUser",
    include_inactive: bool = False
) -> QuerySet[Unit]:
    """
    Get all units owned by a user.
    
    Args:
        user: The user to get units for
        include_inactive: Whether to include inactive units
        
    Returns:
        QuerySet of Unit instances
    """
    queryset = Unit.objects.filter(owner=user)

    if not include_inactive:
        queryset = queryset.filter(is_active=True)

    return queryset


def get_occupied_units(
    *,
    user: "AbstractBaseUser"
) -> QuerySet[Unit]:
    """
    Get all occupied units owned by a user.
    
    Args:
        user: The user to get units for
        
    Returns:
        QuerySet of occupied Unit instances
    """
    return Unit.objects.filter(
        owner=user,
        is_occupied=True,
        is_active=True,
    )


def get_vacant_units(
    *,
    user: "AbstractBaseUser"
) -> QuerySet[Unit]:
    """
    Get all vacant (unoccupied) units owned by a user.
    
    Args:
        user: The user to get units for
        
    Returns:
        QuerySet of vacant Unit instances
    """
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
    """
    Search units owned by a user.
    
    Args:
        user: The user to search units for
        search_term: The term to search for
        
    Returns:
        QuerySet of matching Unit instances
    """
    from django.db.models import Q

    return Unit.objects.filter(
        owner=user,
        is_active=True,
    ).filter(
        Q(identifier__icontains=search_term) |
        Q(occupant_name__icontains=search_term) |
        Q(description__icontains=search_term)
    )


def get_units_by_estate(
    *,
    user: "AbstractBaseUser",
    estate: Estate
) -> QuerySet[Unit]:
    """
    Get all units in a specific estate owned by a user.
    
    Args:
        user: The user to get units for
        estate: The estate to filter by
        
    Returns:
        QuerySet of Unit instances
    """
    return Unit.objects.filter(
        owner=user,
        estate=estate,
        is_active=True,
    )


def get_unit_statistics(
    *,
    user: "AbstractBaseUser"
) -> dict:
    """
    Get statistics about a user's units.
    
    Args:
        user: The user to get statistics for
        
    Returns:
        Dictionary containing unit statistics
    """
    from django.db.models import Count, Q
    
    units = Unit.objects.filter(owner=user, is_active=True)
    
    stats = units.aggregate(
        total_units=Count('id'),
        occupied_units=Count('id', filter=Q(is_occupied=True)),
        vacant_units=Count('id', filter=Q(is_occupied=False)),
    )
    
    # Calculate occupancy rate
    if stats['total_units'] > 0:
        stats['occupancy_rate'] = (stats['occupied_units'] / stats['total_units']) * 100
    else:
        stats['occupancy_rate'] = 0.0
    
    return stats