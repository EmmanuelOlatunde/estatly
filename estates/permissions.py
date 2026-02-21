# estate/permissions.py
"""
Custom permission classes for estate app.
"""

from rest_framework import permissions



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
    Superusers can manage any estate.
    Estate managers can only write to their own estate.
    """

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        # Creation is superuser-only — managers can't create new estates
        if view.action == 'create':
            return request.user.is_superuser
        return True

    def has_object_permission(self, request, view, obj):
        if request.user.is_superuser:
            return True
        # Manager can edit estate details but NOT change manager
        if obj.manager == request.user:
            if request.method in ['PATCH', 'PUT']:
                if 'manager' in request.data:
                    return False
            return True
        return False
