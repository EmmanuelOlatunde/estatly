# tests/__init__.py

"""
Test suite for the payments app.

pytest payments/tests/


tests/__init__.py - Package initialization
tests/conftest.py - Global fixtures (users, auth clients, test data)
tests/factories.py - Factory Boy factories for all models
tests/helpers.py - Shared assertion utilities
tests/test_urls.py - URL routing tests
tests/test_permissions.py - Permission class unit tests
tests/test_serializers.py - Serializer validation tests
tests/test_views_list.py - List endpoint tests
tests/test_views_retrieve.py - Detail/retrieve endpoint tests
tests/test_views_create.py - Create/POST endpoint tests
tests/test_views_update.py - Update/PATCH/PUT endpoint tests
tests/test_views_delete.py - Delete endpoint tests
tests/test_custom_actions.py - Custom @action tests
tests/test_filters.py - Filter & query parameter tests
tests/test_pagination.py - Pagination tests
tests/test_ordering.py - Ordering/sorting tests
tests/test_edge_cases.py - Boundary conditions & edge cases
tests/test_error_handling.py - Error response tests
tests/test_security.py - Security-specific tests (IDOR, XSS, etc.)
"""