# reports/permissions.py
import logging
from rest_framework.permissions import BasePermission
from accounts.models import User

logger = logging.getLogger(__name__)


class CanAccessReports(BasePermission):
    """
    Allows access to reports for:
    - Super Admins
    - Estate Managers WITH an assigned estate
    """

    message = "You do not have permission to access reports."

    def has_permission(self, request, view):
        user = request.user

        if not user or not user.is_authenticated:
            logger.warning("Unauthenticated access attempt to reports")
            return False

        # Super admins always allowed
        if user.is_superuser or user.role == User.Role.SUPER_ADMIN:
            logger.info(f"Super admin {user.id} granted report access")
            return True

        # Estate manager MUST have a valid estate_id
        if user.role == User.Role.ESTATE_MANAGER:
            if user.estate_id:
                logger.info(
                    f"Estate manager {user.id} granted report access for estate {user.estate_id}"
                )
                return True

            logger.warning(
                f"Estate manager {user.id} denied report access (no estate assigned)"
            )
            return False

        # Everyone else
        logger.warning(f"User {user.id} denied report access (invalid role)")
        return False