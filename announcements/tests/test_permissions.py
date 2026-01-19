# tests/test_permissions.py

"""
Tests for announcements permission classes.

Coverage:
- IsManagerOrReadOnly permission
- IsOwnerOrReadOnly permission
- IsManager permission
- Permission edge cases
"""

import pytest
from rest_framework.test import APIRequestFactory
from announcements.permissions import IsManagerOrReadOnly, IsOwnerOrReadOnly, IsManager
from announcements import views
from .factories import UserFactory, AnnouncementFactory


@pytest.mark.django_db
class TestIsManagerOrReadOnly:
    """Test IsManagerOrReadOnly permission class."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.factory = APIRequestFactory()
        self.permission = IsManagerOrReadOnly()
        self.view = views.AnnouncementViewSet()
    
    def test_anonymous_user_denied(self):
        """Test anonymous users are denied access."""
        request = self.factory.get('/')
        request.user = None
        
        assert not self.permission.has_permission(request, self.view)
    
    def test_authenticated_user_can_read(self):
        """Test authenticated users can read."""
        user = UserFactory.create(is_staff=False)
        request = self.factory.get('/')
        request.user = user
        
        assert self.permission.has_permission(request, self.view)
    
    def test_non_manager_cannot_write(self):
        """Test non-managers cannot create announcements."""
        user = UserFactory.create(is_staff=False)
        request = self.factory.post('/')
        request.user = user
        
        assert not self.permission.has_permission(request, self.view)
    
    def test_staff_user_can_write(self):
        """Test staff users can create announcements."""
        user = UserFactory.create(is_staff=True)
        request = self.factory.post('/')
        request.user = user
        
        assert self.permission.has_permission(request, self.view)
    
    def test_superuser_can_write(self):
        """Test superusers can create announcements."""
        user = UserFactory.create(is_superuser=True)
        request = self.factory.post('/')
        request.user = user
        
        assert self.permission.has_permission(request, self.view)


@pytest.mark.django_db
class TestIsOwnerOrReadOnly:
    """Test IsOwnerOrReadOnly permission class."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.factory = APIRequestFactory()
        self.permission = IsOwnerOrReadOnly()
        self.view = views.AnnouncementViewSet()
    
    def test_anonymous_user_denied(self):
        """Test anonymous users are denied access."""
        request = self.factory.get('/')
        request.user = None
        
        assert not self.permission.has_permission(request, self.view)
    
    def test_authenticated_user_granted_view_permission(self):
        """Test authenticated users granted view-level permission."""
        user = UserFactory.create()
        request = self.factory.get('/')
        request.user = user
        
        assert self.permission.has_permission(request, self.view)
    
    def test_owner_can_read_own_announcement(self):
        """Test owner can read their own announcement."""
        user = UserFactory.create(is_staff=True)
        announcement = AnnouncementFactory.create(created_by=user)
        request = self.factory.get('/')
        request.user = user
        
        assert self.permission.has_object_permission(request, self.view, announcement)
    
    def test_non_owner_can_read_active_announcement(self):
        """Test non-owner can read active announcements."""
        user = UserFactory.create()
        other_user = UserFactory.create(is_staff=True)
        announcement = AnnouncementFactory.create(created_by=other_user, is_active=True)
        request = self.factory.get('/')
        request.user = user
        
        assert self.permission.has_object_permission(request, self.view, announcement)
    
    def test_non_owner_cannot_read_inactive_announcement(self):
        """Test non-owner cannot read inactive announcements."""
        user = UserFactory.create()
        other_user = UserFactory.create(is_staff=True)
        announcement = AnnouncementFactory.create(created_by=other_user, is_active=False)
        request = self.factory.get('/')
        request.user = user
        
        assert not self.permission.has_object_permission(request, self.view, announcement)
    
    def test_owner_can_update_own_announcement(self):
        """Test owner can update their own announcement."""
        user = UserFactory.create(is_staff=True)
        announcement = AnnouncementFactory.create(created_by=user)
        request = self.factory.patch('/')
        request.user = user
        
        assert self.permission.has_object_permission(request, self.view, announcement)
    
    def test_non_owner_cannot_update_announcement(self):
        """Test non-owner cannot update announcements."""
        user = UserFactory.create(is_staff=True)
        other_user = UserFactory.create(is_staff=True)
        announcement = AnnouncementFactory.create(created_by=other_user)
        request = self.factory.patch('/')
        request.user = user
        
        assert not self.permission.has_object_permission(request, self.view, announcement)
    
    def test_superuser_can_update_any_announcement(self):
        """Test superuser can update any announcement."""
        user = UserFactory.create(is_superuser=True)
        other_user = UserFactory.create(is_staff=True)
        announcement = AnnouncementFactory.create(created_by=other_user)
        request = self.factory.patch('/')
        request.user = user
        
        assert self.permission.has_object_permission(request, self.view, announcement)


@pytest.mark.django_db
class TestIsManager:
    """Test IsManager permission class."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.factory = APIRequestFactory()
        self.permission = IsManager()
        self.view = views.AnnouncementViewSet()
    
    def test_anonymous_user_denied(self):
        """Test anonymous users are denied."""
        request = self.factory.get('/')
        request.user = None
        
        assert not self.permission.has_permission(request, self.view)
    
    def test_regular_user_denied(self):
        """Test regular users are denied."""
        user = UserFactory.create(is_staff=False)
        request = self.factory.get('/')
        request.user = user
        
        assert not self.permission.has_permission(request, self.view)
    
    def test_staff_user_granted(self):
        """Test staff users are granted access."""
        user = UserFactory.create(is_staff=True)
        request = self.factory.get('/')
        request.user = user
        
        assert self.permission.has_permission(request, self.view)
    
    def test_superuser_granted(self):
        """Test superusers are granted access."""
        user = UserFactory.create(is_superuser=True)
        request = self.factory.get('/')
        request.user = user
        
        assert self.permission.has_permission(request, self.view)