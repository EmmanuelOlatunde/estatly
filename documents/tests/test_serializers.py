# tests/test_serializers.py
"""
Tests for documents app serializers.

Coverage:
- Field validation
- Required fields
- Read-only fields
- Computed fields
- Custom validation logic
"""

import pytest
from uuid import uuid4
from documents.serializers import (
    DocumentSerializer,
    DocumentCreateSerializer,
    DocumentUpdateSerializer,
    DocumentListSerializer,
    DocumentDownloadSerializer,
    DocumentDownloadCreateSerializer,
    DocumentRegenerateSerializer,
)
from documents.models import DocumentType, DocumentStatus
from .factories import (
    UserFactory,
    DocumentFactory,
    CompletedDocumentFactory,
    DocumentDownloadFactory,
)


@pytest.mark.django_db
class TestDocumentSerializer:
    """Test DocumentSerializer (read)."""
    
    def test_serializes_all_fields(self):
        """Serializer includes all expected fields."""
        document = CompletedDocumentFactory.create()
        serializer = DocumentSerializer(document)
        data = serializer.data
        
        expected_fields = {
            'id', 'document_type', 'document_type_display', 'title',
            'file', 'file_url', 'status', 'status_display',
            'related_user', 'related_user_email', 'related_payment_id',
            'related_announcement_id', 'file_size', 'metadata',
            'error_message', 'created_at', 'updated_at', 'generated_at',
            'download_count'
        }
        assert set(data.keys()) == expected_fields
    
    def test_document_type_display(self):
        """Document type display shows human-readable value."""
        document = DocumentFactory.create(
            document_type=DocumentType.PAYMENT_RECEIPT
        )
        serializer = DocumentSerializer(document)
        
        assert serializer.data['document_type_display'] == 'Payment Receipt'
    
    def test_status_display(self):
        """Status display shows human-readable value."""
        document = DocumentFactory.create(status=DocumentStatus.COMPLETED)
        serializer = DocumentSerializer(document)
        
        assert serializer.data['status_display'] == 'Completed'
    
    def test_download_count_computed(self):
        """Download count is computed from related downloads."""
        document = CompletedDocumentFactory.create()
        DocumentDownloadFactory.create_batch(3, document=document)
        
        serializer = DocumentSerializer(document)
        
        assert serializer.data['download_count'] == 3
    
    def test_file_url_with_request_context(self, rf):
        """File URL is absolute when request is in context."""
        document = CompletedDocumentFactory.create()
        request = rf.get('/')
        
        serializer = DocumentSerializer(document, context={'request': request})
        
        assert serializer.data['file_url'] is not None
        assert 'http' in serializer.data['file_url']
    
    def test_file_url_without_file(self):
        """File URL is None when document has no file."""
        document = DocumentFactory.create(file=None)
        serializer = DocumentSerializer(document)
        
        assert serializer.data['file_url'] is None


@pytest.mark.django_db
class TestDocumentCreateSerializer:
    """Test DocumentCreateSerializer (write)."""
    
    def test_valid_payment_receipt_data(self):
        """Valid payment receipt data passes validation."""
        user = UserFactory.create()
        data = {
            'document_type': DocumentType.PAYMENT_RECEIPT,
            'title': 'Payment Receipt #123',
            'related_user': user.id,
            'related_payment_id': str(uuid4()),
            'metadata': {'amount': 1000},
        }
        
        serializer = DocumentCreateSerializer(data=data)
        assert serializer.is_valid(), serializer.errors
    
    def test_valid_announcement_data(self):
        """Valid announcement data passes validation."""
        user = UserFactory.create()
        data = {
            'document_type': DocumentType.ANNOUNCEMENT,
            'title': 'Community Announcement',
            'related_user': user.id,
            'related_announcement_id': str(uuid4()),
            'metadata': {},
        }
        
        serializer = DocumentCreateSerializer(data=data)
        assert serializer.is_valid(), serializer.errors
    
    def test_payment_receipt_requires_payment_id(self):
        """Payment receipts must have related_payment_id."""
        user = UserFactory.create()
        data = {
            'document_type': DocumentType.PAYMENT_RECEIPT,
            'title': 'Payment Receipt',
            'related_user': user.id,
        }
        
        serializer = DocumentCreateSerializer(data=data)
        assert not serializer.is_valid()
        assert 'related_payment_id' in serializer.errors
    
    def test_announcement_requires_announcement_id(self):
        """Announcements must have related_announcement_id."""
        user = UserFactory.create()
        data = {
            'document_type': DocumentType.ANNOUNCEMENT,
            'title': 'Announcement',
            'related_user': user.id,
        }
        
        serializer = DocumentCreateSerializer(data=data)
        assert not serializer.is_valid()
        assert 'related_announcement_id' in serializer.errors
    
    def test_missing_title_fails(self):
        """Missing title fails validation."""
        user = UserFactory.create()
        data = {
            'document_type': DocumentType.PAYMENT_RECEIPT,
            'related_user': user.id,
            'related_payment_id': str(uuid4()),
        }
        
        serializer = DocumentCreateSerializer(data=data)
        assert not serializer.is_valid()
        assert 'title' in serializer.errors


@pytest.mark.django_db
class TestDocumentUpdateSerializer:
    """Test DocumentUpdateSerializer."""
    
    def test_can_update_title(self):
        """Title can be updated."""
        document = DocumentFactory.create()
        data = {'title': 'Updated Title'}
        
        serializer = DocumentUpdateSerializer(document, data=data, partial=True)
        assert serializer.is_valid(), serializer.errors
        
        updated = serializer.save()
        assert updated.title == 'Updated Title'
    
    def test_can_update_metadata(self):
        """Metadata can be updated."""
        document = DocumentFactory.create()
        data = {'metadata': {'new_key': 'new_value'}}
        
        serializer = DocumentUpdateSerializer(document, data=data, partial=True)
        assert serializer.is_valid(), serializer.errors
        
        updated = serializer.save()
        assert updated.metadata == {'new_key': 'new_value'}
    
    def test_limited_fields(self):
        """Only title and metadata can be updated."""
        expected_fields = {'title', 'metadata'}
        serializer = DocumentUpdateSerializer()
        assert set(serializer.fields.keys()) == expected_fields


@pytest.mark.django_db
class TestDocumentListSerializer:
    """Test DocumentListSerializer (lightweight)."""
    
    def test_excludes_heavy_fields(self):
        """List serializer excludes metadata and error_message."""
        document = CompletedDocumentFactory.create(
            metadata={'heavy': 'data'},
            error_message='Some error'
        )
        serializer = DocumentListSerializer(document)
        
        assert 'metadata' not in serializer.data
        assert 'error_message' not in serializer.data
        assert 'download_count' not in serializer.data
    
    def test_includes_essential_fields(self):
        """List serializer includes essential fields."""
        document = CompletedDocumentFactory.create()
        serializer = DocumentListSerializer(document)
        
        expected_fields = {
            'id', 'document_type', 'document_type_display', 'title',
            'file_url', 'status', 'status_display', 'related_user',
            'file_size', 'created_at', 'generated_at'
        }
        assert set(serializer.data.keys()) == expected_fields


@pytest.mark.django_db
class TestDocumentDownloadSerializer:
    """Test DocumentDownloadSerializer."""
    
    def test_serializes_all_fields(self):
        """Serializer includes all expected fields."""
        download = DocumentDownloadFactory.create()
        serializer = DocumentDownloadSerializer(download)
        
        expected_fields = {
            'id', 'document', 'document_title', 'user', 'user_email',
            'ip_address', 'user_agent', 'downloaded_at'
        }
        assert set(serializer.data.keys()) == expected_fields
    
    def test_document_title_computed(self):
        """Document title is computed from related document."""
        download = DocumentDownloadFactory.create()
        serializer = DocumentDownloadSerializer(download)
        
        assert serializer.data['document_title'] == download.document.title


@pytest.mark.django_db
class TestDocumentDownloadCreateSerializer:
    """Test DocumentDownloadCreateSerializer."""
    
    def test_valid_data(self):
        """Valid download data passes validation."""
        document = CompletedDocumentFactory.create()
        data = {
            'document': document.id,
            'ip_address': '192.168.1.1',
            'user_agent': 'Mozilla/5.0',
        }
        
        serializer = DocumentDownloadCreateSerializer(data=data)
        assert serializer.is_valid(), serializer.errors
    
    def test_incomplete_document_fails(self):
        """Cannot create download for incomplete document."""
        document = DocumentFactory.create(status=DocumentStatus.PENDING)
        data = {
            'document': document.id,
            'ip_address': '192.168.1.1',
        }
        
        serializer = DocumentDownloadCreateSerializer(data=data)
        assert not serializer.is_valid()
        assert 'document' in serializer.errors
    
    def test_deleted_document_fails(self):
        """Cannot create download for deleted document."""
        document = CompletedDocumentFactory.create(is_deleted=True)
        data = {
            'document': document.id,
            'ip_address': '192.168.1.1',
        }
        
        serializer = DocumentDownloadCreateSerializer(data=data)
        assert not serializer.is_valid()
        assert 'document' in serializer.errors


@pytest.mark.django_db
class TestDocumentRegenerateSerializer:
    """Test DocumentRegenerateSerializer."""
    
    def test_valid_data(self):
        """Valid regenerate request passes validation."""
        document = CompletedDocumentFactory.create()
        data = {
            'force': True,
            'metadata': {'updated': 'value'},
        }
        
        serializer = DocumentRegenerateSerializer(
            data=data,
            context={'document': document}
        )
        assert serializer.is_valid(), serializer.errors
    
    def test_defaults(self):
        """Default values are set correctly."""
        document = DocumentFactory.create()
        data = {}
        
        serializer = DocumentRegenerateSerializer(
            data=data,
            context={'document': document}
        )
        assert serializer.is_valid(), serializer.errors
        assert serializer.validated_data['force'] is False
    
    def test_generating_document_fails(self):
        """Cannot regenerate document that is being generated."""
        document = DocumentFactory.create(status=DocumentStatus.GENERATING)
        data = {'force': True}
        
        serializer = DocumentRegenerateSerializer(
            data=data,
            context={'document': document}
        )
        assert not serializer.is_valid()
    
    def test_missing_document_context_fails(self):
        """Validation fails if document not in context."""
        data = {'force': True}
        
        serializer = DocumentRegenerateSerializer(data=data)
        assert not serializer.is_valid()