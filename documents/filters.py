"""
Filter classes for documents app.
"""
from django.db.models import Q

import django_filters
# from django.db.models import Q
from .models import Document, DocumentDownload, DocumentType, DocumentStatus


class DocumentFilter(django_filters.FilterSet):
    """
    FilterSet for Document model with common query patterns.
    """
    
    document_type = django_filters.CharFilter(
        field_name='document_type',
        help_text='Filter by document type'
    )
    status = django_filters.CharFilter(
        field_name='status',
        help_text='Filter by generation status'
    )
    related_user = django_filters.UUIDFilter(
        field_name='related_user__id',
        help_text='Filter by related user ID'
    )
    related_payment_id = django_filters.UUIDFilter(
        field_name='related_payment_id',
        help_text='Filter by related payment ID'
    )
    related_announcement_id = django_filters.UUIDFilter(
        field_name='related_announcement_id',
        help_text='Filter by related announcement ID'
    )
    
    created_after = django_filters.DateTimeFilter(
        field_name='created_at',
        lookup_expr='gte',
        help_text='Filter documents created after this datetime'
    )
    created_before = django_filters.DateTimeFilter(
        field_name='created_at',
        lookup_expr='lte',
        help_text='Filter documents created before this datetime'
    )
    
    generated_after = django_filters.DateTimeFilter(
        field_name='generated_at',
        lookup_expr='gte',
        help_text='Filter documents generated after this datetime'
    )
    generated_before = django_filters.DateTimeFilter(
        field_name='generated_at',
        lookup_expr='lte',
        help_text='Filter documents generated before this datetime'
    )
    
    is_deleted = django_filters.BooleanFilter(
        field_name='is_deleted',
        help_text='Include deleted documents'
    )
    
    has_file = django_filters.BooleanFilter(
        method='filter_has_file',
        help_text='Filter by whether document has a file attached'
    )
    
    search = django_filters.CharFilter(
        method='filter_search',
        help_text='Search in title and error message'
    )
    
    class Meta:
        model = Document
        fields = [

        ]
    
    def filter_has_file(self, queryset, name, value):
        """Filter documents that have or don't have a file."""
        if value:
            return queryset.exclude(file='')
        return queryset.filter(file='')
    
    def filter_search(self, queryset, name, value):
        if not value:
            return queryset
        return queryset.filter(
            Q(title__icontains=value)
        )



class DocumentDownloadFilter(django_filters.FilterSet):
    """
    FilterSet for DocumentDownload model.
    """
    
    document = django_filters.UUIDFilter(
        field_name='document__id',
        help_text='Filter by document ID'
    )
    user = django_filters.UUIDFilter(
        field_name='user__id',
        help_text='Filter by user ID'
    )
    document_type = django_filters.ChoiceFilter(
        field_name='document__document_type',
        choices=DocumentType.choices,
        help_text='Filter by document type'
    )
    
    downloaded_after = django_filters.DateTimeFilter(
        field_name='downloaded_at',
        lookup_expr='gte',
        help_text='Filter downloads after this datetime'
    )
    downloaded_before = django_filters.DateTimeFilter(
        field_name='downloaded_at',
        lookup_expr='lte',
        help_text='Filter downloads before this datetime'
    )
    
    ip_address = django_filters.CharFilter(
        field_name='ip_address',
        lookup_expr='exact',
        help_text='Filter by IP address'
    )
    
    class Meta:
        model = DocumentDownload
        fields = [
            'document',
            'user',
            'document_type',
        ]