# announcements/permissions.py

"""
Custom permission classes for announcements app.

Defines fine-grained permissions for announcement operations.
"""

import logging
from rest_framework import permissions
from django.contrib.auth import get_user_model
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from django.contrib.auth.models import AbstractBaseUser
User = get_user_model()

logger = logging.getLogger(__name__)


class IsManagerOrReadOnly(permissions.BasePermission):
    """
    Permission class that allows:
    - Managers to create, update, and delete announcements
    - All authenticated users to read announcements
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


class IsOwnerOrReadOnly(permissions.BasePermission):
    """
    Permission class that allows:
    - Announcement creators to update and delete their own announcements
    - All authenticated users to read announcements
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
                    f"User {request.user.id} attempted to view inactive announcement {obj.id}"
                )
                return False
            return True
        
        # Write permissions are only allowed to the creator or superuser
        is_owner = obj.created_by == request.user
        is_superuser = request.user.is_superuser
        
        if not (is_owner or is_superuser):
            logger.warning(
                f"User {request.user.id} attempted to modify announcement {obj.id} without permission"
            )
        
        return is_owner or is_superuser


class IsManager(permissions.BasePermission):
    """
    Permission class that only allows managers to access the view.
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
