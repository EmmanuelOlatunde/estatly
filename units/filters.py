"""
Filter classes for the units app.

Provides filtering capabilities for unit queries.
"""

import django_filters
from .models import Unit


class UnitFilter(django_filters.FilterSet):
    """
    FilterSet for Unit model.
    
    Provides filtering options for unit queries including:
    - Unit type
    - Occupancy status
    - Active status
    - Search by identifier or occupant name
    """
    
    # Exact match filters
    # unit_type = django_filters.ChoiceFilter(
    #     field_name='unit_type',
    #     choices=Unit.UnitType.choices,
    #     help_text='Filter by unit type'
    # )
    unit_type = django_filters.CharFilter(method='filter_unit_type')

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
    
    class Meta:
        model = Unit
        fields = [
            'unit_type',
            'is_occupied',
            'is_active',
            'identifier',
            'occupant_name',
        ]
        
    def filter_unit_type(self, queryset, name, value):
        """
        Ignore invalid unit_type values instead of raising 400.
        """
        valid_values = {choice[0] for choice in Unit.UnitType.choices}

        if value in valid_values:
            return queryset.filter(unit_type=value)

        return queryset  # <-- invalid value is ignored


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
        from django.db.models import Q
        
        if not value:
            return queryset
        
        return queryset.filter(
            Q(identifier__icontains=value) |
            Q(occupant_name__icontains=value) |
            Q(description__icontains=value)
        )