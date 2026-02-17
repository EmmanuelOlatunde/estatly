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
        
        # Write permissions only for the creator or superusers
        is_creator = obj.created_by == request.user
        
        # Only superusers, not is_staff (managers are is_staff but not superuser)
        is_superuser = request.user.is_superuser
        
        if not (is_creator or is_superuser):
            logger.warning(
                f"User {request.user.id} (is_staff={request.user.is_staff}) "
                f"denied permission to modify ticket {obj.id}"
            )
        
        return is_creator or is_superuser


class CanCreateTicket(permissions.BasePermission):
    """
    Permission that checks if a user can create maintenance tickets
    for the specified estate.
    
    Users can only create tickets for estates they manage.
    """
    
    def has_permission(self, request: Request, view: APIView) -> bool:
        """
        Check if user can create tickets for the specified estate.
        
        Args:
            request: The incoming request
            view: The view being accessed
            
        Returns:
            True if user has permission, False otherwise
        """
        if not request.user or not request.user.is_authenticated:
            logger.warning("Unauthenticated user attempted to create ticket")
            return False
        
        # Only superusers can create tickets for any estate
        if request.user.is_superuser:
            return True
        
        # For create action, check if user owns the estate in request data
        if request.method == 'POST':
            estate_id = request.data.get('estate')
            if not estate_id:
                logger.warning(
                    f"User {request.user.id} attempted to create ticket without estate_id"
                )
                return False
            
            # Check if the estate matches the user's estate
            if not request.user.estate:
                logger.warning(
                    f"User {request.user.id} (is_staff={request.user.is_staff}) "
                    f"has no estate assigned"
                )
                return False
            
            user_estate_id = str(request.user.estate.id)
            request_estate_id = str(estate_id)
            
            if user_estate_id != request_estate_id:
                logger.warning(
                    f"User {request.user.id} (is_staff={request.user.is_staff}) "
                    f"attempted to create ticket for estate {estate_id} "
                    f"but they manage estate {user_estate_id}"
                )
                return False
            
            return True
        
        return True


class IsTicketCreatorOrAdmin(permissions.BasePermission):
    """
    Permission that allows only the ticket creator or superuser
    to perform actions on a ticket.
    
    Also enforces that users can only access tickets from their own estate.
    Note: is_staff (managers) are NOT treated as admins here.
    """
    
    def has_object_permission(self, request: Request, view: APIView, obj) -> bool:
        """
        Check if user is the ticket creator or a superuser,
        and that the ticket belongs to their estate.
        
        Args:
            request: The incoming request
            view: The view being accessed
            obj: The MaintenanceTicket instance
            
        Returns:
            True if user has permission, False otherwise
        """
        # Only superusers can access any ticket (not is_staff)
        is_superuser = request.user.is_superuser
        if is_superuser:
            return True
        
        # Check if ticket belongs to user's estate
        if not request.user.estate:
            logger.warning(
                f"User {request.user.id} (is_staff={request.user.is_staff}) "
                f"has no estate assigned, denied access to ticket {obj.id}"
            )
            return False
        
        ticket_estate_id = obj.estate_id
        user_estate_id = request.user.estate.id
        
        if ticket_estate_id != user_estate_id:
            logger.warning(
                f"User {request.user.id} (is_staff={request.user.is_staff}) "
                f"from estate {user_estate_id} denied access to ticket {obj.id} "
                f"from estate {ticket_estate_id}"
            )
            return False
        
        # At this point, ticket is from user's estate
        # Now check if they created it
        is_creator = obj.created_by == request.user
        
        if not is_creator:
            logger.warning(
                f"User {request.user.id} (is_staff={request.user.is_staff}) "
                f"denied permission for ticket {obj.id}. Creator: {obj.created_by.id}"
            )
        
        return is_creator


class CanAccessEstate(permissions.BasePermission):
    """
    Permission that checks if a user has access to an estate.
    
    Users can only access data from estates they manage.
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
        
        # Only superusers can access any estate (not is_staff)
        if request.user.is_superuser:
            return True
        
        # For statistics endpoint, check estate_id query param
        estate_id = request.query_params.get('estate_id')
        if estate_id:
            if not request.user.estate:
                logger.warning(
                    f"User {request.user.id} (is_staff={request.user.is_staff}) "
                    f"has no estate assigned"
                )
                return False
            
            user_estate_id = str(request.user.estate.id)
            request_estate_id = str(estate_id)
            
            if user_estate_id != request_estate_id:
                logger.warning(
                    f"User {request.user.id} (is_staff={request.user.is_staff}) "
                    f"attempted to access statistics for estate {estate_id} "
                    f"but they manage estate {user_estate_id}"
                )
                return False
        
        return True