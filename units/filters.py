# units/filters.py

"""
Filter classes for the units app.

Provides filtering capabilities for unit queries.
"""

import django_filters
from django.db.models import Q
from .models import Unit


class UnitFilter(django_filters.FilterSet):
    """
    FilterSet for Unit model.
    
    Provides filtering options for unit queries including:
    - Estate
    - Unit type
    - Occupancy status
    - Active status
    - Search by identifier, occupant name, or description
    - Date range filters
    """
    
    # Estate filter
    estate = django_filters.UUIDFilter(
        field_name='estate__id',
        help_text='Filter by estate ID'
    )
    
    # Exact match filters
    unit_type = django_filters.CharFilter(
        method='filter_unit_type',
        help_text='Filter by unit type'
    )

    is_occupied = django_filters.BooleanFilter(
        field_name='is_occupied',
        help_text='Filter by occupancy status'
    )
    
    is_active = django_filters.BooleanFilter(
        field_name='is_active',
        help_text='Filter by active status'
    )
    
    # Text search filters
    identifier = django_filters.CharFilter(
        field_name='identifier',
        lookup_expr='icontains',
        help_text='Search by unit identifier (case-insensitive)'
    )
    
    occupant_name = django_filters.CharFilter(
        field_name='occupant_name',
        lookup_expr='icontains',
        help_text='Search by occupant name (case-insensitive)'
    )
    
    # General search across multiple fields
    search = django_filters.CharFilter(
        method='filter_search',
        help_text='Search across identifier, occupant name, and description'
    )
    
    # Date range filters
    created_after = django_filters.DateTimeFilter(
        field_name='created_at',
        lookup_expr='gte',
        help_text='Filter units created after this date'
    )
    
    created_before = django_filters.DateTimeFilter(
        field_name='created_at',
        lookup_expr='lte',
        help_text='Filter units created before this date'
    )
    
    updated_after = django_filters.DateTimeFilter(
        field_name='updated_at',
        lookup_expr='gte',
        help_text='Filter units updated after this date'
    )
    
    updated_before = django_filters.DateTimeFilter(
        field_name='updated_at',
        lookup_expr='lte',
        help_text='Filter units updated before this date'
    )
    
    class Meta:
        model = Unit
        # REMOVE ALL FIELDS - they're all defined above explicitly
        fields = []
        
    def filter_unit_type(self, queryset, name, value):
        """
        Ignore invalid unit_type values instead of raising 400.
        
        Args:
            queryset: The initial queryset
            name: The filter field name
            value: The unit type value
            
        Returns:
            Filtered queryset or unchanged queryset if value is invalid
        """
        valid_values = {choice[0] for choice in Unit.UnitType.choices}

        if value in valid_values:
            return queryset.filter(unit_type=value)

        # Invalid value is silently ignored
        return queryset

    def filter_search(self, queryset, name, value):
        """
        Custom filter method for general search.
        
        Searches across identifier, occupant_name, and description fields.
        
        Args:
            queryset: The initial queryset
            name: The filter field name
            value: The search term
            
        Returns:
            Filtered queryset
        """
        if not value:
            return queryset
        
        return queryset.filter(
            Q(identifier__icontains=value) |
            Q(occupant_name__icontains=value) |
            Q(description__icontains=value)
        )