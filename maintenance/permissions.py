# maintenance/permissions.py

"""
Custom permission classes for the maintenance app.

Defines permissions for maintenance ticket access and operations.
"""

import logging
from rest_framework import permissions
from rest_framework.request import Request
from rest_framework.views import APIView

logger = logging.getLogger(__name__)


class IsEstateManagerOrReadOnly(permissions.BasePermission):
    """
    Permission that allows estate managers to modify tickets,
    while allowing read-only access to authenticated users.
    
    For MVP, this assumes estate managers are identified by a role or
    relationship to the estate. Adjust logic based on your User model structure.
    """
    
    def has_permission(self, request: Request, view: APIView) -> bool:
        """
        Check if user has permission to access the view.
        
        Args:
            request: The incoming request
            view: The view being accessed
            
        Returns:
            True if user has permission, False otherwise
        """
        # Allow authenticated users to read
        if request.method in permissions.SAFE_METHODS:
            return request.user and request.user.is_authenticated
        
        # For write operations, user must be authenticated
        # Additional checks in has_object_permission
        return request.user and request.user.is_authenticated
    
    def has_object_permission(self, request: Request, view: APIView, obj) -> bool:
        """
        Check if user has permission to access a specific ticket.
        
        Args:
            request: The incoming request
            view: The view being accessed
            obj: The MaintenanceTicket instance
            
        Returns:
            True if user has permission, False otherwise
        """
        # Read permissions for authenticated users
        if request.method in permissions.SAFE_METHODS:
            return True
        
        # Write permissions only for the creator or estate managers
        # For MVP, we'll allow the creator to modify their own tickets
        is_creator = obj.created_by == request.user
        
        # Check if user is a staff member (admin)
        is_staff = request.user.is_staff
        
        if not (is_creator or is_staff):
            logger.warning(
                f"User {request.user.id} denied permission to modify "
                f"ticket {obj.id}"
            )
        
        return is_creator or is_staff


class CanCreateTicket(permissions.BasePermission):
    """
    Permission that checks if a user can create maintenance tickets.
    
    For MVP, we allow authenticated estate managers to create tickets.
    Adjust based on your role/permission structure.
    """
    
    def has_permission(self, request: Request, view: APIView) -> bool:
        """
        Check if user can create tickets.
        
        Args:
            request: The incoming request
            view: The view being accessed
            
        Returns:
            True if user has permission, False otherwise
        """
        if not request.user or not request.user.is_authenticated:
            logger.warning("Unauthenticated user attempted to create ticket")
            return False
        
        # For MVP, allow all authenticated users to create tickets
        # In production, you might check for estate manager role:
        # return hasattr(request.user, 'is_estate_manager') and request.user.is_estate_manager
        
        return True


class IsTicketCreatorOrAdmin(permissions.BasePermission):
    """
    Permission that allows only the ticket creator or admin users
    to perform actions on a ticket.
    """
    
    def has_object_permission(self, request: Request, view: APIView, obj) -> bool:
        """
        Check if user is the ticket creator or an admin.
        
        Args:
            request: The incoming request
            view: The view being accessed
            obj: The MaintenanceTicket instance
            
        Returns:
            True if user has permission, False otherwise
        """
        is_creator = obj.created_by == request.user
        is_admin = request.user.is_staff or request.user.is_superuser
        
        has_permission = is_creator or is_admin
        
        if not has_permission:
            logger.warning(
                f"User {request.user.id} denied permission for ticket {obj.id}. "
                f"Creator: {obj.created_by.id}, User is admin: {is_admin}"
            )
        
        return has_permission


class CanAccessEstate(permissions.BasePermission):
    """
    Permission that checks if a user has access to an estate.
    
    For MVP, this is a placeholder. In production, implement proper
    estate access checks based on user roles and estate relationships.
    """
    
    def has_permission(self, request: Request, view: APIView) -> bool:
        """
        Check if user has access to the estate.
        
        Args:
            request: The incoming request
            view: The view being accessed
            
        Returns:
            True if user has permission, False otherwise
        """
        if not request.user or not request.user.is_authenticated:
            return False
        
        # For MVP, allow authenticated users
        # In production, check estate access:
        # estate_id = view.kwargs.get('estate_id') or request.data.get('estate')
        # return user_has_estate_access(request.user, estate_id)
        
        return True