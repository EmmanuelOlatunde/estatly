# reports/permissions.py
"""
Permission classes for reports app.
"""

import logging
from rest_framework.permissions import BasePermission
from django.contrib.auth import get_user_model
from estates.models import Estate

User = get_user_model()
logger = logging.getLogger(__name__)


class CanAccessReports(BasePermission):
    """
    Grants report access to Super Admins and Estate Managers.

    Super Admins always pass.
    Estate Managers pass only if they have an estate assigned via the
    reverse OneToOne relation on Estate.manager. If no estate exists
    for this user, access is denied.

    NOTE: user.estate_id no longer exists — the FK column lives on the
    Estate table (Estate.manager), not on the User table. Always access
    the estate through the reverse relation: user.estate.
    """

    def has_permission(self, request, view):
        user = request.user

        if not user or not user.is_authenticated:
            return False

        # Super Admin has full access
        if user.role == User.Role.SUPER_ADMIN:
            logger.info(f"Super admin {user.id} granted report access")
            return True

        # Estate Manager must have an estate assigned
        if user.role == User.Role.ESTATE_MANAGER:
            try:
                estate = user.estate  # reverse OneToOne — may raise DoesNotExist
                logger.info(
                    f"Estate manager {user.id} granted report access "
                    f"for estate {estate.id}"
                )
                return True
            except Estate.DoesNotExist:
                logger.warning(
                    f"Estate manager {user.id} denied report access "
                    f"(no estate assigned)"
                )
                return False

        # Any other role is denied
        logger.warning(
            f"User {user.id} with role '{user.role}' denied report access"
        )
        return False