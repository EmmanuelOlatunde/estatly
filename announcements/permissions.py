# announcements/permissions.py

"""
Custom permission classes for announcements app.

Defines fine-grained permissions for announcement operations.
SECURITY: Only is_superuser is treated as admin, not is_staff (managers).
"""

import logging
from rest_framework import permissions
from django.contrib.auth import get_user_model
from .utils import is_manager


User = get_user_model()

logger = logging.getLogger(__name__)


class IsManagerOrReadOnly(permissions.BasePermission):
    """
    Permission class that allows:
    - Managers to create, update, and delete announcements
    - All authenticated users to read announcements
    
    Note: This checks if user is a manager (has is_staff or specific role),
    but does NOT grant cross-estate access. Estate filtering is done in get_queryset().
    """
    
    message = "You must be a manager to perform this action."
    
    def has_permission(self, request, view) -> bool:
        """
        Check if the user has permission to access the view.
        
        Args:
            request: The HTTP request
            view: The view being accessed
        
        Returns:
            True if user has permission, False otherwise
        """
        # Allow read-only methods for all authenticated users
        if request.method in permissions.SAFE_METHODS:
            return request.user and request.user.is_authenticated
        
        # Write methods require manager status
        return request.user and request.user.is_authenticated and self._is_manager(request.user)
    
    def _is_manager(self, user) -> bool:
        return is_manager(user)  # delegate to shared helper


class IsOwnerOrReadOnly(permissions.BasePermission):
    """
    Permission class that allows:
    - Announcement creators to update and delete their own announcements
    - Superusers to modify any announcement
    - All authenticated users to read announcements
    
    Note: is_staff (managers) are NOT treated as admins here.
    """
    
    message = "You can only modify your own announcements."
    
    def has_permission(self, request, view) -> bool:
        """
        Check if the user has permission to access the view.
        
        Args:
            request: The HTTP request
            view: The view being accessed
        
        Returns:
            True if user has permission, False otherwise
        """
        # All authenticated users can access the view
        return request.user and request.user.is_authenticated
    
    def has_object_permission(self, request, view, obj) -> bool:
        """
        Check if the user has permission to access a specific object.
        
        Args:
            request: The HTTP request
            view: The view being accessed
            obj: The object being accessed (Announcement instance)
        
        Returns:
            True if user has permission, False otherwise
        """
        # Read permissions are allowed for any authenticated user
        if request.method in permissions.SAFE_METHODS:
            # Only show active announcements to non-creators
            if not obj.is_active and obj.created_by != request.user:
                logger.warning(
                    f"User {request.user.id} (is_staff={request.user.is_staff}) "
                    f"attempted to view inactive announcement {obj.id}"
                )
                return False
            return True
        
        # Write permissions are only allowed to the creator or superuser (not is_staff)
        is_owner = obj.created_by == request.user
        is_superuser = request.user.is_superuser
        
        if not (is_owner or is_superuser):
            logger.warning(
                f"User {request.user.id} (is_staff={request.user.is_staff}) "
                f"attempted to modify announcement {obj.id} without permission. "
                f"Creator: {obj.created_by.id}"
            )
        
        return is_owner or is_superuser


class IsManager(permissions.BasePermission):
    """
    Permission class that only allows managers to access the view.
    
    Note: This checks if user is a manager (has is_staff or specific role),
    but does NOT grant cross-estate access. Estate filtering is done in get_queryset().
    """
    
    message = "You must be a manager to access this resource."
    
    def has_permission(self, request, view) -> bool:
        """
        Check if the user has permission to access the view.
        
        Args:
            request: The HTTP request
            view: The view being accessed
        
        Returns:
            True if user has permission, False otherwise
        """
        if not (request.user and request.user.is_authenticated):
            return False
        
        return self._is_manager(request.user)
    
    def _is_manager(self, user) -> bool:
        return is_manager(user)  # delegate to shared helper


class IsActiveUser(permissions.BasePermission):
    """
    Allows access only to active users.
    """

    message = "Your account is inactive."

    def has_permission(self, request, view) -> bool:
        return bool(
            request.user
            and request.user.is_authenticated
            and request.user.is_active
        )