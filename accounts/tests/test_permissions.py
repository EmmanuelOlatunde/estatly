# tests/test_permissions.py
"""
Tests for accounts app custom permission classes.

Coverage:
- IsSuperAdmin permission
- IsSuperAdminOrSelf permission
- IsOwner permission
- IsSuperAdminOrReadOnly permission
"""

import pytest
from unittest.mock import Mock
from accounts.permissions import (
    IsSuperAdmin,
    IsSuperAdminOrSelf,
    IsOwner,
    IsSuperAdminOrReadOnly,
)
# from .factories import UserFactory


@pytest.mark.django_db
class TestIsSuperAdmin:
    """Test IsSuperAdmin permission class."""

    def test_super_admin_has_permission(self, super_admin):
        """Test super admin user has permission."""
        permission = IsSuperAdmin()
        request = Mock(user=super_admin)
        view = Mock()

        assert permission.has_permission(request, view) is True

    def test_regular_user_has_no_permission(self, authenticated_user):
        """Test regular user does not have permission."""
        permission = IsSuperAdmin()
        request = Mock(user=authenticated_user)
        view = Mock()

        assert permission.has_permission(request, view) is False

    def test_unauthenticated_user_has_no_permission(self):
        """Test unauthenticated user has no permission."""
        permission = IsSuperAdmin()
        request = Mock(user=Mock(is_authenticated=False))
        view = Mock()

        assert permission.has_permission(request, view) is False


@pytest.mark.django_db
class TestIsSuperAdminOrSelf:
    """Test IsSuperAdminOrSelf permission class."""

    def test_authenticated_user_has_view_permission(self, authenticated_user):
        """Test authenticated user has view-level permission."""
        permission = IsSuperAdminOrSelf()
        request = Mock(user=authenticated_user)
        view = Mock()

        assert permission.has_permission(request, view) is True

    def test_unauthenticated_user_has_no_permission(self):
        """Test unauthenticated user has no permission."""
        permission = IsSuperAdminOrSelf()
        request = Mock(user=Mock(is_authenticated=False))
        view = Mock()

        assert permission.has_permission(request, view) is False

    def test_super_admin_has_object_permission_for_any_user(self, super_admin, other_user):
        """Test super admin can access any user object."""
        permission = IsSuperAdminOrSelf()
        request = Mock(user=super_admin)
        view = Mock()

        assert permission.has_object_permission(request, view, other_user) is True

    def test_user_has_object_permission_for_self(self, authenticated_user):
        """Test user can access their own object."""
        permission = IsSuperAdminOrSelf()
        request = Mock(user=authenticated_user)
        view = Mock()

        assert permission.has_object_permission(request, view, authenticated_user) is True

    def test_user_has_no_object_permission_for_other_user(
        self, authenticated_user, other_user
    ):
        """Test user cannot access other user's object."""
        permission = IsSuperAdminOrSelf()
        request = Mock(user=authenticated_user)
        view = Mock()

        assert permission.has_object_permission(request, view, other_user) is False


@pytest.mark.django_db
class TestIsOwner:
    """Test IsOwner permission class."""

    def test_owner_has_object_permission(self, authenticated_user):
        """Test owner has permission for their object."""
        permission = IsOwner()
        request = Mock(user=authenticated_user)
        view = Mock()

        assert permission.has_object_permission(request, view, authenticated_user) is True

    def test_non_owner_has_no_object_permission(self, authenticated_user, other_user):
        """Test non-owner has no permission for other's object."""
        permission = IsOwner()
        request = Mock(user=authenticated_user)
        view = Mock()

        assert permission.has_object_permission(request, view, other_user) is False


@pytest.mark.django_db
class TestIsSuperAdminOrReadOnly:
    """Test IsSuperAdminOrReadOnly permission class."""

    def test_unauthenticated_user_has_no_permission(self):
        """Test unauthenticated user has no permission."""
        permission = IsSuperAdminOrReadOnly()
        request = Mock(user=Mock(is_authenticated=False), method='GET')
        view = Mock()

        assert permission.has_permission(request, view) is False

    def test_authenticated_user_has_read_permission(self, authenticated_user):
        """Test authenticated user has read permission."""
        permission = IsSuperAdminOrReadOnly()
        request = Mock(user=authenticated_user, method='GET')
        view = Mock()

        assert permission.has_permission(request, view) is True

    def test_regular_user_has_no_write_permission(self, authenticated_user):
        """Test regular user has no write permission."""
        permission = IsSuperAdminOrReadOnly()
        request = Mock(user=authenticated_user, method='POST')
        view = Mock()

        assert permission.has_permission(request, view) is False

    def test_super_admin_has_write_permission(self, super_admin):
        """Test super admin has write permission."""
        permission = IsSuperAdminOrReadOnly()
        request = Mock(user=super_admin, method='POST')
        view = Mock()

        assert permission.has_permission(request, view) is True

    def test_object_level_read_permission(self, authenticated_user, other_user):
        """Test object-level read permission."""
        permission = IsSuperAdminOrReadOnly()
        request = Mock(user=authenticated_user, method='GET')
        view = Mock()

        assert permission.has_object_permission(request, view, other_user) is True

    def test_object_level_write_permission_denied_for_regular_user(
        self, authenticated_user, other_user
    ):
        """Test object-level write permission denied for regular user."""
        permission = IsSuperAdminOrReadOnly()
        request = Mock(user=authenticated_user, method='PUT')
        view = Mock()

        assert permission.has_object_permission(request, view, other_user) is False

    def test_object_level_write_permission_for_super_admin(
        self, super_admin, other_user
    ):
        """Test object-level write permission for super admin."""
        permission = IsSuperAdminOrReadOnly()
        request = Mock(user=super_admin, method='PUT')
        view = Mock()

        assert permission.has_object_permission(request, view, other_user) is True