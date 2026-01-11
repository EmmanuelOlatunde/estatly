# tests/test_permissions.py
"""
Tests for units app permission classes.

Coverage:
- IsOwner permission
- IsOwnerOrReadOnly permission
- IsActiveUnit permission
- Authentication checks
- Object-level permission checks
"""

import pytest
from rest_framework.test import APIRequestFactory
from rest_framework.views import APIView
from units.permissions import IsOwner, IsOwnerOrReadOnly, IsActiveUnit
from .factories import UserFactory, UnitFactory


@pytest.mark.django_db
class TestIsOwnerPermission:
    """Test IsOwner permission class."""
    
    def test_unauthenticated_user_denied(self):
        """Test that unauthenticated users are denied access."""
        permission = IsOwner()
        factory = APIRequestFactory()
        request = factory.get("/")
        request.user = None
        
        view = APIView()
        assert not permission.has_permission(request, view)
    
    def test_authenticated_user_allowed_at_view_level(self):
        """Test that authenticated users pass view-level check."""
        permission = IsOwner()
        factory = APIRequestFactory()
        request = factory.get("/")
        request.user = UserFactory.build()
        
        view = APIView()
        assert permission.has_permission(request, view)
    
    def test_owner_can_access_own_unit(self):
        """Test that owner can access their own unit."""
        permission = IsOwner()
        factory = APIRequestFactory()
        user = UserFactory.create()
        unit = UnitFactory.create(owner=user)
        
        request = factory.get("/")
        request.user = user
        
        view = APIView()
        assert permission.has_object_permission(request, view, unit)
    
    def test_non_owner_cannot_access_unit(self):
        """Test that non-owner cannot access another user's unit."""
        permission = IsOwner()
        factory = APIRequestFactory()
        owner = UserFactory.create()
        other_user = UserFactory.create()
        unit = UnitFactory.create(owner=owner)
        
        request = factory.get("/")
        request.user = other_user
        
        view = APIView()
        assert not permission.has_object_permission(request, view, unit)


@pytest.mark.django_db
class TestIsOwnerOrReadOnlyPermission:
    """Test IsOwnerOrReadOnly permission class."""
    
    def test_authenticated_user_can_read(self):
        """Test that authenticated users can perform read operations."""
        permission = IsOwnerOrReadOnly()
        factory = APIRequestFactory()
        user = UserFactory.create()
        other_user = UserFactory.create()
        unit = UnitFactory.create(owner=other_user)
        
        request = factory.get("/")
        request.user = user
        
        view = APIView()
        assert permission.has_object_permission(request, view, unit)
    
    def test_owner_can_write(self):
        """Test that owner can perform write operations."""
        permission = IsOwnerOrReadOnly()
        factory = APIRequestFactory()
        user = UserFactory.create()
        unit = UnitFactory.create(owner=user)
        
        request = factory.post("/")
        request.user = user
        
        view = APIView()
        assert permission.has_object_permission(request, view, unit)
    
    def test_non_owner_cannot_write(self):
        """Test that non-owner cannot perform write operations."""
        permission = IsOwnerOrReadOnly()
        factory = APIRequestFactory()
        owner = UserFactory.create()
        other_user = UserFactory.create()
        unit = UnitFactory.create(owner=owner)
        
        request = factory.post("/")
        request.user = other_user
        
        view = APIView()
        assert not permission.has_object_permission(request, view, unit)


@pytest.mark.django_db
class TestIsActiveUnitPermission:
    """Test IsActiveUnit permission class."""
    
    def test_active_unit_allowed(self):
        """Test that active units are accessible."""
        permission = IsActiveUnit()
        factory = APIRequestFactory()
        user = UserFactory.create()
        unit = UnitFactory.create(owner=user, is_active=True)
        
        request = factory.get("/")
        request.user = user
        
        view = APIView()
        assert permission.has_object_permission(request, view, unit)
    
    def test_inactive_unit_denied(self):
        """Test that inactive units are not accessible."""
        permission = IsActiveUnit()
        factory = APIRequestFactory()
        user = UserFactory.create()
        unit = UnitFactory.create(owner=user, is_active=False)
        
        request = factory.get("/")
        request.user = user
        
        view = APIView()
        assert not permission.has_object_permission(request, view, unit)