# announcements/admin.py

"""
Django admin configuration for announcements app.

Provides admin interface for managing announcements.
"""

from django.contrib import admin
from django.utils.html import format_html
from .models import Announcement


@admin.register(Announcement)
class AnnouncementAdmin(admin.ModelAdmin):
    """
    Admin interface for Announcement model.
    
    Provides a comprehensive interface for managing announcements
    in the Django admin panel.
    """
    
    list_display = [
        'title',
        'preview_message',
        'created_by',
        'status_badge',
        'created_at',
        'updated_at',
    ]
    
    list_filter = [
        'is_active',
        'created_at',
        'updated_at',
        'created_by',
    ]
    
    search_fields = [
        'title',
        'message',
        'created_by__email',
        'created_by__first_name',
        'created_by__last_name',
    ]
    
    readonly_fields = [
        'id',
        'created_at',
        'updated_at',
    ]
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('title', 'message', 'is_active')
        }),
        ('Metadata', {
            'fields': ('id', 'created_by', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    date_hierarchy = 'created_at'
    
    ordering = ['-created_at']
    
    list_per_page = 25
    
    def preview_message(self, obj):
        """
        Display a preview of the message in list view.
        
        Args:
            obj: Announcement instance
        
        Returns:
            Truncated message preview
        """
        if len(obj.message) <= 50:
            return obj.message
        return f"{obj.message[:47]}..."
    
    preview_message.short_description = 'Message Preview'
    
    def status_badge(self, obj):
        """
        Display a colored badge for the announcement status.
        
        Args:
            obj: Announcement instance
        
        Returns:
            HTML formatted status badge
        """
        if obj.is_active:
            return format_html(
                '<span style="background-color: #28a745; color: white; '
                'padding: 3px 10px; border-radius: 3px;">Active</span>'
            )
        return format_html(
            '<span style="background-color: #6c757d; color: white; '
            'padding: 3px 10px; border-radius: 3px;">Inactive</span>'
        )
    
    status_badge.short_description = 'Status'
    
    def has_delete_permission(self, request, obj=None):
        """
        Determine if the user has permission to delete an announcement.
        
        Superusers can delete any announcement.
        Staff can only delete their own announcements.
        
        Args:
            request: HTTP request
            obj: Announcement instance (optional)
        
        Returns:
            True if user can delete, False otherwise
        """
        if request.user.is_superuser:
            return True
        
        if obj is not None:
            return obj.created_by == request.user
        
        return True
    
    def has_change_permission(self, request, obj=None):
        """
        Determine if the user has permission to change an announcement.
        
        Superusers can change any announcement.
        Staff can only change their own announcements.
        
        Args:
            request: HTTP request
            obj: Announcement instance (optional)
        
        Returns:
            True if user can change, False otherwise
        """
        if request.user.is_superuser:
            return True
        
        if obj is not None:
            return obj.created_by == request.user
        
        return True
    
    def save_model(self, request, obj, form, change):
        """
        Save the announcement model.
        
        If creating a new announcement, set the created_by field
        to the current user.
        
        Args:
            request: HTTP request
            obj: Announcement instance
            form: ModelForm instance
            change: True if updating existing object
        """
        if not change:
            obj.created_by = request.user
        
        super().save_model(request, obj, form, change)
    
    def get_queryset(self, request):
        """
        Get the queryset for the admin list view.
        
        Superusers see all announcements.
        Staff users see only their own announcements.
        
        Args:
            request: HTTP request
        
        Returns:
            Filtered QuerySet
        """
        qs = super().get_queryset(request)
        
        if request.user.is_superuser:
            return qs
        
        return qs.filter(created_by=request.user)