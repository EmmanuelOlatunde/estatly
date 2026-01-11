# maintenance/admin.py

"""
Django admin configuration for the maintenance app.

Registers models and customizes admin interface for maintenance tickets.
"""

from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
# from django.utils.safestring import mark_safe
from .models import MaintenanceTicket


@admin.register(MaintenanceTicket)
class MaintenanceTicketAdmin(admin.ModelAdmin):
    """
    Admin interface for MaintenanceTicket model.
    
    Provides comprehensive management interface with filtering,
    searching, and organized display of ticket information.
    """
    
    list_display = [
        'title',
        'colored_status',
        'category',
        'estate_link',
        'unit_link',
        'created_by_link',
        'created_at',
        'resolved_at',
    ]
    
    list_filter = [
        'status',
        'category',
        'created_at',
        'resolved_at',
        'estate',
    ]
    
    search_fields = [
        'title',
        'description',
        'id',
        'created_by__email',
        'estate__name',
    ]
    
    readonly_fields = [
        'id',
        'created_at',
        'updated_at',
        'resolved_at',
    ]
    
    fieldsets = (
        ('Basic Information', {
            'fields': (
                'id',
                'title',
                'description',
                'category',
                'status',
            )
        }),
        ('Relationships', {
            'fields': (
                'estate',
                'unit',
                'created_by',
            )
        }),
        ('Timestamps', {
            'fields': (
                'created_at',
                'updated_at',
                'resolved_at',
            ),
            'classes': ('collapse',)
        }),
    )
    
    date_hierarchy = 'created_at'
    
    list_per_page = 25
    
    ordering = ['-created_at']
    
    def colored_status(self, obj):
        """
        Display status with color coding.
        
        Args:
            obj: MaintenanceTicket instance
            
        Returns:
            HTML formatted status with color
        """
        colors = {
            'OPEN': '#dc3545',  # Red
            'RESOLVED': '#28a745',  # Green
        }
        color = colors.get(obj.status, '#6c757d')
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color,
            obj.get_status_display()
        )
    colored_status.short_description = 'Status'
    colored_status.admin_order_field = 'status'
    
    def estate_link(self, obj):
        """
        Create a link to the related estate in admin.
        
        Args:
            obj: MaintenanceTicket instance
            
        Returns:
            HTML link to estate admin page
        """
        if obj.estate:
            url = reverse('admin:estates_estate_change', args=[obj.estate.id])
            return format_html('<a href="{}">{}</a>', url, obj.estate.name)
        return '-'
    estate_link.short_description = 'Estate'
    estate_link.admin_order_field = 'estate__name'
    
    def unit_link(self, obj):
        """
        Create a link to the related unit in admin.
        
        Args:
            obj: MaintenanceTicket instance
            
        Returns:
            HTML link to unit admin page or dash if no unit
        """
        if obj.unit:
            url = reverse('admin:units_unit_change', args=[obj.unit.id])
            return format_html(
                '<a href="{}">{}</a>',
                url,
                getattr(obj.unit, 'unit_number', str(obj.unit))
            )
        return '-'
    unit_link.short_description = 'Unit'
    
    def created_by_link(self, obj):
        """
        Create a link to the user who created the ticket.
        
        Args:
            obj: MaintenanceTicket instance
            
        Returns:
            HTML link to user admin page
        """
        if obj.created_by:
            # Adjust this based on your user model's app label
            try:
                url = reverse('admin:auth_user_change', args=[obj.created_by.id])
                display_name = (
                    obj.created_by.get_full_name()
                    if hasattr(obj.created_by, 'get_full_name')
                    else str(obj.created_by)
                )
                return format_html('<a href="{}">{}</a>', url, display_name)
            except Exception:
                return str(obj.created_by)
        return '-'
    created_by_link.short_description = 'Created By'
    created_by_link.admin_order_field = 'created_by__email'
    
    def get_queryset(self, request):
        """
        Optimize queryset with select_related to reduce database queries.
        
        Args:
            request: The HTTP request
            
        Returns:
            Optimized queryset
        """
        queryset = super().get_queryset(request)
        return queryset.select_related('created_by', 'unit', 'estate')
    
    def has_delete_permission(self, request, obj=None):
        """
        Control delete permission.
        
        Args:
            request: The HTTP request
            obj: The object being deleted
            
        Returns:
            Boolean indicating if user has delete permission
        """
        # Only superusers can delete tickets
        return request.user.is_superuser
    
    actions = ['mark_as_resolved', 'mark_as_open']
    
    def mark_as_resolved(self, request, queryset):
        """
        Admin action to mark selected tickets as resolved.
        
        Args:
            request: The HTTP request
            queryset: Selected tickets
        """
        from django.utils import timezone
        updated = queryset.update(
            status=MaintenanceTicket.StatusChoices.RESOLVED,
            resolved_at=timezone.now()
        )
        self.message_user(
            request,
            f'{updated} ticket(s) marked as resolved.'
        )
    mark_as_resolved.short_description = 'Mark selected tickets as resolved'
    
    def mark_as_open(self, request, queryset):
        """
        Admin action to mark selected tickets as open.
        
        Args:
            request: The HTTP request
            queryset: Selected tickets
        """
        updated = queryset.update(
            status=MaintenanceTicket.StatusChoices.OPEN,
            resolved_at=None
        )
        self.message_user(
            request,
            f'{updated} ticket(s) marked as open.'
        )
    mark_as_open.short_description = 'Mark selected tickets as open'