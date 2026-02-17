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
        'estate_name',
        'preview_message',
        'created_by',
        'status_badge',
        'created_at',
        'updated_at',
    ]
    
    list_filter = [
        'estate',
        'is_active',
        'created_at',
        'updated_at',
        'created_by',
    ]
    
    search_fields = [
        'title',
        'message',
        'estate__name',
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
            'fields': ('estate', 'title', 'message', 'is_active')
        }),
        ('Metadata', {
            'fields': ('id', 'created_by', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    date_hierarchy = 'created_at'
    
    ordering = ['-created_at']
    
    list_per_page = 25
    
    autocomplete_fields = ['estate']  # Enable autocomplete for estate selection
    
    def estate_name(self, obj):
        """
        Display the estate name in list view.
        
        Args:
            obj: Announcement instance
        
        Returns:
            Estate name or 'No Estate' if not set
        """
        if obj.estate:
            return obj.estate.name
        return format_html(
            '<span style="color: #dc3545; font-weight: bold;">⚠️ No Estate</span>'
        )
    
    estate_name.short_description = 'Estate'
    estate_name.admin_order_field = 'estate__name'
    
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
        Staff can only delete their own announcements from their estate.
        
        Args:
            request: HTTP request
            obj: Announcement instance (optional)
        
        Returns:
            True if user can delete, False otherwise
        """
        if request.user.is_superuser:
            return True
        
        if obj is not None:
            # Must be creator AND announcement must be from their estate
            is_creator = obj.created_by == request.user
            same_estate = (
                hasattr(request.user, 'estate') and 
                request.user.estate and 
                obj.estate == request.user.estate
            )
            return is_creator and same_estate
        
        return True
    
    def has_change_permission(self, request, obj=None):
        """
        Determine if the user has permission to change an announcement.
        
        Superusers can change any announcement.
        Staff can only change their own announcements from their estate.
        
        Args:
            request: HTTP request
            obj: Announcement instance (optional)
        
        Returns:
            True if user can change, False otherwise
        """
        if request.user.is_superuser:
            return True
        
        if obj is not None:
            # Must be creator AND announcement must be from their estate
            is_creator = obj.created_by == request.user
            same_estate = (
                hasattr(request.user, 'estate') and 
                request.user.estate and 
                obj.estate == request.user.estate
            )
            return is_creator and same_estate
        
        return True
    
    def save_model(self, request, obj, form, change):
        """
        Save the announcement model.
        
        If creating a new announcement, set the created_by field
        to the current user and default estate to user's estate.
        
        Args:
            request: HTTP request
            obj: Announcement instance
            form: ModelForm instance
            change: True if updating existing object
        """
        if not change:
            obj.created_by = request.user
            
            # Auto-set estate for non-superusers if not already set
            if not request.user.is_superuser and not obj.estate:
                if hasattr(request.user, 'estate') and request.user.estate:
                    obj.estate = request.user.estate
        
        super().save_model(request, obj, form, change)
    
    def get_queryset(self, request):
        """
        Get the queryset for the admin list view.
        
        Superusers see all announcements.
        Staff users see only announcements from their estate.
        
        Args:
            request: HTTP request
        
        Returns:
            Filtered QuerySet
        """
        qs = super().get_queryset(request)
        
        if request.user.is_superuser:
            return qs
        
        # Filter by user's estate for staff members
        if hasattr(request.user, 'estate') and request.user.estate:
            return qs.filter(estate=request.user.estate)
        
        # If staff user has no estate, show only their own announcements
        return qs.filter(created_by=request.user)
    
    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        """
        Customize the estate foreign key field in the form.
        
        Non-superusers can only select their own estate.
        Superusers can select any estate.
        
        Args:
            db_field: Database field
            request: HTTP request
            **kwargs: Additional arguments
        
        Returns:
            Form field
        """
        if db_field.name == "estate":
            if not request.user.is_superuser:
                # Non-superusers can only select their own estate
                if hasattr(request.user, 'estate') and request.user.estate:
                    from estates.models import Estate
                    kwargs["queryset"] = Estate.objects.filter(id=request.user.estate.id)
                    kwargs["initial"] = request.user.estate
        
        return super().formfield_for_foreignkey(db_field, request, **kwargs)
    
    def get_readonly_fields(self, request, obj=None):
        """
        Get readonly fields based on user permissions.
        
        For non-superusers, make estate field readonly if object already exists
        (they can't change estate after creation).
        
        Args:
            request: HTTP request
            obj: Announcement instance (optional)
        
        Returns:
            List of readonly field names
        """
        readonly = list(self.readonly_fields)
        
        # Non-superusers cannot change estate after creation
        if not request.user.is_superuser and obj is not None:
            if 'estate' not in readonly:
                readonly.append('estate')
        
        return readonly
    
    class Media:
        """
        Add custom CSS/JS for the admin interface.
        """
        css = {
            'all': ('admin/css/announcements.css',)  # Optional: custom styling
        }