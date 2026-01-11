"""
Custom permission classes for the units app.

Defines permissions for unit access and management.
"""

from rest_framework import permissions


class IsOwner(permissions.BasePermission):
    """
    Permission class that only allows owners to access their own units.
    
    For list views, the queryset filtering handles ownership.
    For detail views, this checks object-level ownership.
    """
    
    message = 'You do not have permission to access this unit.'
    
    def has_permission(self, request, view):
        """
        Check if user has permission to access the view.
        
        Args:
            request: The HTTP request
            view: The view being accessed
            
        Returns:
            bool: True if user is authenticated, False otherwise
        """
        return request.user and request.user.is_authenticated
    
    def has_object_permission(self, request, view, obj):
        """
        Check if user has permission to access the specific unit.
        
        Args:
            request: The HTTP request
            view: The view being accessed
            obj: The Unit instance
            
        Returns:
            bool: True if user owns the unit, False otherwise
        """
        return obj.owner == request.user


class IsOwnerOrReadOnly(permissions.BasePermission):
    """
    Permission class that allows read-only access to all authenticated users,
    but only allows owners to modify their units.
    
    This could be used if you want to allow users to view each other's units
    but only modify their own. Currently not used but available for future needs.
    """
    
    message = 'You do not have permission to modify this unit.'
    
    def has_permission(self, request, view):
        """
        Check if user has permission to access the view.
        
        Args:
            request: The HTTP request
            view: The view being accessed
            
        Returns:
            bool: True if user is authenticated, False otherwise
        """
        return request.user and request.user.is_authenticated
    
    def has_object_permission(self, request, view, obj):
        """
        Check if user has permission to access/modify the specific unit.
        
        Args:
            request: The HTTP request
            view: The view being accessed
            obj: The Unit instance
            
        Returns:
            bool: True if read-only method or user owns the unit
        """
        # Read permissions are allowed to any authenticated user
        if request.method in permissions.SAFE_METHODS:
            return True
        
        # Write permissions only for owner
        return obj.owner == request.user


class IsActiveUnit(permissions.BasePermission):
    """
    Permission class that only allows access to active units.
    
    Can be combined with other permissions for additional restrictions.
    """
    
    message = 'This unit is not active.'
    
    def has_object_permission(self, request, view, obj):
        """
        Check if the unit is active.
        
        Args:
            request: The HTTP request
            view: The view being accessed
            obj: The Unit instance
            
        Returns:
            bool: True if unit is active, False otherwise
        """
        return obj.is_active