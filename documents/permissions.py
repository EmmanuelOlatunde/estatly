"""
Custom permission classes for documents app.
"""

import logging
from rest_framework import permissions

logger = logging.getLogger(__name__)


class IsDocumentOwnerOrAdmin(permissions.BasePermission):
    """
    Permission check for document access.
    
    Allows:
    - Admin/staff users to access any document
    - Users to access their own documents (related_user matches)
    """
    
    def has_permission(self, request, view):
        """Check if user has permission to access the view."""
        return request.user and request.user.is_authenticated
    
    def has_object_permission(self, request, view, obj):
        """Check if user has permission to access specific document."""
        if request.user.is_staff or request.user.is_superuser:
            logger.debug(f"Admin user {request.user.id} accessing document {obj.id}")
            return True
        
        if hasattr(obj, 'related_user') and obj.related_user:
            is_owner = obj.related_user == request.user
            if not is_owner:
                logger.warning(
                    f"User {request.user.id} denied access to document {obj.id} "
                    f"(owner: {obj.related_user.id})"
                )
            return is_owner
        
        logger.warning(f"Document {obj.id} has no related_user, denying access")
        return False


class CanDownloadDocument(permissions.BasePermission):
    """
    Permission check for document downloads.
    
    Allows downloading only if:
    - Document is completed and has a file
    - User owns the document or is admin
    - Document is not deleted
    """
    
    def has_permission(self, request, view):
        """Check if user has permission to download."""
        return request.user and request.user.is_authenticated
    
    def has_object_permission(self, request, view, obj):
        """Check if user can download specific document."""
        from .models import DocumentStatus
        
        if obj.is_deleted:
            logger.warning(f"Attempt to download deleted document {obj.id}")
            return False
        
        if obj.status != DocumentStatus.COMPLETED:
            logger.warning(
                f"Attempt to download incomplete document {obj.id} "
                f"(status: {obj.status})"
            )
            return False
        
        if not obj.file:
            logger.warning(f"Attempt to download document {obj.id} with no file")
            return False
        
        if request.user.is_staff or request.user.is_superuser:
            return True
        
        if hasattr(obj, 'related_user') and obj.related_user:
            is_owner = obj.related_user == request.user
            if not is_owner:
                logger.warning(
                    f"User {request.user.id} denied download of document {obj.id}"
                )
            return is_owner
        
        return False


class IsAdminOrReadOnly(permissions.BasePermission):
    """
    Permission for admin-only write operations.
    
    Allows:
    - Anyone to read (GET, HEAD, OPTIONS)
    - Only admin users to write (POST, PUT, PATCH, DELETE)
    """
    
    def has_permission(self, request, view):
        """Check view-level permission."""
        if not request.user or not request.user.is_authenticated:
            return False
        
        if request.method in permissions.SAFE_METHODS:
            return True
        
        is_admin = request.user.is_staff or request.user.is_superuser
        if not is_admin:
            logger.warning(
                f"Non-admin user {request.user.id} attempted write operation"
            )
        return is_admin


class CanViewDocumentDownloads(permissions.BasePermission):
    """
    Permission to view download records.
    
    Allows:
    - Admin users to view all downloads
    - Users to view downloads of their own documents
    """
    
    def has_permission(self, request, view):
        """Check view-level permission."""
        return request.user and request.user.is_authenticated
    
    def has_object_permission(self, request, view, obj):
        """Check object-level permission for download record."""
        if request.user.is_staff or request.user.is_superuser:
            return True
        
        if hasattr(obj, 'document'):
            document = obj.document
            if hasattr(document, 'related_user') and document.related_user:
                is_owner = document.related_user == request.user
                if not is_owner:
                    logger.warning(
                        f"User {request.user.id} denied access to download "
                        f"record {obj.id}"
                    )
                return is_owner
        
        return False