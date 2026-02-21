"""
Serializers for documents app.
"""

from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import Document, DocumentDownload, DocumentType, DocumentStatus

User = get_user_model()


class DocumentSerializer(serializers.ModelSerializer):
    """
    Serializer for reading Document instances.
    
    Includes computed fields and detailed information.
    """
    document_type_display = serializers.CharField(
        source='get_document_type_display', read_only=True
    )
    status_display = serializers.CharField(
        source='get_status_display', read_only=True
    )
    file_url = serializers.SerializerMethodField()
    download_count = serializers.SerializerMethodField()
    related_user_email = serializers.EmailField(
        source='related_user.email', read_only=True, allow_null=True
    )

    class Meta:
        model = Document
        fields = [
            'id',
            'document_type',
            'document_type_display',
            'title',
            # 'file' removed — exposes raw storage path
            'file_url',
            'status',
            'status_display',
            'related_user',
            'related_user_email',
            'related_payment_id',
            'related_announcement_id',
            'file_size',
            'metadata',
            'error_message',
            'created_at',
            'updated_at',
            'generated_at',
            'download_count',
        ]
        read_only_fields = ['id', 'file_size', 'created_at', 'updated_at', 'generated_at']

    def get_file_url(self, obj):
        if obj.file:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.file.url)
            return obj.file.url
        return None

    def get_download_count(self, obj):
        return obj.downloads.count()


class DocumentCreateSerializer(serializers.ModelSerializer):
    """
    Serializer for creating Document instances.
    
    Used when initiating document generation.
    """
    related_user = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(),
        required=False,     
        allow_null=True     
    )
    class Meta:
        model = Document
        fields = [
            'document_type',
            'title',
            'related_user',
            'related_payment_id',
            'related_announcement_id',
            'metadata',
        ]
    
    def validate(self, attrs):
        """Validate document creation data."""
        document_type = attrs.get('document_type')
        request = self.context.get('request')
        user = request.user if request else None

        # --- New: Enforce related_user for non-admins ---
        # If user is not staff/admin, related_user MUST be provided
        if user and not (user.is_staff or user.is_superuser):
            if not attrs.get('related_user'):
                raise serializers.ValidationError({
                    'related_user': 'This field is required for regular users.'
                })

        # --- Existing Validation ---
        if document_type == DocumentType.PAYMENT_RECEIPT:
            if not attrs.get('related_payment_id'):
                raise serializers.ValidationError({
                    'related_payment_id': 'Payment receipts must have a related payment ID'
                })
        
        if document_type == DocumentType.ANNOUNCEMENT:
            if not attrs.get('related_announcement_id'):
                raise serializers.ValidationError({
                    'related_announcement_id': 'Announcements must have a related announcement ID'
                })
        
        return attrs

class DocumentUpdateSerializer(serializers.ModelSerializer):
    """
    Serializer for updating Document instances.
    
    Limited fields that can be updated after creation.
    """
    
    class Meta:
        model = Document
        fields = [
            'title',
            'metadata',
        ]


class DocumentListSerializer(serializers.ModelSerializer):
    """
    Lightweight serializer for listing documents.
    
    Excludes heavy fields like metadata and error messages.
    """
    
    document_type_display = serializers.CharField(
        source='get_document_type_display',
        read_only=True
    )
    status_display = serializers.CharField(
        source='get_status_display',
        read_only=True
    )
    file_url = serializers.SerializerMethodField()
    
    class Meta:
        model = Document
        fields = [
            'id',
            'document_type',
            'document_type_display',
            'title',
            'file_url',
            'status',
            'status_display',
            'related_user',
            'related_payment_id',        # 👈 ADD
            'related_announcement_id',   # 👈 ADD
            'file_size',
            'created_at',
            'generated_at',
        ]
    
    def get_file_url(self, obj):
        """Get absolute URL for the file."""
        if obj.file:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.file.url)
            return obj.file.url
        return None


class DocumentDownloadSerializer(serializers.ModelSerializer):
    """
    Serializer for DocumentDownload instances.
    
    Tracks when users download documents.
    """
    
    document_title = serializers.CharField(
        source='document.title',
        read_only=True
    )
    user_email = serializers.EmailField(
        source='user.email',
        read_only=True,
        allow_null=True
    )
    
    class Meta:
        model = DocumentDownload
        fields = [
            'id',
            'document',
            'document_title',
            'user',
            'user_email',
            'ip_address',
            'user_agent',
            'downloaded_at',
        ]
        read_only_fields = [
            'id',
            'downloaded_at',
        ]


class DocumentDownloadCreateSerializer(serializers.ModelSerializer):
    """
    Serializer for creating DocumentDownload records.
    """
    
    class Meta:
        model = DocumentDownload
        fields = [
            'document',
            'ip_address',
            'user_agent',
        ]
    
    def validate_document(self, value):
        """Ensure document exists and is available for download."""
        if value.status != DocumentStatus.COMPLETED:
            raise serializers.ValidationError(
                'Document is not ready for download'
            )
        
        if not value.file:
            raise serializers.ValidationError(
                'Document file is not available'
            )
        
        if value.is_deleted:
            raise serializers.ValidationError(
                'Document has been deleted'
            )
        
        return value


class DocumentRegenerateSerializer(serializers.Serializer):
    """
    Serializer for triggering document regeneration.
    """
    
    force = serializers.BooleanField(
        default=False,
        help_text='Force regeneration even if document already exists'
    )
    metadata = serializers.JSONField(
        required=False,
        help_text='Updated metadata for regeneration'
    )
    
    def validate(self, attrs):
        """Validate regeneration request."""
        document = self.context.get('document')
        
        if not document:
            raise serializers.ValidationError('Document not found in context')
        
        if document.status == DocumentStatus.GENERATING:
            raise serializers.ValidationError(
                'Document is already being generated'
            )
        
        return attrs