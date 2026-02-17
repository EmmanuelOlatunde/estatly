# maintenance/filters.py

"""
Filter classes for the maintenance app.

Defines filterset for advanced filtering of maintenance tickets.
"""

import django_filters
from django.db.models import Q
from .models import MaintenanceTicket


class MaintenanceTicketFilter(django_filters.FilterSet):
    """
    FilterSet for maintenance tickets with advanced filtering options.
    
    Supports filtering by:
    - Status
    - Category
    - Estate
    - Unit
    - Created by
    - Date ranges
    - Search in title/description
    """
    
    status = django_filters.CharFilter(  
        field_name="status",
        lookup_expr="iexact",  # Case-insensitive
        help_text='Filter by ticket status (case-insensitive)'
    )

    category = django_filters.CharFilter(  
        field_name="category",
        lookup_expr="iexact",  # Case-insensitive
        help_text='Filter by ticket category (case-insensitive)'
    )
    
    estate = django_filters.UUIDFilter(
        field_name="estate__id",
        help_text="Filter by estate UUID"
    )

    unit = django_filters.UUIDFilter(
        field_name="unit__id",
        help_text="Filter by unit UUID"
    )

    created_by = django_filters.CharFilter(
        field_name='created_by_id',
        help_text='Filter by creator UUID'
    )
    
    created_after = django_filters.DateTimeFilter(
        field_name='created_at',
        lookup_expr='gte',
        help_text='Filter tickets created after this datetime'
    )
    
    created_before = django_filters.DateTimeFilter(
        field_name='created_at',
        lookup_expr='lte',
        help_text='Filter tickets created before this datetime'
    )
    
    resolved_after = django_filters.DateTimeFilter(
        field_name='resolved_at',
        lookup_expr='gte',
        help_text='Filter tickets resolved after this datetime'
    )
    
    resolved_before = django_filters.DateTimeFilter(
        field_name='resolved_at',
        lookup_expr='lte',
        help_text='Filter tickets resolved before this datetime'
    )
    
    is_resolved = django_filters.BooleanFilter(
        method='filter_is_resolved',
        help_text='Filter by resolved status (true/false)'
    )
    
    has_unit = django_filters.BooleanFilter(
        method='filter_has_unit',
        help_text='Filter tickets with or without unit association'
    )
    
    search = django_filters.CharFilter(
        method='filter_search',
        help_text='Search in title and description'
    )
    
    class Meta:
        model = MaintenanceTicket
        # Remove duplicates - only list fields that are NOT defined above
        fields = []
    
    def filter_is_resolved(self, queryset, name, value):
        """
        Filter tickets by resolved status.
        
        Args:
            queryset: The base queryset
            name: The filter name
            value: Boolean value (True for resolved, False for open)
            
        Returns:
            Filtered queryset
        """
        if value:
            return queryset.filter(status=MaintenanceTicket.StatusChoices.RESOLVED)
        return queryset.filter(status=MaintenanceTicket.StatusChoices.OPEN)
    
    def filter_has_unit(self, queryset, name, value):
        """
        Filter tickets by unit association.
        
        Args:
            queryset: The base queryset
            name: The filter name
            value: Boolean value (True for with unit, False for without)
            
        Returns:
            Filtered queryset
        """
        if value:
            return queryset.exclude(unit__isnull=True)
        return queryset.filter(unit__isnull=True)
    
    def filter_search(self, queryset, name, value):
        """
        Search tickets by title or description.
        
        Args:
            queryset: The base queryset
            name: The filter name
            value: Search term
            
        Returns:
            Filtered queryset
        """
        if not value:
            return queryset
        
        return queryset.filter(
            Q(title__icontains=value) | Q(description__icontains=value)
        )