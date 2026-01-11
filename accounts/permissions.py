from rest_framework.permissions import BasePermission, SAFE_METHODS


class IsSuperAdmin(BasePermission):
    """
    Allows access only to super admins.
    """

    def has_permission(self, request, view):
        return (
            request.user
            and request.user.is_authenticated
            and request.user.is_super_admin()
        )


class IsSuperAdminOrSelf(BasePermission):
    """
    Super admins can do anything.
    Regular users can only retrieve/update themselves.
    """

    def has_permission(self, request, view):
        # Must be authenticated for any access
        if not request.user or not request.user.is_authenticated:
            return False

        # Only super admins can CREATE users
        if view.action == "create":
            return request.user.is_super_admin()

        return True

    def has_object_permission(self, request, view, obj):
        # Super admins can access any user
        if request.user.is_super_admin():
            return True

        # Regular users can only access themselves
        return obj == request.user


class IsOwner(BasePermission):
    """
    Object-level permission that allows access only to the owner.

    Supports:
    - User objects (obj == request.user)
    - User-owned objects (obj.user == request.user)
    """

    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated

    def has_object_permission(self, request, view, obj):
        # Case 1: the object itself IS the user
        if obj == request.user:
            return True

        # Case 2: the object has a `user` attribute
        owner = getattr(obj, "user", None)
        return owner == request.user




class IsSuperAdminOrReadOnly(BasePermission):
    """
    Read-only for authenticated users.
    Write access only for super admins.
    """

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False

        if request.method in SAFE_METHODS:
            return True

        return request.user.is_super_admin()

    def has_object_permission(self, request, view, obj):
        if request.method in SAFE_METHODS:
            return True

        return request.user.is_super_admin()
