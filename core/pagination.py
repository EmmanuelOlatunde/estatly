
# core/pagination.py
"""
Custom pagination classes for Estatly APIs.
"""

from rest_framework.pagination import PageNumberPagination


class StandardResultsPagination(PageNumberPagination):
    """
    Standard pagination for list endpoints.
    """
    page_size = 10
    page_size_query_param = 'page_size'
    max_page_size = 100


class LargeResultsPagination(PageNumberPagination):
    """
    Pagination for endpoints with potentially large datasets.
    """
    page_size = 50
    page_size_query_param = 'page_size'
    max_page_size = 200


