
# core/permissions.py
"""
Custom permission classes for core app.
Simple MVP permissions: Estate Manager or Super Admin only.
"""

from rest_framework import permissions
from . import services


class IsEstateManagerOrSuperAdmin(permissions.BasePermission):
    """
    Permission class for estate managers and super admins.
    MVP: Only estate managers can access their estate's data.
    """
    
    message = "You must be an estate manager to perform this action."
    
    def has_permission(self, request, view):
        """Check if user is authenticated and has estate access."""
        if not request.user or not request.user.is_authenticated:
            return False
        
        # Super admins can do everything
        if request.user.is_superuser:
            return True
        
        # Estate managers can access their own estate
        try:
            services.get_user_estate(request.user)
            return True
        except Exception:
            return False
    
    def has_object_permission(self, request, view, obj):
        """Check if user can access this specific object."""
        if request.user.is_superuser:
            return True
        
        # For estate-scoped objects
        if hasattr(obj, 'estate'):
            return services.is_estate_manager(
                user=request.user,
                estate=obj.estate
            )
        
        return False


class IsSuperAdminOnly(permissions.BasePermission):
    """
    Permission class that only allows super admins.
    Used for system-level operations.
    """
    
    message = "Only super administrators can perform this action."
    
    def has_permission(self, request, view):
        """Check if user is a super admin."""
        return request.user and request.user.is_authenticated and request.user.is_superuser


class ReadOnlyForAll(permissions.BasePermission):
    """
    Read-only permission for safe methods, estate manager for modifications.
    """
    
    def has_permission(self, request, view):
        """Allow read for authenticated users, write for estate managers."""
        if not request.user or not request.user.is_authenticated:
            return False
        
        if request.method in permissions.SAFE_METHODS:
            return True
        
        return (
            request.user.is_superuser or
            hasattr(request.user, 'managed_estate')
        )

