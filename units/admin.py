"""
Django admin configuration for the units app.

Provides admin interface for managing units.
"""
from django.contrib import admin
from .models import Unit


@admin.register(Unit)
class UnitAdmin(admin.ModelAdmin):
    """
    Admin interface for Unit model.
    
    Provides comprehensive management capabilities for units
    with organized fieldsets and filtering options.
    """
    
    list_display = [
        'identifier',
        'unit_type',
        'owner',
        'is_occupied',
        'occupant_name',
        'is_active',
        'estate',

        'created_at',
    ]
    
    list_filter = [
        'estate',
        'unit_type',
        'is_occupied',
        'is_active',
        'created_at',
        'updated_at',
    ]
    
    search_fields = [
        'estate__name',
        'identifier',
        'occupant_name',
        'occupant_phone',
        'description',
        'owner__email',
        'owner__username',
    ]
    
    readonly_fields = [
        'id',
        'created_at',
        'updated_at',
        'has_occupant_info',
    ]
    
    fieldsets = (
        ('Basic Information', {
            'fields': (
                'id',
                'identifier',
                'estate',
                'unit_type',
                'owner',
            )
        }),
        ('Occupancy Information', {
            'fields': (
                'is_occupied',
                'occupant_name',
                'occupant_phone',
            )
        }),
        ('Additional Details', {
            'fields': (
                'description',
                'is_active',
            )
        }),
        ('Metadata', {
            'fields': (
                'has_occupant_info',
                'created_at',
                'updated_at',
            ),
            'classes': ('collapse',)
        }),
    )
    
    ordering = ['identifier', '-created_at']
    
    date_hierarchy = 'created_at'
    
    list_per_page = 25
    
    def get_queryset(self, request):
        """
        Optimize queryset with select_related for owner.
        
        Args:
            request: The HTTP request
            
        Returns:
            Optimized queryset
        """
        queryset = super().get_queryset(request)
        return queryset.select_related('owner','estate')
    
    def has_occupant_info(self, obj):
        """
        Display whether unit has occupant information.
        
        Args:
            obj: The Unit instance
            
        Returns:
            bool: Whether unit has occupant info
        """
        return obj.has_occupant_info
    
    has_occupant_info.boolean = True
    has_occupant_info.short_description = 'Has Occupant Info'