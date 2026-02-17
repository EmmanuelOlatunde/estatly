# maintenance/permissions.py
"""
Custom permission classes for the maintenance app.
"""

import logging
from rest_framework import permissions
from rest_framework.request import Request
from rest_framework.views import APIView

from estates.models import Estate

logger = logging.getLogger(__name__)


def _get_user_estate(user):
    """
    Safely return the user's estate via reverse OneToOne, or None.

    All three permission classes need this. Bare attribute access
    (user.estate) raises Estate.DoesNotExist when no estate is assigned
    instead of returning None, which would turn permission denials into 500s.
    """
    try:
        return user.estate
    except Estate.DoesNotExist:
        return None


class CanCreateTicket(permissions.BasePermission):
    """
    Allow ticket creation only for the estate the user manages.

    Super admins may create tickets for any estate.
    Estate managers may only create tickets for their own estate.
    """

    def has_permission(self, request: Request, view: APIView) -> bool:
        if not request.user or not request.user.is_authenticated:
            logger.warning("Unauthenticated user attempted to create ticket")
            return False

        if request.user.is_superuser:
            return True

        if request.method == 'POST':
            estate_id = request.data.get('estate')
            if not estate_id:
                logger.warning(
                    f"User {request.user.id} attempted to create ticket "
                    f"without estate_id"
                )
                return False

            estate = _get_user_estate(request.user)
            if not estate:
                logger.warning(
                    f"User {request.user.id} has no estate assigned"
                )
                return False

            if str(estate.id) != str(estate_id):
                logger.warning(
                    f"User {request.user.id} attempted to create ticket for "
                    f"estate {estate_id} but manages estate {estate.id}"
                )
                return False

        return True


class IsTicketCreatorOrAdmin(permissions.BasePermission):
    """
    Object-level permission: allow access only to the ticket creator or a superuser,
    and only when the ticket belongs to the user's estate.

    Note: is_staff (estate managers) are NOT treated as admins here —
    only is_superuser bypasses the creator check.
    """

    def has_object_permission(self, request: Request, view: APIView, obj) -> bool:
        if request.user.is_superuser:
            return True

        estate = _get_user_estate(request.user)
        if not estate:
            logger.warning(
                f"User {request.user.id} has no estate assigned, "
                f"denied access to ticket {obj.id}"
            )
            return False

        if obj.estate_id != estate.id:
            logger.warning(
                f"User {request.user.id} from estate {estate.id} denied "
                f"access to ticket {obj.id} from estate {obj.estate_id}"
            )
            return False

        is_creator = obj.created_by == request.user
        if not is_creator:
            logger.warning(
                f"User {request.user.id} is not the creator of ticket {obj.id} "
                f"(creator: {obj.created_by.id})"
            )
        return is_creator


class CanAccessEstate(permissions.BasePermission):
    """
    Allow access to estate-scoped data only for users who manage that estate.

    Super admins may access any estate.
    Estate managers may only access their own estate.
    Used on the statistics endpoint.
    """

    def has_permission(self, request: Request, view: APIView) -> bool:
        if not request.user or not request.user.is_authenticated:
            return False

        if request.user.is_superuser:
            return True

        estate_id = request.query_params.get('estate_id')
        if estate_id:
            estate = _get_user_estate(request.user)
            if not estate:
                logger.warning(
                    f"User {request.user.id} has no estate assigned"
                )
                return False

            if str(estate.id) != str(estate_id):
                logger.warning(
                    f"User {request.user.id} attempted to access statistics "
                    f"for estate {estate_id} but manages estate {estate.id}"
                )
                return False

        return True


class IsEstateManagerOrReadOnly(permissions.BasePermission):
    """
    Allow estate managers to modify tickets; authenticated users get read-only access.

    Not currently wired up in get_permissions() but kept for future use.
    """

    def has_permission(self, request: Request, view: APIView) -> bool:
        if request.method in permissions.SAFE_METHODS:
            return bool(request.user and request.user.is_authenticated)
        return bool(request.user and request.user.is_authenticated)

    def has_object_permission(self, request: Request, view: APIView, obj) -> bool:
        if request.method in permissions.SAFE_METHODS:
            return True

        is_creator = obj.created_by == request.user
        if not (is_creator or request.user.is_superuser):
            logger.warning(
                f"User {request.user.id} denied permission to modify ticket {obj.id}"
            )
        return is_creator or request.user.is_superuser