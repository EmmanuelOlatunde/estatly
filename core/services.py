
# core/services.py
"""
Business logic for core app.
Shared utility functions for estate context and permissions.
"""

import logging
from django.contrib.auth import get_user_model
from django.core.exceptions import PermissionDenied, ValidationError

User = get_user_model()
logger = logging.getLogger(__name__)


def validate_estate_access(user, estate) -> None:
    """
    Validate that a user has access to a specific estate.
    
    In MVP: Users can only access their own estate (Super Admin can access all).
    
    Args:
        user: The user requesting access
        estate: The estate being accessed
        
    Raises:
        PermissionDenied: If user cannot access this estate
    """
    if user.is_superuser:
        return
    
    # Check if user is the estate manager
    if hasattr(user, 'managed_estate') and user.managed_estate == estate:
        return
    
    logger.warning(
        f"User {user.email} attempted unauthorized access to estate {estate.id}"
    )
    raise PermissionDenied("You don't have access to this estate.")


def get_user_estate(user):
    """
    Get the estate that a user manages.
    
    In MVP: Each estate manager manages exactly one estate.
    Super admins don't have a specific estate.
    
    Args:
        user: The user to get estate for
        
    Returns:
        Estate instance or None for super admins
        
    Raises:
        ValidationError: If user has no estate assigned
    """
    if user.is_superuser:
        return None
    
    if not hasattr(user, 'managed_estate'):
        logger.error(f"User {user.email} has no estate assigned")
        raise ValidationError("No estate assigned to this user.")
    
    return user.managed_estate


def enforce_estate_context(queryset, user):
    """
    Filter a queryset to only include objects from the user's estate.
    
    Args:
        queryset: The queryset to filter
        user: The user making the request
        
    Returns:
        Filtered queryset
    """
    if user.is_superuser:
        return queryset
    
    estate = get_user_estate(user)
    
    # Check if queryset model has estate field
    if hasattr(queryset.model, 'estate'):
        return queryset.filter(estate=estate)
    
    logger.warning(
        f"Model {queryset.model.__name__} doesn't have estate field for filtering"
    )
    return queryset


def is_estate_manager(user, estate) -> bool:
    """
    Check if a user is the manager of a specific estate.
    
    Args:
        user: The user to check
        estate: The estate to check against
        
    Returns:
        True if user manages this estate, False otherwise
    """
    if user.is_superuser:
        return True
    
    if not hasattr(user, 'managed_estate'):
        return False
    
    return user.managed_estate == estate


def can_modify_estate_data(user, obj) -> bool:
    """
    Check if a user can modify an estate-scoped object.
    
    Args:
        user: The user attempting modification
        obj: The object to modify (must have estate attribute)
        
    Returns:
        True if user can modify, False otherwise
    """
    if user.is_superuser:
        return True
    
    if not hasattr(obj, 'estate'):
        logger.warning(
            f"Object {obj.__class__.__name__} has no estate attribute"
        )
        return False
    
    return is_estate_manager(user=user, estate=obj.estate)

