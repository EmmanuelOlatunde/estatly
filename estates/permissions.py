# estate/permissions.py
"""
Custom permission classes for estate app.
"""

from rest_framework import permissions


class IsAuthenticatedOrReadOnly(permissions.BasePermission):
    """
    Allow read access to anyone, but write access only to authenticated users.
    """
    
    def has_permission(self, request, view):
        """Check if user has permission to access the view."""
        if request.method in permissions.SAFE_METHODS:
            return True
        return request.user and request.user.is_authenticated


class IsAdminOrReadOnly(permissions.BasePermission):
    """
    Allow read access to authenticated users, but write access only to admin users.
    """
    
    def has_permission(self, request, view):
        """Check if user has permission to access the view."""
        if not request.user or not request.user.is_authenticated:
            return False
        
        if request.method in permissions.SAFE_METHODS:
            return True
        
        return request.user.is_staff or request.user.is_superuser


class CanManageEstate(permissions.BasePermission):
    """
    Permission to manage estate records.
    Only staff and superusers can create, update, or delete estates.
    """
    
    def has_permission(self, request, view):
        """Check if user has permission to access the view."""
        if not request.user or not request.user.is_authenticated:
            return False
        
        if request.method in permissions.SAFE_METHODS:
            return True
        
        return request.user.is_staff or request.user.is_superuser
    
    def has_object_permission(self, request, view, obj):
        """Check if user has permission to access the specific estate."""
        if request.method in permissions.SAFE_METHODS:
            return True
        
        return request.user.is_staff or request.user.is_superuser
