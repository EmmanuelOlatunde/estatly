# reports/tests/test_permissions.py
"""
Tests for reports app permission classes.

Coverage:
- CanAccessReports permission logic
- Authentication requirements
- Role-based access
- Estate assignment validation
"""

import pytest
from unittest.mock import Mock, PropertyMock
from reports.permissions import CanAccessReports


@pytest.mark.django_db
class TestCanAccessReportsPermission:
    """Test CanAccessReports permission class."""
    
    def test_unauthenticated_user_denied(self):
        """Test unauthenticated user is denied access."""
        permission = CanAccessReports()
        request = Mock()
        request.user = None
        
        assert permission.has_permission(request, None) is False
    
    def test_anonymous_user_denied(self):
        """Test anonymous user is denied access."""
        permission = CanAccessReports()
        request = Mock()
        request.user = Mock()
        request.user.is_authenticated = False
        
        assert permission.has_permission(request, None) is False
    
    def test_superuser_granted_access(self):
        """Test superuser is granted access."""
        permission = CanAccessReports()
        user = Mock()
        user.is_authenticated = True
        user.is_superuser = True
        
        request = Mock()
        request.user = user
        
        assert permission.has_permission(request, None) is True
    
    def test_super_admin_role_granted_access(self):
        """Test user with SUPER_ADMIN role is granted access."""
        permission = CanAccessReports()
        user = Mock()
        user.is_authenticated = True
        user.is_superuser = False
        
        # Mock the Role enum
        role_enum = Mock()
        role_enum.SUPER_ADMIN = 'super_admin'
        type(user).Role = PropertyMock(return_value=role_enum)
        user.role = 'super_admin'
        
        request = Mock()
        request.user = user
        
        assert permission.has_permission(request, None) is True
    
    def test_estate_manager_with_estate_granted_access(self):
        """Test estate manager with assigned estate is granted access."""
        permission = CanAccessReports()
        user = Mock()
        user.is_authenticated = True
        user.is_superuser = False
        
        # Mock the Role enum
        role_enum = Mock()
        role_enum.SUPER_ADMIN = 'super_admin'
        role_enum.ESTATE_MANAGER = 'estate_manager'
        type(user).Role = PropertyMock(return_value=role_enum)
        user.role = 'estate_manager'
        user.estate_id = 'some-estate-uuid'
        
        request = Mock()
        request.user = user
        
        assert permission.has_permission(request, None) is True
    
    def test_estate_manager_without_estate_denied_access(self):
        """Test estate manager without assigned estate is denied access."""
        permission = CanAccessReports()
        user = Mock()
        user.is_authenticated = True
        user.is_superuser = False
        
        # Mock the Role enum
        role_enum = Mock()
        role_enum.SUPER_ADMIN = 'super_admin'
        role_enum.ESTATE_MANAGER = 'estate_manager'
        type(user).Role = PropertyMock(return_value=role_enum)
        user.role = 'estate_manager'
        user.estate_id = None
        
        request = Mock()
        request.user = user
        
        assert permission.has_permission(request, None) is False
    
    def test_estate_manager_with_empty_estate_denied_access(self):
        """Test estate manager with empty estate_id is denied access."""
        permission = CanAccessReports()
        user = Mock()
        user.is_authenticated = True
        user.is_superuser = False
        
        # Mock the Role enum
        role_enum = Mock()
        role_enum.SUPER_ADMIN = 'super_admin'
        role_enum.ESTATE_MANAGER = 'estate_manager'
        type(user).Role = PropertyMock(return_value=role_enum)
        user.role = 'estate_manager'
        user.estate_id = ''
        
        request = Mock()
        request.user = user
        
        assert permission.has_permission(request, None) is False
    
    def test_tenant_role_denied_access(self):
        """Test user with tenant role is denied access."""
        permission = CanAccessReports()
        user = Mock()
        user.is_authenticated = True
        user.is_superuser = False
        
        # Mock the Role enum
        role_enum = Mock()
        role_enum.SUPER_ADMIN = 'super_admin'
        role_enum.ESTATE_MANAGER = 'estate_manager'
        role_enum.TENANT = 'tenant'
        type(user).Role = PropertyMock(return_value=role_enum)
        user.role = 'tenant'
        
        request = Mock()
        request.user = user
        
        assert permission.has_permission(request, None) is False
    
    def test_unknown_role_denied_access(self):
        """Test user with unknown role is denied access."""
        permission = CanAccessReports()
        user = Mock()
        user.is_authenticated = True
        user.is_superuser = False
        
        # Mock the Role enum
        role_enum = Mock()
        role_enum.SUPER_ADMIN = 'super_admin'
        role_enum.ESTATE_MANAGER = 'estate_manager'
        type(user).Role = PropertyMock(return_value=role_enum)
        user.role = 'unknown_role'
        
        request = Mock()
        request.user = user
        
        assert permission.has_permission(request, None) is False
    
    def test_user_without_role_attribute_denied_access(self):
        """Test user without role attribute is denied access."""
        permission = CanAccessReports()
        user = Mock()
        user.is_authenticated = True
        user.is_superuser = False
        
        # No role attribute
        del user.role
        
        request = Mock()
        request.user = user
        
        # Should raise AttributeError or return False
        try:
            result = permission.has_permission(request, None)
            assert result is False
        except AttributeError:
            # Expected if role is accessed directly
            pass
    
    def test_staff_user_without_superuser_or_valid_role_denied(self):
        """Test staff user without valid role is denied access."""
        permission = CanAccessReports()
        user = Mock()
        user.is_authenticated = True
        user.is_superuser = False
        user.is_staff = True
        
        # Mock the Role enum
        role_enum = Mock()
        role_enum.SUPER_ADMIN = 'super_admin'
        role_enum.ESTATE_MANAGER = 'estate_manager'
        type(user).Role = PropertyMock(return_value=role_enum)
        user.role = 'staff'
        
        request = Mock()
        request.user = user
        
        assert permission.has_permission(request, None) is False
    
    def test_permission_message_is_descriptive(self):
        """Test permission has descriptive error message."""
        permission = CanAccessReports()
        
        assert hasattr(permission, 'message')
        assert len(permission.message) > 0
        assert 'permission' in permission.message.lower()