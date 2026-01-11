# estate/filters.py
"""
Filter classes for estate app.
"""

import django_filters
from .models import Estate


class EstateFilter(django_filters.FilterSet):
    """
    FilterSet for Estate model.
    
    Provides filtering capabilities for estate queries.
    """
    
    name = django_filters.CharFilter(
        field_name='name',
        lookup_expr='icontains',
        label='Estate name (contains)'
    )
    estate_type = django_filters.ChoiceFilter(
        choices=Estate.EstateType.choices,
        label='Estate type'
    )
    fee_frequency = django_filters.ChoiceFilter(
        choices=Estate.FeeFrequency.choices,
        label='Fee frequency'
    )
    is_active = django_filters.BooleanFilter(
        field_name='is_active',
        label='Is active'
    )
    min_units = django_filters.NumberFilter(
        field_name='approximate_units',
        lookup_expr='gte',
        label='Minimum units'
    )
    max_units = django_filters.NumberFilter(
        field_name='approximate_units',
        lookup_expr='lte',
        label='Maximum units'
    )
    created_after = django_filters.DateTimeFilter(
        field_name='created_at',
        lookup_expr='gte',
        label='Created after'
    )
    created_before = django_filters.DateTimeFilter(
        field_name='created_at',
        lookup_expr='lte',
        label='Created before'
    )
    
    class Meta:
        model = Estate
        fields = [
            'name',
            'estate_type',
            'fee_frequency',
            'is_active',
        ]
