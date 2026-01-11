# estate/admin.py
"""
Django admin configuration for estate app.
"""

from django.contrib import admin
from .models import Estate


@admin.register(Estate)
class EstateAdmin(admin.ModelAdmin):
    """Admin interface for Estate model."""
    
    list_display = [
        'name',
        'estate_type',
        'approximate_units',
        'total_units',        # 👈 total units
        'active_units',       # 👈 active units
        'fee_frequency',
        'is_active',
        'created_at',
    ]
    
    list_filter = [
        'estate_type',
        'fee_frequency',
        'is_active',
        'created_at',
    ]
    
    search_fields = [
        'name',
        'description',
        'address',
    ]
    
    readonly_fields = [
        'id',
        'created_at',
        'updated_at',
    ]
    
    fieldsets = (
        ('Basic Information', {
            'fields': (
                'name',
                'estate_type',
                'description',
            )
        }),
        ('Details', {
            'fields': (
                'approximate_units',
                'fee_frequency',
                'address',
            )
        }),
        ('Status', {
            'fields': (
                'is_active',
            )
        }),
        ('System Information', {
            'fields': (
                'id',
                'created_at',
                'updated_at',
            ),
            'classes': ('collapse',)
        }),
    )
    
    ordering = ['-created_at']
    
    actions = ['activate_estates', 'deactivate_estates']
    
    def activate_estates(self, request, queryset):
        """Bulk activate estates."""
        updated = queryset.update(is_active=True)
        self.message_user(
            request,
            f'{updated} estate(s) activated successfully.'
        )
    activate_estates.short_description = 'Activate selected estates'
    
    def deactivate_estates(self, request, queryset):
        """Bulk deactivate estates."""
        updated = queryset.update(is_active=False)
        self.message_user(
            request,
            f'{updated} estate(s) deactivated successfully.'
        )
    deactivate_estates.short_description = 'Deactivate selected estates'
    

    # Add methods to expose properties in admin
    def total_units(self, obj):
        return obj.total_units
    total_units.short_description = 'Total Units'

    def active_units(self, obj):
        return obj.active_units
    active_units.short_description = 'Active Units'