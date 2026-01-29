# tests/test_permissions.py
"""
Tests for documents app permission classes.

Coverage:
- IsDocumentOwnerOrAdmin permission
- CanDownloadDocument permission
- IsAdminOrReadOnly permission
- CanViewDocumentDownloads permission
"""

import pytest
from unittest.mock import Mock
from documents.permissions import (
    IsDocumentOwnerOrAdmin,
    CanDownloadDocument,
    IsAdminOrReadOnly,
    CanViewDocumentDownloads,
)
from documents.models import DocumentStatus
from .factories import UserFactory, DocumentFactory, CompletedDocumentFactory


@pytest.mark.django_db
class TestIsDocumentOwnerOrAdmin:
    """Test IsDocumentOwnerOrAdmin permission class."""
    
    def test_requires_authentication(self):
        """Unauthenticated users are denied."""
        permission = IsDocumentOwnerOrAdmin()
        request = Mock(user=Mock(is_authenticated=False))
        
        assert not permission.has_permission(request, None)
    
    def test_authenticated_user_has_view_permission(self):
        """Authenticated users can access view."""
        permission = IsDocumentOwnerOrAdmin()
        request = Mock(user=Mock(is_authenticated=True))
        
        assert permission.has_permission(request, None)
    
    def test_owner_can_access_own_document(self):
        """User can access their own document."""
        user = UserFactory.create()
        document = DocumentFactory.create(related_user=user)
        
        permission = IsDocumentOwnerOrAdmin()
        request = Mock(user=user)
        
        assert permission.has_object_permission(request, None, document)
    
    def test_non_owner_cannot_access_document(self):
        """User cannot access another user's document."""
        owner = UserFactory.create()
        other_user = UserFactory.create()
        document = DocumentFactory.create(related_user=owner)
        
        permission = IsDocumentOwnerOrAdmin()
        request = Mock(user=other_user)
        
        assert not permission.has_object_permission(request, None, document)
    
    def test_admin_can_access_any_document(self):
        """Admin users can access any document."""
        owner = UserFactory.create()
        admin = UserFactory.create(is_staff=True)
        document = DocumentFactory.create(related_user=owner)
        
        permission = IsDocumentOwnerOrAdmin()
        request = Mock(user=admin)
        
        assert permission.has_object_permission(request, None, document)
    
    def test_superuser_can_access_any_document(self):
        """Superusers can access any document."""
        owner = UserFactory.create()
        superuser = UserFactory.create(is_superuser=True)
        document = DocumentFactory.create(related_user=owner)
        
        permission = IsDocumentOwnerOrAdmin()
        request = Mock(user=superuser)
        
        assert permission.has_object_permission(request, None, document)
    
    def test_document_without_related_user_denied(self):
        """Documents without related_user are denied."""
        user = UserFactory.create()
        document = DocumentFactory.create(related_user=None)
        
        permission = IsDocumentOwnerOrAdmin()
        request = Mock(user=user)
        
        assert not permission.has_object_permission(request, None, document)


@pytest.mark.django_db
class TestCanDownloadDocument:
    """Test CanDownloadDocument permission class."""
    
    def test_requires_authentication(self):
        """Unauthenticated users cannot download."""
        permission = CanDownloadDocument()
        request = Mock(user=Mock(is_authenticated=False))
        
        assert not permission.has_permission(request, None)
    
    def test_cannot_download_deleted_document(self):
        """Cannot download soft-deleted documents."""
        user = UserFactory.create()
        document = CompletedDocumentFactory.create(
            related_user=user,
            is_deleted=True
        )
        
        permission = CanDownloadDocument()
        request = Mock(user=user)
        
        assert not permission.has_object_permission(request, None, document)
    
    def test_cannot_download_incomplete_document(self):
        """Cannot download documents that are not completed."""
        user = UserFactory.create()
        document = DocumentFactory.create(
            related_user=user,
            status=DocumentStatus.PENDING
        )
        
        permission = CanDownloadDocument()
        request = Mock(user=user)
        
        assert not permission.has_object_permission(request, None, document)
    
    def test_cannot_download_document_without_file(self):
        """Cannot download documents without file attached."""
        user = UserFactory.create()
        document = DocumentFactory.create(
            related_user=user,
            status=DocumentStatus.COMPLETED,
            file=None
        )
        
        permission = CanDownloadDocument()
        request = Mock(user=user)
        
        assert not permission.has_object_permission(request, None, document)
    
    def test_owner_can_download_completed_document(self):
        """Owner can download their completed document."""
        user = UserFactory.create()
        document = CompletedDocumentFactory.create(related_user=user)
        
        permission = CanDownloadDocument()
        request = Mock(user=user)
        
        assert permission.has_object_permission(request, None, document)
    
    def test_non_owner_cannot_download(self):
        """Non-owner cannot download document."""
        owner = UserFactory.create()
        other_user = UserFactory.create()
        document = CompletedDocumentFactory.create(related_user=owner)
        
        permission = CanDownloadDocument()
        request = Mock(user=other_user)
        
        assert not permission.has_object_permission(request, None, document)
    
    def test_admin_can_download_any_document(self):
        """Admin can download any user's document."""
        owner = UserFactory.create()
        admin = UserFactory.create(is_staff=True)
        document = CompletedDocumentFactory.create(related_user=owner)
        
        permission = CanDownloadDocument()
        request = Mock(user=admin)
        
        assert permission.has_object_permission(request, None, document)


@pytest.mark.django_db
class TestIsAdminOrReadOnly:
    """Test IsAdminOrReadOnly permission class."""
    
    def test_unauthenticated_user_denied(self):
        """Unauthenticated users are denied."""
        permission = IsAdminOrReadOnly()
        request = Mock(user=None)
        
        assert not permission.has_permission(request, None)
    
    def test_authenticated_user_can_read(self):
        """Authenticated users can perform safe methods."""
        user = UserFactory.create()
        permission = IsAdminOrReadOnly()
        
        for method in ['GET', 'HEAD', 'OPTIONS']:
            request = Mock(user=user, method=method)
            assert permission.has_permission(request, None)
    
    def test_non_admin_cannot_write(self):
        """Non-admin users cannot perform write operations."""
        user = UserFactory.create()
        permission = IsAdminOrReadOnly()
        
        for method in ['POST', 'PUT', 'PATCH', 'DELETE']:
            request = Mock(user=user, method=method)
            assert not permission.has_permission(request, None)
    
    def test_admin_can_write(self):
        """Admin users can perform write operations."""
        admin = UserFactory.create(is_staff=True)
        permission = IsAdminOrReadOnly()
        
        for method in ['POST', 'PUT', 'PATCH', 'DELETE']:
            request = Mock(user=admin, method=method)
            assert permission.has_permission(request, None)


@pytest.mark.django_db
class TestCanViewDocumentDownloads:
    """Test CanViewDocumentDownloads permission class."""
    
    def test_requires_authentication(self):
        """Unauthenticated users cannot view downloads."""
        permission = CanViewDocumentDownloads()
        request = Mock(user=Mock(is_authenticated=False))
        
        assert not permission.has_permission(request, None)
    
    def test_authenticated_user_has_view_permission(self):
        """Authenticated users can access view."""
        permission = CanViewDocumentDownloads()
        request = Mock(user=Mock(is_authenticated=True))
        
        assert permission.has_permission(request, None)
    
    def test_document_owner_can_view_downloads(self):
        """User can view downloads of their own documents."""
        user = UserFactory.create()
        document = CompletedDocumentFactory.create(related_user=user)
        download = Mock(document=document)
        
        permission = CanViewDocumentDownloads()
        request = Mock(user=user)
        
        assert permission.has_object_permission(request, None, download)
    
    def test_non_owner_cannot_view_downloads(self):
        """User cannot view downloads of other users' documents."""
        owner = UserFactory.create()
        other_user = UserFactory.create()
        document = CompletedDocumentFactory.create(related_user=owner)
        download = Mock(document=document)
        
        permission = CanViewDocumentDownloads()
        request = Mock(user=other_user)
        
        assert not permission.has_object_permission(request, None, download)
    
    def test_admin_can_view_all_downloads(self):
        """Admin can view all download records."""
        owner = UserFactory.create()
        admin = UserFactory.create(is_staff=True)
        document = CompletedDocumentFactory.create(related_user=owner)
        download = Mock(document=document)
        
        permission = CanViewDocumentDownloads()
        request = Mock(user=admin)
        
        assert permission.has_object_permission(request, None, download)