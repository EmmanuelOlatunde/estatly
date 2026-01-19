# announcements/filters.py

"""
Filter classes for announcements app.

Provides advanced filtering capabilities for announcement queries.
"""
import uuid

import django_filters
from django.db.models import Q
from .models import Announcement
from django.core.exceptions import ValidationError


class AnnouncementFilter(django_filters.FilterSet):
    """
    FilterSet for advanced announcement filtering.
    
    Provides filters for:
    - Active status
    - Date range (created_at, updated_at)
    - Creator
    - Title and message search
    """
    
    title = django_filters.CharFilter(
        field_name='title',
        lookup_expr='icontains',
        label='Title contains'
    )
    
    message = django_filters.CharFilter(
        field_name='message',
        lookup_expr='icontains',
        label='Message contains'
    )
    
    search = django_filters.CharFilter(
        method='filter_search',
        label='Search in title or message'
    )
    
    is_active = django_filters.BooleanFilter(
        field_name='is_active',
        label='Is active'
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
    
    updated_after = django_filters.DateTimeFilter(
        field_name='updated_at',
        lookup_expr='gte',
        label='Updated after'
    )
    
    updated_before = django_filters.DateTimeFilter(
        field_name='updated_at',
        lookup_expr='lte',
        label='Updated before'
    )
    
    created_by = django_filters.CharFilter(method='filter_created_by')

    
    class Meta:
        model = Announcement
        fields = [
            'created_by',
        ]
    
    def filter_search(self, queryset, name, value):
        """
        Custom filter method for searching across multiple fields.
        
        Searches in both title and message fields.
        
        Args:
            queryset: Base queryset to filter
            name: Filter field name
            value: Search value
        
        Returns:
            Filtered queryset
        """
        if not value:
            return queryset
        
        return queryset.filter(
            Q(title__icontains=value) | Q(message__icontains=value)
        )

    def filter_created_by(self, queryset, name, value):
        """
        Safely filter by creator UUID.
        Invalid UUIDs return an empty queryset instead of raising errors.
        """
        try:
            uuid_value = uuid.UUID(str(value))
        except (ValueError, TypeError, AttributeError):
            return queryset.none()

        return queryset.filter(created_by__id=uuid_value)
