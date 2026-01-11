# payments/permissions.py

"""
Custom permission classes for the payments app.

Handles authorization for fees, payments, and receipts.
"""

from rest_framework import permissions


class IsEstateManagerOrReadOnly(permissions.BasePermission):
    """
    Permission class that allows:
    - Estate managers to create/update/delete
    - Any authenticated user to read (if they have access to the estate)
    """
    
    def has_permission(self, request, view):
        """Check if user has permission to access the view."""
        if not request.user or not request.user.is_authenticated:
            return False
        
        if request.method in permissions.SAFE_METHODS:
            return True
        
        return hasattr(request.user, 'is_estate_manager') and request.user.is_estate_manager
    
    def has_object_permission(self, request, view, obj):
        """Check if user has permission to access the specific object."""
        if not request.user or not request.user.is_authenticated:
            return False
        
        if request.method in permissions.SAFE_METHODS:
            return self._user_has_estate_access(request.user, obj)
        
        if hasattr(request.user, 'is_estate_manager') and request.user.is_estate_manager:
            return self._user_has_estate_access(request.user, obj)
        
        return False
    
    def _user_has_estate_access(self, user, obj):
        """
        Check if user has access to the estate related to this object.
        
        This is a placeholder - actual implementation depends on your estate
        access control model.
        """
        if hasattr(obj, 'estate'):
            estate = obj.estate
        elif hasattr(obj, 'fee') and hasattr(obj.fee, 'estate'):
            estate = obj.fee.estate
        elif hasattr(obj, 'fee_assignment') and hasattr(obj.fee_assignment.fee, 'estate'):
            estate = obj.fee_assignment.fee.estate
        elif hasattr(obj, 'payment') and hasattr(obj.payment.fee_assignment.fee, 'estate'):
            estate = obj.payment.fee_assignment.fee.estate  # noqa: F841
        else:
            return False
        
        return True


class CanRecordPayment(permissions.BasePermission):
    """
    Permission class for recording payments.
    
    Only estate managers or authorized staff can record payments.
    """
    
    message = "You do not have permission to record payments."
    
    def has_permission(self, request, view):
        """Check if user can record payments."""
        if not request.user or not request.user.is_authenticated:
            return False
        
        return (
            hasattr(request.user, 'is_estate_manager') and request.user.is_estate_manager
        ) or (
            hasattr(request.user, 'is_staff') and request.user.is_staff
        )


class CanViewReceipt(permissions.BasePermission):
    """
    Permission class for viewing receipts.
    
    Users can view receipts for:
    - Their own units (if they're residents)
    - Any unit in estates they manage (if they're managers)
    """
    
    def has_permission(self, request, view):
        """Check if user is authenticated."""
        return request.user and request.user.is_authenticated
    
    def has_object_permission(self, request, view, obj):
        """Check if user can view this specific receipt."""
        if not request.user or not request.user.is_authenticated:
            return False
        
        if hasattr(request.user, 'is_estate_manager') and request.user.is_estate_manager:
            return True
        
        if hasattr(obj, 'payment'):
            unit = obj.payment.fee_assignment.unit
            return self._user_owns_or_resides_in_unit(request.user, unit)
        
        return False
    
    def _user_owns_or_resides_in_unit(self, user, unit):
        """
        Check if user owns or resides in the unit.
        
        This is a placeholder - actual implementation depends on your
        unit ownership/residency model.
        """
        return hasattr(unit, 'owner') and unit.owner == user


class IsEstateManager(permissions.BasePermission):
    """
    Permission class that only allows estate managers.
    """
    
    message = "Only estate managers can perform this action."
    
    def has_permission(self, request, view):
        """Check if user is an estate manager."""
        if not request.user or not request.user.is_authenticated:
            return False
        
        return hasattr(request.user, 'is_estate_manager') and request.user.is_estate_manager