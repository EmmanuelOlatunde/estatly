# maintenance/services.py

"""
Business logic layer for the maintenance app.

Contains all domain logic and business rules for maintenance ticket management.
"""

import logging
from typing import Optional, Dict, Any, TYPE_CHECKING
from django.db import transaction
from django.db.models import QuerySet, Q
from django.utils import timezone
from django.core.exceptions import ValidationError
from django.contrib.auth import get_user_model

from .models import MaintenanceTicket
if TYPE_CHECKING:
    from django.contrib.auth.models import AbstractBaseUser

User = get_user_model()
logger = logging.getLogger(__name__)


def create_maintenance_ticket(
    *,
    title: str,
    description: str,
    category: str,
    estate_id: str,
    created_by: "AbstractBaseUser",
    unit_id: Optional[str] = None,
    **kwargs
) -> MaintenanceTicket:
    """
    Create a new maintenance ticket.
    
    Args:
        title: Brief title describing the issue
        description: Detailed description of the maintenance issue
        category: Category of the issue (WATER, ELECTRICITY, etc.)
        estate_id: UUID of the estate where the issue is located
        created_by: User who is creating the ticket (estate manager)
        unit_id: Optional UUID of the unit associated with the issue
        **kwargs: Additional fields for the ticket
        
    Returns:
        The created MaintenanceTicket instance
        
    Raises:
        ValueError: If validation fails or required data is missing
        ValidationError: If model validation fails
    """
    logger.info(
        f"Creating maintenance ticket for estate {estate_id} by user {created_by.id}"
    )
    
    # Validate required fields
    if not title or not title.strip():
        logger.error("Attempted to create ticket with empty title")
        raise ValueError("Title is required and cannot be empty")
    
    if not description or not description.strip():
        logger.error("Attempted to create ticket with empty description")
        raise ValueError("Description is required and cannot be empty")
    
    if not category:
        logger.error("Attempted to create ticket without category")
        raise ValueError("Category is required")
    
    # Validate category is valid
    valid_categories = [choice[0] for choice in MaintenanceTicket.CategoryChoices.choices]
    if category not in valid_categories:
        logger.error(f"Invalid category provided: {category}")
        raise ValueError(f"Category must be one of: {', '.join(valid_categories)}")
    
    try:
        with transaction.atomic():
            ticket = MaintenanceTicket(
                title=title.strip(),
                description=description.strip(),
                category=category,
                estate_id=estate_id,
                created_by=created_by,
                unit_id=unit_id,
                status=MaintenanceTicket.StatusChoices.OPEN,
                **kwargs
            )
            ticket.full_clean()
            ticket.save()
            
            logger.info(
                f"Successfully created maintenance ticket {ticket.id} "
                f"for estate {estate_id}"
            )
            return ticket
            
    except ValidationError as e:
        logger.error(f"Validation error creating maintenance ticket: {e}")
        raise
    except Exception as e:
        logger.error(f"Error creating maintenance ticket: {e}")
        raise ValueError(f"Failed to create maintenance ticket: {str(e)}")


def update_maintenance_ticket(
    *,
    ticket: MaintenanceTicket,
    user: "AbstractBaseUser",
    **update_fields
) -> MaintenanceTicket:
    """
    Update an existing maintenance ticket.
    
    Args:
        ticket: The MaintenanceTicket instance to update
        user: User performing the update
        **update_fields: Fields to update with their new values
        
    Returns:
        The updated MaintenanceTicket instance
        
    Raises:
        ValueError: If validation fails
        PermissionDenied: If user doesn't have permission to update
        ValidationError: If model validation fails
    """
    logger.info(f"Updating maintenance ticket {ticket.id} by user {user.id}")
    
    try:
        with transaction.atomic():
            # Update allowed fields
            for field, value in update_fields.items():
                if hasattr(ticket, field):
                    # Handle status change to resolved
                    if field == 'status' and value == MaintenanceTicket.StatusChoices.RESOLVED:
                        if ticket.status != MaintenanceTicket.StatusChoices.RESOLVED:
                            ticket.resolved_at = timezone.now()
                            logger.info(f"Ticket {ticket.id} marked as resolved")
                    
                    # Handle status change from resolved to open (reopening)
                    if field == 'status' and value == MaintenanceTicket.StatusChoices.OPEN:
                        if ticket.status == MaintenanceTicket.StatusChoices.RESOLVED:
                            ticket.resolved_at = None
                            # Update created_at to now so days_open reflects time since reopening
                            ticket.created_at = timezone.now()
                            logger.info(f"Ticket {ticket.id} reopened, created_at updated to {ticket.created_at}")
                    
                    # Strip string fields
                    if isinstance(value, str) and field in ['title', 'description']:
                        value = value.strip()
                    
                    setattr(ticket, field, value)
            
            ticket.full_clean()
            ticket.save()
            
            logger.info(f"Successfully updated maintenance ticket {ticket.id}")
            return ticket
            
    except ValidationError as e:
        logger.error(f"Validation error updating maintenance ticket: {e}")
        raise
    except Exception as e:
        logger.error(f"Error updating maintenance ticket: {e}")
        raise ValueError(f"Failed to update maintenance ticket: {str(e)}")


def resolve_maintenance_ticket(
    *,
    ticket: MaintenanceTicket,
    user: "AbstractBaseUser",
) -> MaintenanceTicket:
    """
    Mark a maintenance ticket as resolved.
    
    Args:
        ticket: The MaintenanceTicket instance to resolve
        user: User performing the action
        
    Returns:
        The resolved MaintenanceTicket instance
        
    Raises:
        ValueError: If ticket is already resolved
    """
    logger.info(f"Resolving maintenance ticket {ticket.id} by user {user.id}")
    
    if ticket.status == MaintenanceTicket.StatusChoices.RESOLVED:
        logger.warning(f"Attempted to resolve already resolved ticket {ticket.id}")
        raise ValueError("Ticket is already resolved")
    
    return update_maintenance_ticket(
        ticket=ticket,
        user=user,
        status=MaintenanceTicket.StatusChoices.RESOLVED
    )


def reopen_maintenance_ticket(
    *,
    ticket: MaintenanceTicket,
    user: "AbstractBaseUser",
) -> MaintenanceTicket:
    """
    Reopen a resolved maintenance ticket.
    
    When reopening, the created_at timestamp is updated to the current time
    so that days_open calculation reflects the time since reopening rather
    than the original creation date.
    
    Args:
        ticket: The MaintenanceTicket instance to reopen
        user: User performing the action
        
    Returns:
        The reopened MaintenanceTicket instance
        
    Raises:
        ValueError: If ticket is not resolved
    """
    logger.info(f"Reopening maintenance ticket {ticket.id} by user {user.id}")
    
    if ticket.status != MaintenanceTicket.StatusChoices.RESOLVED:
        logger.warning(f"Attempted to reopen ticket {ticket.id} that is not resolved")
        raise ValueError("Ticket is not resolved, cannot reopen")
    
    return update_maintenance_ticket(
        ticket=ticket,
        user=user,
        status=MaintenanceTicket.StatusChoices.OPEN
    )


def get_tickets_for_estate(
    *,
    estate_id: str,
    user: "AbstractBaseUser",
    status: Optional[str] = None,
    category: Optional[str] = None,
    unit_id: Optional[str] = None
) -> QuerySet[MaintenanceTicket]:
    """
    Get maintenance tickets for a specific estate with optional filtering.
    
    Args:
        estate_id: UUID of the estate
        user: User requesting the tickets
        status: Optional status filter (OPEN or RESOLVED)
        category: Optional category filter
        unit_id: Optional unit filter
        
    Returns:
        QuerySet of MaintenanceTicket instances
        
    Raises:
        ValueError: If invalid filters are provided
    """
    logger.info(
        f"Fetching maintenance tickets for estate {estate_id} by user {user.id}"
    )
    
    queryset = MaintenanceTicket.objects.filter(estate_id=estate_id).select_related(
        'created_by',
        'unit',
        'estate'
    )
    
    # Apply status filter
    if status:
        if status not in [choice[0] for choice in MaintenanceTicket.StatusChoices.choices]:
            logger.error(f"Invalid status filter: {status}")
            raise ValueError(f"Invalid status: {status}")
        queryset = queryset.filter(status=status)
    
    # Apply category filter
    if category:
        if category not in [choice[0] for choice in MaintenanceTicket.CategoryChoices.choices]:
            logger.error(f"Invalid category filter: {category}")
            raise ValueError(f"Invalid category: {category}")
        queryset = queryset.filter(category=category)
    
    # Apply unit filter
    if unit_id:
        queryset = queryset.filter(unit_id=unit_id)
    
    logger.info(f"Returning {queryset.count()} tickets for estate {estate_id}")
    return queryset


def get_tickets_created_by_user(
    *,
    user: "AbstractBaseUser",
    status: Optional[str] = None
) -> QuerySet[MaintenanceTicket]:
    """
    Get all maintenance tickets created by a specific user.
    
    Args:
        user: The user who created the tickets
        status: Optional status filter
        
    Returns:
        QuerySet of MaintenanceTicket instances
    """
    logger.info(f"Fetching tickets created by user {user.id}")
    
    queryset = MaintenanceTicket.objects.filter(
        created_by=user
    ).select_related('created_by', 'unit', 'estate')
    
    if status:
        queryset = queryset.filter(status=status)
    
    return queryset


def search_tickets(
    *,
    estate_id: str,
    user: "AbstractBaseUser",
    search_term: str
) -> QuerySet[MaintenanceTicket]:
    """
    Search maintenance tickets by title or description.
    
    Args:
        estate_id: UUID of the estate to search within
        user: User performing the search
        search_term: Text to search for
        
    Returns:
        QuerySet of matching MaintenanceTicket instances
    """
    logger.info(
        f"Searching tickets in estate {estate_id} for term: {search_term}"
    )
    
    queryset = MaintenanceTicket.objects.filter(
        estate_id=estate_id
    ).filter(
        Q(title__icontains=search_term) | Q(description__icontains=search_term)
    ).select_related('created_by', 'unit', 'estate')
    
    logger.info(f"Found {queryset.count()} matching tickets")
    return queryset


def delete_maintenance_ticket(
    *,
    ticket: MaintenanceTicket,
    user: "AbstractBaseUser",
) -> None:
    """
    Delete a maintenance ticket.
    
    Args:
        ticket: The MaintenanceTicket instance to delete
        user: User performing the deletion
        
    Raises:
        PermissionDenied: If user doesn't have permission to delete
    """
    logger.info(f"Deleting maintenance ticket {ticket.id} by user {user.id}")
    
    ticket_id = ticket.id
    ticket.delete()
    
    logger.info(f"Successfully deleted maintenance ticket {ticket_id}")


def get_ticket_statistics(
    *,
    estate_id: str,
    user: "AbstractBaseUser",
) -> Dict[str, Any]:
    """
    Get statistics for maintenance tickets in an estate.
    
    Args:
        estate_id: UUID of the estate
        user: User requesting statistics
        
    Returns:
        Dictionary containing ticket statistics
    """
    logger.info(f"Calculating ticket statistics for estate {estate_id}")
    
    tickets = MaintenanceTicket.objects.filter(estate_id=estate_id)
    
    stats = {
        'total_tickets': tickets.count(),
        'open_tickets': tickets.filter(status=MaintenanceTicket.StatusChoices.OPEN).count(),
        'resolved_tickets': tickets.filter(status=MaintenanceTicket.StatusChoices.RESOLVED).count(),
        'by_category': {}
    }
    
    # Count by category
    for category_choice in MaintenanceTicket.CategoryChoices.choices:
        category_code = category_choice[0]
        category_name = category_choice[1]
        count = tickets.filter(category=category_code).count()
        stats['by_category'][category_name] = count
    
    logger.info(f"Statistics calculated for estate {estate_id}: {stats}")
    return stats