# tests/__init__.py

"""
Test suite for announcements app.

Run with: pytest tests/

pytest announcements/tests/test_edge_cases.py


Edge Cases & Security

tests/test_edge_cases.py - Boundary conditions and edge cases
tests/test_security.py - Security vulnerabilities (IDOR, XSS, SQL injection)
tests/test_error_handling.py - Error responses and exception handling


# Run all tests
pytest tests/

# Run specific test file
pytest announcements/tests/test_urls.py

# Run with coverage
pytest tests/ --cov=announcements --cov-report=html

# Run specific test class
pytest tests/test_views_create.py::TestAnnouncementCreate

# Run with verbose output
pytest tests/ -v

# Run parallel (if pytest-xdist installed)
pytest tests/ -n auto


URL & Component Tests

tests/test_urls.py - URL routing and reverse resolution
tests/test_permissions.py - Permission class unit tests
tests/test_serializers.py - Serializer validation and field tests


tests/__init__.py - Test package initialization
tests/conftest.py - Global fixtures (users, clients, JWT, test data)
tests/factories.py - Factory Boy factories for models
tests/helpers.py - Shared test utilities


View Tests (CRUD)

tests/test_views_list.py - List endpoint (GET)
tests/test_views_retrieve.py - Retrieve endpoint (GET detail)
tests/test_views_create.py - Create endpoint (POST)
tests/test_views_update.py - Update endpoints (PUT/PATCH)
tests/test_views_delete.py - Delete endpoint (DELETE)
Advanced Features

tests/test_custom_actions.py - Print announcement action
tests/test_filters.py - Filtering and search functionality
tests/test_pagination_ordering.py - Pagination and ordering

"""