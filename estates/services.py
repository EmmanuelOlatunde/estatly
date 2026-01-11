# estates/services.py
"""
Business logic layer for estates app.
"""

from typing import Optional, Dict, Any
from django.db import transaction, models
from django.core.exceptions import ValidationError
from .models import Estate


def create_estate(
    *,
    name: str,
    estate_type: str,
    fee_frequency: str,
    approximate_units: Optional[int] = None,
    is_active: bool = True,
    description: Optional[str] = None,
    address: Optional[str] = None,
    **kwargs
) -> Estate:
    """
    Create a new estate.
    
    Args:
        name: Estate name
        estate_type: Type of estate (GOVERNMENT or PRIVATE)
        fee_frequency: Fee payment frequency (MONTHLY or YEARLY)
        approximate_units: Approximate number of units
        is_active: Whether estate is active
        description: Optional description
        address: Optional physical address
        **kwargs: Additional fields
    
    Returns:
        The created Estate instance
    
    Raises:
        ValueError: If validation fails
        ValidationError: If model validation fails
    """
    if not name or not name.strip():
        raise ValueError("Estate name is required and cannot be empty.")
    
    if estate_type not in dict(Estate.EstateType.choices):
        raise ValueError(f"Invalid estate type: {estate_type}")
    
    if fee_frequency not in dict(Estate.FeeFrequency.choices):
        raise ValueError(f"Invalid fee frequency: {fee_frequency}")
    
    if approximate_units is not None and approximate_units < 1:
        raise ValueError("Number of units must be at least 1.")
    
    try:
        with transaction.atomic():
            estate = Estate.objects.create(
                name=name.strip(),
                estate_type=estate_type,
                fee_frequency=fee_frequency,
                approximate_units=approximate_units,
                is_active=is_active,
                description=description,
                address=address,
                **kwargs
            )
            return estate
    except ValidationError as e:
        raise ValueError(f"Estate validation failed: {e}")


def update_estate(
    *,
    estate: Estate,
    **update_fields: Any
) -> Estate:
    """
    Update an existing estate.
    
    Args:
        estate: The Estate instance to update
        **update_fields: Fields to update
    
    Returns:
        The updated Estate instance
    
    Raises:
        ValueError: If validation fails
        ValidationError: If model validation fails
    """
    if 'name' in update_fields:
        name = update_fields['name']
        if not name or not name.strip():
            raise ValueError("Estate name cannot be empty.")
        update_fields['name'] = name.strip()
    
    if 'estate_type' in update_fields:
        if update_fields['estate_type'] not in dict(Estate.EstateType.choices):
            raise ValueError(f"Invalid estate type: {update_fields['estate_type']}")
    
    if 'fee_frequency' in update_fields:
        if update_fields['fee_frequency'] not in dict(Estate.FeeFrequency.choices):
            raise ValueError(f"Invalid fee frequency: {update_fields['fee_frequency']}")
    
    if 'approximate_units' in update_fields:
        units = update_fields['approximate_units']
        if units is not None and units < 1:
            raise ValueError("Number of units must be at least 1.")
    
    try:
        with transaction.atomic():
            for field, value in update_fields.items():
                setattr(estate, field, value)
            estate.full_clean()
            estate.save()
            return estate
    except ValidationError as e:
        raise ValueError(f"Estate update validation failed: {e}")


def deactivate_estate(*, estate: Estate) -> Estate:
    """
    Deactivate an estate.
    
    Args:
        estate: The Estate instance to deactivate
    
    Returns:
        The updated Estate instance
    """
    estate.is_active = False
    estate.save(update_fields=['is_active', 'updated_at'])
    return estate


def activate_estate(*, estate: Estate) -> Estate:
    """
    Activate an estate.
    
    Args:
        estate: The Estate instance to activate
    
    Returns:
        The updated Estate instance
    """
    estate.is_active = True
    estate.save(update_fields=['is_active', 'updated_at'])
    return estate


def get_active_estates():
    """
    Get all active estates.
    
    Returns:
        QuerySet of active Estate instances
    """
    return Estate.objects.filter(is_active=True)


def get_estates_by_type(*, estate_type: str):
    """
    Get estates filtered by type.
    
    Args:
        estate_type: Type of estate to filter by
    
    Returns:
        QuerySet of Estate instances
    
    Raises:
        ValueError: If estate_type is invalid
    """
    if estate_type not in dict(Estate.EstateType.choices):
        raise ValueError(f"Invalid estate type: {estate_type}")
    
    return Estate.objects.filter(estate_type=estate_type)


def get_estate_statistics() -> Dict[str, Any]:
    """
    Get statistics about estates.
    
    Returns:
        Dictionary containing estate statistics
    """
    from django.db.models import Count, Sum
    
    stats = Estate.objects.aggregate(
        total_estates=Count('id'),
        active_estates=Count('id', filter=models.Q(is_active=True)),
        government_estates=Count('id', filter=models.Q(estate_type=Estate.EstateType.GOVERNMENT)),
        private_estates=Count('id', filter=models.Q(estate_type=Estate.EstateType.PRIVATE)),
        total_units=Sum('approximate_units'),
    )
    
    return stats