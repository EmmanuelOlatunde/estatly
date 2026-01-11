

# core/filters.py
"""
Filter classes for core app.
Provides base filters for other apps.
"""

import django_filters


class EstateFilterMixin(django_filters.FilterSet):
    """
    Base filter mixin for estate-scoped models.
    Provides common filtering patterns.
    """
    
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
        abstract = True

