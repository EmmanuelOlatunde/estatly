

# tests/test_permissions.py
"""
Tests for estates app permission classes.

Coverage:
- IsAuthenticatedOrReadOnly permission
- IsAdminOrReadOnly permission
- CanManageEstate permission
- View-level permissions
- Object-level permissions
"""

from unittest.mock import Mock
from rest_framework.test import APIRequestFactory
from estates.permissions import (
    IsAuthenticatedOrReadOnly,
    IsAdminOrReadOnly,
    CanManageEstate
)


class TestIsAuthenticatedOrReadOnly:
    """Test IsAuthenticatedOrReadOnly permission class."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.permission = IsAuthenticatedOrReadOnly()
        self.factory = APIRequestFactory()
        self.view = Mock()
    
    def test_allows_safe_methods_for_anyone(self):
        """Test that GET requests are allowed without authentication."""
        request = self.factory.get("/")
        request.user = Mock(is_authenticated=False)
        
        assert self.permission.has_permission(request, self.view) is True
    
    def test_denies_write_methods_for_unauthenticated(self):
        """Test that POST is denied for unauthenticated users."""
        request = self.factory.post("/")
        request.user = Mock(is_authenticated=False)
        
        assert self.permission.has_permission(request, self.view) is False
    
    def test_allows_write_methods_for_authenticated(self):
        """Test that POST is allowed for authenticated users."""
        request = self.factory.post("/")
        request.user = Mock(is_authenticated=True)
        
        assert self.permission.has_permission(request, self.view) is True


class TestIsAdminOrReadOnly:
    """Test IsAdminOrReadOnly permission class."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.permission = IsAdminOrReadOnly()
        self.factory = APIRequestFactory()
        self.view = Mock()
    
    def test_denies_unauthenticated_users(self):
        """Test that unauthenticated users are denied."""
        request = self.factory.get("/")
        request.user = Mock(is_authenticated=False)
        
        assert self.permission.has_permission(request, self.view) is False
    
    def test_allows_safe_methods_for_authenticated(self):
        """Test that GET is allowed for authenticated users."""
        request = self.factory.get("/")
        request.user = Mock(is_authenticated=True, is_staff=False, is_superuser=False)
        
        assert self.permission.has_permission(request, self.view) is True
    
    def test_denies_write_methods_for_non_admin(self):
        """Test that POST is denied for non-admin users."""
        request = self.factory.post("/")
        request.user = Mock(is_authenticated=True, is_staff=False, is_superuser=False)
        
        assert self.permission.has_permission(request, self.view) is False
    
    def test_allows_write_methods_for_staff(self):
        """Test that POST is allowed for staff users."""
        request = self.factory.post("/")
        request.user = Mock(is_authenticated=True, is_staff=True, is_superuser=False)
        
        assert self.permission.has_permission(request, self.view) is True
    
    def test_allows_write_methods_for_superuser(self):
        """Test that POST is allowed for superusers."""
        request = self.factory.post("/")
        request.user = Mock(is_authenticated=True, is_staff=False, is_superuser=True)
        
        assert self.permission.has_permission(request, self.view) is True


class TestCanManageEstate:
    """Test CanManageEstate permission class."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.permission = CanManageEstate()
        self.factory = APIRequestFactory()
        self.view = Mock()
        self.obj = Mock()
    
    def test_denies_unauthenticated_users(self):
        """Test that unauthenticated users are denied."""
        request = self.factory.get("/")
        request.user = Mock(is_authenticated=False)
        
        assert self.permission.has_permission(request, self.view) is False
    
    def test_allows_safe_methods_for_authenticated(self):
        """Test that GET is allowed for authenticated users."""
        request = self.factory.get("/")
        request.user = Mock(is_authenticated=True, is_staff=False, is_superuser=False)
        
        assert self.permission.has_permission(request, self.view) is True
    
    def test_denies_write_methods_for_non_staff(self):
        """Test that POST is denied for non-staff users."""
        request = self.factory.post("/")
        request.user = Mock(is_authenticated=True, is_staff=False, is_superuser=False)
        
        assert self.permission.has_permission(request, self.view) is False
    
    def test_allows_write_methods_for_staff(self):
        """Test that POST is allowed for staff users."""
        request = self.factory.post("/")
        request.user = Mock(is_authenticated=True, is_staff=True, is_superuser=False)
        
        assert self.permission.has_permission(request, self.view) is True
    
    def test_object_permission_safe_methods(self):
        """Test object-level permission for safe methods."""
        request = self.factory.get("/")
        request.user = Mock(is_authenticated=True, is_staff=False)
        
        assert self.permission.has_object_permission(request, self.view, self.obj) is True
    
    def test_object_permission_write_methods_non_staff(self):
        """Test object-level permission denies write for non-staff."""
        request = self.factory.delete("/")
        request.user = Mock(is_authenticated=True, is_staff=False, is_superuser=False)
        
        assert self.permission.has_object_permission(request, self.view, self.obj) is False
    
    def test_object_permission_write_methods_staff(self):
        """Test object-level permission allows write for staff."""
        request = self.factory.delete("/")
        request.user = Mock(is_authenticated=True, is_staff=True, is_superuser=False)
        
        assert self.permission.has_object_permission(request, self.view, self.obj) is True

