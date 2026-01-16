# payments/permissions.py

"""
Custom permission classes for the payments app.

Handles authorization for fees, payments, and receipts.
"""

from rest_framework import permissions
from accounts.models import User

class IsEstateManagerOrReadOnly(permissions.BasePermission):
    """
    Permission class that allows:
    - Estate managers to create/update/delete
    - Any authenticated user to read (if they have access to the estate)
    """
    
    def has_permission(self, request, view):
        user = getattr(request, "user", None)

        if not user or not getattr(user, "is_authenticated", False):
            return False

        if request.method in permissions.SAFE_METHODS:
            return True

        return user.role == User.Role.ESTATE_MANAGER
    
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
        user = getattr(request, "user", None)

        if not user or not getattr(user, "is_authenticated", False):
            return False

        if getattr(user, "is_staff", False):
            return True

        return user.role == User.Role.ESTATE_MANAGER


class CanViewReceipt(permissions.BasePermission):
    """
    Permission class for viewing receipts.
    
    Users can view receipts for:
    - Their own units (if they're residents)
    - Any unit in estates they manage (if they're managers)
    """
    
    def has_permission(self, request, view):
        user = getattr(request, "user", None)
        return bool(user and getattr(user, "is_authenticated", False))
    
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
        user = getattr(request, "user", None)

        if not user or not getattr(user, "is_authenticated", False):
            return False

        return user.role == User.Role.ESTATE_MANAGER


class EstateAccessPermission(permissions.BasePermission):
    """
    Ensures user has access to the estate related to requested objects.
    Prevents cross-estate data access.
    """
    
    def has_object_permission(self, request, view, obj):
        """Check if user's estate matches object's estate."""
        user = request.user
        
        if not user or not user.is_authenticated:
            return False
        
        # Get the estate from the object
        if hasattr(obj, 'estate'):
            obj_estate = obj.estate
        elif hasattr(obj, 'fee') and hasattr(obj.fee, 'estate'):
            obj_estate = obj.fee.estate
        elif hasattr(obj, 'fee_assignment') and hasattr(obj.fee_assignment, 'fee'):
            obj_estate = obj.fee_assignment.fee.estate
        elif hasattr(obj, 'payment') and hasattr(obj.payment, 'fee_assignment'):
            obj_estate = obj.payment.fee_assignment.fee.estate
        else:
            return False
        
        # User must be assigned to the same estate
        user_estate = getattr(user, 'estate', None)
        if not user_estate:
            return False
        
        return user_estate.id == obj_estate.id