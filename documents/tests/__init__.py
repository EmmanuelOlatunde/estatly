# tests/__init__.py
"""
Test suite for documents app.

Run with: pytest tests/
# Install dependencies
pip install -r requirements-test.txt
# Run with coverage
pytest tests/ --cov=documents --cov-report=html

# Run specific test file
pytest tests/test_security.py

# Run with specific marker
pytest tests/ -v -k "test_owner"

tests/__init__.py - Test package initialization
✅ tests/conftest.py - Global fixtures (users, clients, JWT)
✅ tests/factories.py - Factory Boy factories for all models
✅ tests/helpers.py - Shared test utilities
✅ tests/test_urls.py - URL routing tests

✅ tests/test_permissions.py - Permission class unit tests


# Run all tests
pytest documents/tests/test_security.py

✅ tests/test_serializers.py - Serializer validation tests
✅ tests/test_views_list.py - List endpoint tests
✅ tests/test_views_retrieve.py - Detail endpoint tests
✅ tests/test_views_create.py - Create endpoint tests

✅ tests/test_views_update.py - Update endpoint tests
✅ tests/test_views_delete.py - Delete endpoint tests

✅ tests/test_custom_actions.py - Custom @action tests
✅ tests/test_filters.py - Filtering tests
✅ tests/.py - Pagination tests
✅ tests/.py - Ordering/sorting tests
✅ tests/test_edge_cases.py - Edge cases & boundaries
✅ tests/.py - Error response tests

✅ tests/test_security.py - Security vulnerability tests
✅ pytest.ini - Pytest configuration
✅ requirements-test.txt - Test dependencies
"""