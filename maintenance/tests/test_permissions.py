# tests/test_permissions.py

"""
Tests for maintenance app permission classes.

Coverage:
- Permission class logic
- Object-level permissions
- Role-based access control
"""

import pytest
from rest_framework.test import APIRequestFactory
from maintenance.permissions import (
    IsEstateManagerOrReadOnly,
    CanCreateTicket,
    IsTicketCreatorOrAdmin,
)
from maintenance.views import MaintenanceTicketViewSet
from .factories import UserFactory, MaintenanceTicketFactory, EstateFactory


@pytest.mark.django_db
class TestIsEstateManagerOrReadOnly:
    """Test IsEstateManagerOrReadOnly permission class."""
    
    def setup_method(self):
        """Setup test request factory."""
        self.factory = APIRequestFactory()
        self.permission = IsEstateManagerOrReadOnly()
    
    def test_allows_authenticated_user_read_access(self, user):
        """Test authenticated users can read."""
        request = self.factory.get('/')
        request.user = user
        view = MaintenanceTicketViewSet()
        
        assert self.permission.has_permission(request, view) is True
    
    def test_denies_unauthenticated_user_read_access(self):
        """Test unauthenticated users cannot read."""
        from django.contrib.auth.models import AnonymousUser
        request = self.factory.get('/')
        request.user = AnonymousUser()
        view = MaintenanceTicketViewSet()
        
        assert self.permission.has_permission(request, view) is False
    
    def test_allows_authenticated_user_write_access(self, user):
        """Test authenticated users can write."""
        request = self.factory.post('/')
        request.user = user
        view = MaintenanceTicketViewSet()
        
        assert self.permission.has_permission(request, view) is True
    
    def test_creator_can_modify_own_ticket(self, user, estate):
        """Test creator has object-level permission for their ticket."""
        ticket = MaintenanceTicketFactory.create(created_by=user, estate=estate)
        request = self.factory.put('/')
        request.user = user
        view = MaintenanceTicketViewSet()
        
        assert self.permission.has_object_permission(request, view, ticket) is True
    
    def test_non_creator_cannot_modify_ticket(self, user, other_user, estate):
        """Test non-creator lacks object-level permission."""
        ticket = MaintenanceTicketFactory.create(created_by=other_user, estate=estate)
        request = self.factory.put('/')
        request.user = user
        view = MaintenanceTicketViewSet()
        
        assert self.permission.has_object_permission(request, view, ticket) is False
    
    def test_staff_can_modify_any_ticket(self, admin_user, other_user, estate):
        """Test staff users can modify any ticket."""
        ticket = MaintenanceTicketFactory.create(created_by=other_user, estate=estate)
        request = self.factory.put('/')
        request.user = admin_user
        view = MaintenanceTicketViewSet()
        
        assert self.permission.has_object_permission(request, view, ticket) is True


@pytest.mark.django_db
class TestCanCreateTicket:
    """Test CanCreateTicket permission class."""
    
    def setup_method(self):
        """Setup test request factory."""
        self.factory = APIRequestFactory()
        self.permission = CanCreateTicket()
    
    def test_authenticated_user_can_create_ticket(self, user):
        """Test authenticated users can create tickets."""
        request = self.factory.post('/')
        request.user = user
        view = MaintenanceTicketViewSet()
        
        assert self.permission.has_permission(request, view) is True
    
    def test_unauthenticated_user_cannot_create_ticket(self):
        """Test unauthenticated users cannot create tickets."""
        from django.contrib.auth.models import AnonymousUser
        request = self.factory.post('/')
        request.user = AnonymousUser()
        view = MaintenanceTicketViewSet()
        
        assert self.permission.has_permission(request, view) is False


@pytest.mark.django_db
class TestIsTicketCreatorOrAdmin:
    """Test IsTicketCreatorOrAdmin permission class."""
    
    def setup_method(self):
        """Setup test request factory."""
        self.factory = APIRequestFactory()
        self.permission = IsTicketCreatorOrAdmin()
    
    def test_creator_has_object_permission(self, user, estate):
        """Test ticket creator has permission."""
        ticket = MaintenanceTicketFactory.create(created_by=user, estate=estate)
        request = self.factory.get('/')
        request.user = user
        view = MaintenanceTicketViewSet()
        
        assert self.permission.has_object_permission(request, view, ticket) is True
    
    def test_non_creator_lacks_object_permission(self, user, other_user, estate):
        """Test non-creator lacks permission."""
        ticket = MaintenanceTicketFactory.create(created_by=other_user, estate=estate)
        request = self.factory.get('/')
        request.user = user
        view = MaintenanceTicketViewSet()
        
        assert self.permission.has_object_permission(request, view, ticket) is False
    
    def test_admin_has_object_permission(self, admin_user, other_user, estate):
        """Test admin has permission for any ticket."""
        ticket = MaintenanceTicketFactory.create(created_by=other_user, estate=estate)
        request = self.factory.get('/')
        request.user = admin_user
        view = MaintenanceTicketViewSet()
        
        assert self.permission.has_object_permission(request, view, ticket) is True