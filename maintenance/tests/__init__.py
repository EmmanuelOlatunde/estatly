# tests/__init__.py

"""
Test suite for the maintenance app.

This package contains comprehensive tests for all maintenance app functionality
including views, serializers, permissions, filters, and edge cases.


# Run all tests
pytest maintenance/tests/

# Run with coverage
pytest maintenance/tests/ --cov=maintenance --cov-report=html

# Run specific file
pytest tests/test_views_create.py -v

# Run specific test
pytest tests/test_security.py::TestIDORVulnerabilities::test_user_cannot_access_other_users_ticket_detail -v

Core Test Files ✅

tests/__init__.py - Package initialization
tests/conftest.py - Global pytest fixtures
tests/factories.py - Factory Boy factories
tests/helpers.py - Reusable test utilities

URL & Permission Tests ✅

tests/test_urls.py - URL routing tests
tests/test_permissions.py - Permission class tests

Serializer Tests ✅

tests/test_serializers.py - Serializer validation & fields (NEW!)

View Tests (CRUD) ✅

tests/test_views_list.py - List endpoint
tests/test_views_retrieve.py - Retrieve endpoint
tests/test_views_create.py - Create endpoint
tests/test_views_update.py - Update endpoint (NEW!)
tests/test_views_delete.py - Delete endpoint (NEW!)

Custom Actions ✅

tests/test_custom_actions.py - Resolve, reopen, statistics

Filtering & Ordering ✅

tests/test_filters.py - All filter parameters
tests/test_pagination_ordering.py - Pagination & ordering (NEW!)

Security & Edge Cases ✅

tests/test_security.py - IDOR, SQL injection, XSS, mass assignment
tests/test_edge_cases.py - Boundary conditions, special chars (NEW!)
tests/test_error_handling.py - Error responses & formats (NEW!)

Integration Tests ✅

tests/test_integration.py - Multi-endpoint workflows (NEW!)
"""