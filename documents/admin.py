"""
Django admin configuration for documents app.
"""

from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from .models import Document, DocumentDownload


@admin.register(Document)
class DocumentAdmin(admin.ModelAdmin):
    """Admin interface for Document model."""
    
    list_display = [
        'id',
        'title',
        'document_type',
        'status',
        'related_user_link',
        'file_link',
        'file_size_display',
        'created_at',
        'generated_at',
        'is_deleted',
    ]
    list_filter = [
        'document_type',
        'status',
        'is_deleted',
        'created_at',
        'generated_at',
    ]
    search_fields = [
        'id',
        'title',
        'related_user__email',
        'related_payment_id',
        'related_announcement_id',
        'error_message',
    ]
    readonly_fields = [
        'id',
        'created_at',
        'updated_at',
        'generated_at',
        'deleted_at',
        'file_size',
        'download_count',
        'file_preview',
    ]
    
    fieldsets = (
        ('Basic Information', {
            'fields': (
                'id',
                'document_type',
                'title',
                'status',
            )
        }),
        ('File Information', {
            'fields': (
                'file',
                'file_preview',
                'file_size',
            )
        }),
        ('Related Entities', {
            'fields': (
                'related_user',
                'related_payment_id',
                'related_announcement_id',
            )
        }),
        ('Metadata', {
            'fields': (
                'metadata',
                'error_message',
            ),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': (
                'created_at',
                'updated_at',
                'generated_at',
            ),
            'classes': ('collapse',)
        }),
        ('Deletion', {
            'fields': (
                'is_deleted',
                'deleted_at',
            ),
            'classes': ('collapse',)
        }),
        ('Analytics', {
            'fields': (
                'download_count',
            ),
            'classes': ('collapse',)
        }),
    )
    
    date_hierarchy = 'created_at'
    ordering = ['-created_at']
    
    def related_user_link(self, obj):
        """Display related user as admin link."""
        if obj.related_user:
            url = reverse('admin:auth_user_change', args=[obj.related_user.pk])
            return format_html('<a href="{}">{}</a>', url, obj.related_user.email)
        return '-'
    related_user_link.short_description = 'Related User'
    
    def file_link(self, obj):
        """Display file as download link."""
        if obj.file:
            return format_html(
                '<a href="{}" target="_blank">Download</a>',
                obj.file.url
            )
        return '-'
    file_link.short_description = 'File'
    
    def file_size_display(self, obj):
        """Display file size in human-readable format."""
        if obj.file_size:
            size_kb = obj.file_size / 1024
            if size_kb < 1024:
                return f"{size_kb:.2f} KB"
            size_mb = size_kb / 1024
            return f"{size_mb:.2f} MB"
        return '-'
    file_size_display.short_description = 'File Size'
    
    def download_count(self, obj):
        """Display number of downloads."""
        return obj.downloads.count()
    download_count.short_description = 'Downloads'
    
    def file_preview(self, obj):
        """Display file preview or information."""
        if obj.file:
            return format_html(
                '<iframe src="{}" width="600" height="400"></iframe>',
                obj.file.url
            )
        return '-'
    file_preview.short_description = 'File Preview'
    
    def get_queryset(self, request):
        """Optimize queryset with related data."""
        qs = super().get_queryset(request)
        return qs.select_related('related_user').prefetch_related('downloads')


@admin.register(DocumentDownload)
class DocumentDownloadAdmin(admin.ModelAdmin):
    """Admin interface for DocumentDownload model."""
    
    list_display = [
        'id',
        'document_link',
        'user_link',
        'ip_address',
        'downloaded_at',
    ]
    list_filter = [
        'downloaded_at',
        'document__document_type',
    ]
    search_fields = [
        'id',
        'document__title',
        'user__email',
        'ip_address',
    ]
    readonly_fields = [
        'id',
        'document',
        'user',
        'ip_address',
        'user_agent',
        'downloaded_at',
    ]
    
    fieldsets = (
        ('Download Information', {
            'fields': (
                'id',
                'document',
                'user',
                'downloaded_at',
            )
        }),
        ('Technical Details', {
            'fields': (
                'ip_address',
                'user_agent',
            ),
            'classes': ('collapse',)
        }),
    )
    
    date_hierarchy = 'downloaded_at'
    ordering = ['-downloaded_at']
    
    def document_link(self, obj):
        """Display document as admin link."""
        if obj.document:
            url = reverse('admin:documents_document_change', args=[obj.document.pk])
            return format_html('<a href="{}">{}</a>', url, obj.document.title)
        return '-'
    document_link.short_description = 'Document'
    
    def user_link(self, obj):
        """Display user as admin link."""
        if obj.user:
            url = reverse('admin:auth_user_change', args=[obj.user.pk])
            return format_html('<a href="{}">{}</a>', url, obj.user.email)
        return 'Anonymous'
    user_link.short_description = 'User'
    
    def has_add_permission(self, request):
        """Disable manual creation of download records."""
        return False
    
    def has_change_permission(self, request, obj=None):
        """Make download records read-only."""
        return False
    
    def get_queryset(self, request):
        """Optimize queryset with related data."""
        qs = super().get_queryset(request)
        return qs.select_related('document', 'user')