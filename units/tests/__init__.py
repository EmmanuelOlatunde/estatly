# tests/__init__.py
"""
Test suite for the units app.

# Run all tests
pytest units/tests/
 # Run with coverage
pytest tests/ --cov=units --cov-report=html

# Run specific test file
pytest tests/test_security.py

# Run with verbose output
pytest tests/ -v

# Run tests in parallel
pytest tests/ -n auto

venv\scripts\activate
cd estatly


Files Generated (13 files)

tests/__init__.py - Package initialization
tests/conftest.py - Global fixtures (users, clients, common data)
tests/factories.py - Factory Boy factories for all models
tests/helpers.py - Shared utility functions
tests/test_urls.py - URL routing tests (7 tests)
tests/test_permissions.py - Permission class tests (9 tests)
tests/test_serializers.py - Serializer validation tests (20 tests)
tests/test_views_list.py - List endpoint tests (26 tests)
tests/test_views_retrieve.py - Retrieve/detail endpoint tests (14 tests)
tests/test_views_create.py - Create endpoint tests (20 tests)
tests/test_views_update.py - Update endpoint tests (16 tests)
tests/test_views_delete.py - Delete endpoint tests (10 tests)
tests/test_custom_actions.py - Custom actions tests (19 tests)
tests/test_filters.py - Filtering functionality tests (18 tests)
tests/test_pagination_ordering.py - Pagination & ordering tests (17 tests)
tests/test_edge_cases.py - Edge cases & boundaries (30 tests)
tests/test_error_handling.py - Error handling tests (23 tests)
tests/test_security.py - Security vulnerability tests (27 tests)
"""

# pytest units/tests/test_security.py

# estate = estate_factory()
# "estate": estate, 