# announcements/services.py

"""
Business logic layer for announcements app.

Contains all domain logic and business rules for announcement operations.
"""

import logging
from typing import Optional
from django.contrib.auth import get_user_model
from django.db.models import QuerySet
from django.core.exceptions import ValidationError, PermissionDenied
from .models import Announcement
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from django.contrib.auth.base_user import AbstractBaseUser

User = get_user_model()
logger = logging.getLogger(__name__)


def create_announcement(
    *,
    created_by,
    estate,
    title: str,
    message: str,
    is_active: bool = True,
    **kwargs
) -> Announcement:
    """
    Create a new announcement.
    
    Args:
        created_by: The user creating the announcement (must be a manager)
        estate: The estate this announcement belongs to
        title: The announcement title
        message: The announcement message content
        is_active: Whether the announcement is active (default: True)
        **kwargs: Additional fields for the announcement
    
    Returns:
        The created Announcement instance
    
    Raises:
        ValidationError: If validation fails
        PermissionDenied: If user doesn't have permission
    """
    logger.info(
        f"Creating announcement titled '{title}' by user {created_by.id} "
        f"for estate {estate.id}"
    )
    
    # Validate user permissions
    if not _user_can_create_announcement(created_by):
        logger.warning(
            f"User {created_by.id} attempted to create announcement without permission"
        )
        raise PermissionDenied(
            "You do not have permission to create announcements."
        )
    
    # Validate estate assignment for non-superusers
    if not created_by.is_superuser:
        if hasattr(created_by, 'estate') and created_by.estate:
            if estate.id != created_by.estate.id:
                logger.warning(
                    f"User {created_by.id} attempted to create announcement "
                    f"for estate {estate.id} but they manage estate {created_by.estate.id}"
                )
                raise PermissionDenied(
                    f"You can only create announcements for your assigned estate: {created_by.estate.name}"
                )
    
    # Create the announcement
    try:
        announcement = Announcement(
            created_by=created_by,
            estate=estate,
            title=title.strip(),
            message=message.strip(),
            is_active=is_active,
            **kwargs
        )
        announcement.full_clean()
        announcement.save()
        
        logger.info(
            f"Successfully created announcement {announcement.id}"
        )
        return announcement
        
    except ValidationError as e:
        logger.error(
            f"Validation error creating announcement: {str(e)}"
        )
        raise
    except Exception as e:
        logger.error(
            f"Unexpected error creating announcement: {str(e)}"
        )
        raise


def update_announcement(
    *,
    announcement: Announcement,
    user,
    title: Optional[str] = None,
    message: Optional[str] = None,
    is_active: Optional[bool] = None,
    **kwargs
) -> Announcement:
    """
    Update an existing announcement.
    
    Args:
        announcement: The announcement instance to update
        user: The user performing the update
        title: New title (optional)
        message: New message (optional)
        is_active: New active status (optional)
        **kwargs: Additional fields to update
    
    Returns:
        The updated Announcement instance
    
    Raises:
        ValidationError: If validation fails
        PermissionDenied: If user doesn't have permission
    """
    logger.info(
        f"Updating announcement {announcement.id} by user {user.id}"
    )
    
    # Validate user permissions
    if not _user_can_modify_announcement(user, announcement):
        logger.warning(
            f"User {user.id} attempted to update announcement {announcement.id} without permission"
        )
        raise PermissionDenied(
            "You do not have permission to update this announcement."
        )
    
    # Update fields if provided
    try:
        if title is not None:
            announcement.title = title.strip()
        
        if message is not None:
            announcement.message = message.strip()
        
        if is_active is not None:
            announcement.is_active = is_active
        
        # Update any additional fields (but not estate - it can't be changed)
        for key, value in kwargs.items():
            if hasattr(announcement, key) and key != 'estate':
                setattr(announcement, key, value)
        
        announcement.full_clean()
        announcement.save()
        
        logger.info(
            f"Successfully updated announcement {announcement.id}"
        )
        return announcement
        
    except ValidationError as e:
        logger.error(
            f"Validation error updating announcement {announcement.id}: {str(e)}"
        )
        raise
    except Exception as e:
        logger.error(
            f"Unexpected error updating announcement {announcement.id}: {str(e)}"
        )
        raise


def delete_announcement(
    *,
    announcement: Announcement,
    user,
) -> None:
    """
    Delete an announcement.
    
    Args:
        announcement: The announcement instance to delete
        user: The user performing the deletion
    
    Raises:
        PermissionDenied: If user doesn't have permission
    """
    logger.info(
        f"Deleting announcement {announcement.id} by user {user.id}"
    )
    
    # Validate user permissions
    if not _user_can_modify_announcement(user, announcement):
        logger.warning(
            f"User {user.id} attempted to delete announcement {announcement.id} without permission"
        )
        raise PermissionDenied(
            "You do not have permission to delete this announcement."
        )
    
    try:
        announcement_id = announcement.id
        announcement.delete()
        
        logger.info(
            f"Successfully deleted announcement {announcement_id}"
        )
        
    except Exception as e:
        logger.error(
            f"Error deleting announcement {announcement.id}: {str(e)}"
        )
        raise


def get_user_announcements(
    user,
    include_inactive: bool = False
) -> QuerySet[Announcement]:
    """
    Get announcements visible to a user.
    
    Superusers: All announcements
    Managers: Only announcements from their estate
    Other users: All active announcements from their estate
    
    Args:
        user: The user requesting announcements
        include_inactive: Whether to include inactive announcements
    
    Returns:
        QuerySet of Announcement instances
    """
    logger.debug(
        f"Fetching announcements for user {user.id}"
    )
    
    # Superusers see all announcements
    if user.is_superuser:
        queryset = Announcement.objects.all()
    # Managers and regular users see only their estate's announcements
    elif hasattr(user, 'estate') and user.estate:
        queryset = Announcement.objects.filter(estate=user.estate)
    else:
        # Users without estates see nothing
        queryset = Announcement.objects.none()
    
    # Filter by active status
    if not include_inactive:
        queryset = queryset.filter(is_active=True)
    
    return queryset.select_related('created_by', 'estate')


def get_announcement_by_id(
    announcement_id: str,
    user,
) -> Announcement:
    """
    Get a specific announcement by ID.
    
    Args:
        announcement_id: UUID of the announcement
        user: The user requesting the announcement
    
    Returns:
        The Announcement instance
    
    Raises:
        Announcement.DoesNotExist: If announcement not found
        PermissionDenied: If user doesn't have permission to view
    """
    logger.debug(
        f"Fetching announcement {announcement_id} for user {user.id}"
    )
    
    try:
        announcement = Announcement.objects.select_related(
            'created_by', 'estate'
        ).get(id=announcement_id)
        
        # Check if user can view this announcement
        if not _user_can_view_announcement(user, announcement):
            logger.warning(
                f"User {user.id} attempted to view announcement {announcement_id} without permission"
            )
            raise PermissionDenied(
                "You do not have permission to view this announcement."
            )
        
        return announcement
        
    except Announcement.DoesNotExist:
        logger.warning(
            f"Announcement {announcement_id} not found"
        )
        raise


def _is_manager(user,) -> bool:
    """
    Check if a user is a manager.
    
    Args:
        user: User instance to check
    
    Returns:
        True if user is a manager, False otherwise
    """
    # Check if user has staff status or is superuser
    if user.is_staff or user.is_superuser:
        return True
    
    # Check for manager role if role system exists
    if hasattr(user, 'role'):
        return user.role in ['MANAGER', 'ADMIN']
    
    # Check for groups
    if hasattr(user, 'groups'):
        return user.groups.filter(name__in=['Managers', 'Admins']).exists()
    
    return False


def _user_can_create_announcement(user,) -> bool:
    """
    Check if a user can create announcements.
    
    Args:
        user: User instance to check
    
    Returns:
        True if user can create announcements, False otherwise
    """
    return _is_manager(user)


def _user_can_view_announcement(user, announcement: Announcement) -> bool:
    """
    Check if a user can view a specific announcement.
    
    Args:
        user: User instance to check
        announcement: Announcement instance
    
    Returns:
        True if user can view the announcement, False otherwise
    """
    # Superusers can view any announcement
    if user.is_superuser:
        return True
    
    # Check if announcement is from user's estate
    if hasattr(user, 'estate') and user.estate:
        if announcement.estate_id != user.estate.id:
            return False
    else:
        # Users without estates can't view announcements
        return False
    
    # Inactive announcements can only be viewed by their creator
    if not announcement.is_active:
        return announcement.created_by == user
    
    # Active announcements can be viewed by anyone in the estate
    return True


def _user_can_modify_announcement(user, announcement: Announcement) -> bool:
    """
    Check if a user can modify a specific announcement.
    
    Args:
        user: User instance to check
        announcement: Announcement instance
    
    Returns:
        True if user can modify the announcement, False otherwise
    """
    # Superusers can modify any announcement
    if user.is_superuser:
        return True
    
    # Check if announcement is from user's estate
    if hasattr(user, 'estate') and user.estate:
        if announcement.estate_id != user.estate.id:
            return False
    else:
        # Users without estates can't modify announcements
        return False
    
    # Only the creator can modify (within their estate)
    return announcement.created_by == user