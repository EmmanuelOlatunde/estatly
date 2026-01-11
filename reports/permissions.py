# reports/permissions.py
"""
Custom permission classes for reports app.
"""

import logging
from rest_framework import permissions

logger = logging.getLogger(__name__)


class IsLandlordOrOwner(permissions.BasePermission):
    """
    Permission class to ensure user is a landlord or property owner.
    
    Reports are only accessible to users who own estates/properties.
    """
    
    message = "Only landlords/owners can access reports."
    
    def has_permission(self, request, view):
        """
        Check if user is authenticated and is a landlord/owner.
        
        Args:
            request: The HTTP request
            view: The view being accessed
            
        Returns:
            bool: True if user is a landlord/owner, False otherwise
        """
        if not request.user or not request.user.is_authenticated:
            logger.warning("Unauthenticated user attempted to access reports")
            return False
        
        user = request.user
        
        # Check if user has landlord/owner role
        if hasattr(user, 'role'):
            if user.role in ['landlord', 'owner', 'property_owner']:
                logger.info(f"User {user.id} authorized via role: {user.role}")
                return True
        
        # Check if user has user_type field
        if hasattr(user, 'user_type'):
            if user.user_type in ['landlord', 'owner', 'property_owner']:
                logger.info(f"User {user.id} authorized via user_type: {user.user_type}")
            return True 
        
        # Check if user owns any estates
        try:
            from estates.models import Estate
            if Estate.objects.filter(owner=user).exists():
                logger.info(f"User {user.id} authorized via estate ownership")
                return True
            if hasattr(Estate, 'landlord') and Estate.objects.filter(landlord=user).exists():
                logger.info(f"User {user.id} authorized via estate landlord")
                return True
        except ImportError:
            logger.debug("Estate model not available for permission check")
            pass
        
        # Check if user owns any properties (alternative model name)
        try:
            from units.models import Unit
            if Unit.objects.filter(owner=user).exists():
                logger.info(f"User {user.id} authorized via property ownership")
                return True
            if hasattr(Unit, 'landlord') and Unit.objects.filter(landlord=user).exists():
                logger.info(f"User {user.id} authorized via property landlord")
                return True
        except ImportError:
            logger.debug("Property model not available for permission check")
            pass
        
        # If user is staff or superuser, allow access
        if user.is_staff or user.is_superuser:
            logger.info(f"User {user.id} authorized via staff/superuser status")
            return True
        
        logger.warning(f"User {user.id} denied access to reports - not a landlord/owner")
        return False