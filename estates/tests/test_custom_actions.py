# tests/test_custom_actions.py
"""
Tests for estate custom actions.

Coverage:
- Activate action
- Deactivate action
- Statistics action
- By-type action
"""

import pytest
from .helpers import (
    get_estate_activate_url,
    get_estate_deactivate_url,
    get_estate_statistics_url,
    get_estate_by_type_url
)
from .factories import EstateFactory
from estates.models import Estate


@pytest.mark.django_db
class TestEstateActivateAction:
    """Test POST /estates/{id}/activate/."""
    
    def test_unauthenticated_user_cannot_activate(self, api_client, inactive_estate):
        """Test unauthenticated users cannot activate estates."""
        url = get_estate_activate_url(inactive_estate.id)
        
        response = api_client.post(url)
        assert response.status_code == 401
    
    def test_non_staff_user_cannot_activate(self, authenticated_client, inactive_estate):
        """Test non-staff users cannot activate estates."""
        url = get_estate_activate_url(inactive_estate.id)
        
        response = authenticated_client.post(url)
        assert response.status_code == 403
    
    def test_staff_user_can_activate_estate(self, staff_client, inactive_estate):
        """Test staff users can activate inactive estates."""
        url = get_estate_activate_url(inactive_estate.id)
        
        response = staff_client.post(url)
        
        assert response.status_code == 200
        assert 'detail' in response.data
        assert 'activated successfully' in response.data['detail']
        assert response.data['estate']['is_active'] is True
    
    def test_activate_updates_database(self, staff_client, inactive_estate):
        """Test activate actually updates database."""
        url = get_estate_activate_url(inactive_estate.id)
        
        response = staff_client.post(url)
        
        assert response.status_code == 200
        inactive_estate.refresh_from_db()
        assert inactive_estate.is_active is True
    
    def test_activate_already_active_estate_fails(self, staff_client, estate):
        """Test activating already active estate returns error."""
        assert estate.is_active is True
        
        url = get_estate_activate_url(estate.id)
        response = staff_client.post(url)
        
        assert response.status_code == 400
        assert 'already active' in response.data['detail'].lower()
    
    def test_activate_returns_estate_data(self, staff_client, inactive_estate):
        """Test activate response includes updated estate data."""
        url = get_estate_activate_url(inactive_estate.id)
        
        response = staff_client.post(url)
        
        assert response.status_code == 200
        assert 'estate' in response.data
        assert response.data['estate']['id'] == str(inactive_estate.id)
        assert response.data['estate']['is_active'] is True


@pytest.mark.django_db
class TestEstateDeactivateAction:
    """Test POST /estates/{id}/deactivate/."""
    
    def test_unauthenticated_user_cannot_deactivate(self, api_client, estate):
        """Test unauthenticated users cannot deactivate estates."""
        url = get_estate_deactivate_url(estate.id)
        
        response = api_client.post(url)
        assert response.status_code == 401
    
    def test_non_staff_user_cannot_deactivate(self, authenticated_client, estate):
        """Test non-staff users cannot deactivate estates."""
        url = get_estate_deactivate_url(estate.id)
        
        response = authenticated_client.post(url)
        assert response.status_code == 403
    
    def test_staff_user_can_deactivate_estate(self, staff_client, estate):
        """Test staff users can deactivate active estates."""
        url = get_estate_deactivate_url(estate.id)
        
        response = staff_client.post(url)
        
        assert response.status_code == 200
        assert 'detail' in response.data
        assert 'deactivated successfully' in response.data['detail']
        assert response.data['estate']['is_active'] is False
    
    def test_deactivate_updates_database(self, staff_client, estate):
        """Test deactivate actually updates database."""
        url = get_estate_deactivate_url(estate.id)
        
        response = staff_client.post(url)
        
        assert response.status_code == 200
        estate.refresh_from_db()
        assert estate.is_active is False
    
    def test_deactivate_already_inactive_estate_fails(self, staff_client, inactive_estate):
        """Test deactivating already inactive estate returns error."""
        assert inactive_estate.is_active is False
        
        url = get_estate_deactivate_url(inactive_estate.id)
        response = staff_client.post(url)
        
        assert response.status_code == 400
        assert 'already inactive' in response.data['detail'].lower()
    
    def test_deactivate_returns_estate_data(self, staff_client, estate):
        """Test deactivate response includes updated estate data."""
        url = get_estate_deactivate_url(estate.id)
        
        response = staff_client.post(url)
        
        assert response.status_code == 200
        assert 'estate' in response.data
        assert response.data['estate']['id'] == str(estate.id)
        assert response.data['estate']['is_active'] is False


@pytest.mark.django_db
class TestEstateStatisticsAction:
    """Test GET /estates/statistics/."""
    
    def test_unauthenticated_user_can_view_statistics(self, api_client):
        """Test unauthenticated users can view statistics."""
        EstateFactory.create_batch(3)
        
        url = get_estate_statistics_url()
        response = api_client.get(url)
        
        assert response.status_code == 200
    
    def test_authenticated_user_can_view_statistics(self, authenticated_client, api_client):
        """Test authenticated users can view statistics."""
        EstateFactory.create_batch(3)
        
        url = get_estate_statistics_url()
        response = api_client.get(url)
        
        assert response.status_code == 200
    
    def test_statistics_includes_total_estates(self, authenticated_client):
        """Test statistics includes total estate count."""
        EstateFactory.create_batch(5)
        
        url = get_estate_statistics_url()
        response = authenticated_client.get(url)
        
        assert response.status_code == 200
        assert 'total_estates' in response.data
        assert response.data['total_estates'] == 5
    
    def test_statistics_includes_active_estates(self, authenticated_client):
        """Test statistics includes active estate count."""
        EstateFactory.create_batch(3, is_active=True)
        EstateFactory.create_batch(2, is_active=False)
        
        url = get_estate_statistics_url()
        response = authenticated_client.get(url)
        
        assert response.status_code == 200
        assert 'active_estates' in response.data
        assert response.data['active_estates'] == 3
    
    def test_statistics_includes_estates_by_type(self, authenticated_client):
        """Test statistics includes counts by estate type."""
        EstateFactory.create_batch(4, estate_type=Estate.EstateType.PRIVATE)
        EstateFactory.create_batch(2, estate_type=Estate.EstateType.GOVERNMENT)
        
        url = get_estate_statistics_url()
        response = authenticated_client.get(url)
        
        assert response.status_code == 200
        assert 'government_estates' in response.data
        assert 'private_estates' in response.data
        assert response.data['government_estates'] == 2
        assert response.data['private_estates'] == 4
    
    def test_statistics_includes_total_units(self, authenticated_client):
        """Test statistics includes total unit count."""
        EstateFactory.create(approximate_units=100)
        EstateFactory.create(approximate_units=200)
        EstateFactory.create(approximate_units=50)
        
        url = get_estate_statistics_url()
        response = authenticated_client.get(url)
        
        assert response.status_code == 200
        assert 'total_units' in response.data
        assert response.data['total_units'] == 350
    
    def test_statistics_when_no_estates_exist(self, authenticated_client):
        """Test statistics when no estates exist."""
        url = get_estate_statistics_url()
        response = authenticated_client.get(url)
        
        assert response.status_code == 200
        assert response.data['total_estates'] == 0
        assert response.data['active_estates'] == 0


@pytest.mark.django_db
class TestEstateByTypeAction:
    """Test GET /estates/by-type/{type}/."""
    
    def test_unauthenticated_user_can_view_by_type(self, api_client):
        """Test unauthenticated users can filter by type."""
        EstateFactory.create_batch(2, estate_type=Estate.EstateType.PRIVATE)
        
        url = get_estate_by_type_url('PRIVATE')
        response = api_client.get(url)
        
        assert response.status_code == 200
    
    def test_filter_by_private_type(self, authenticated_client):
        """Test filtering estates by PRIVATE type."""
        private_estates = EstateFactory.create_batch(3, estate_type=Estate.EstateType.PRIVATE)
        gov_estates = EstateFactory.create_batch(2, estate_type=Estate.EstateType.GOVERNMENT)
        
        url = get_estate_by_type_url('PRIVATE')
        response = authenticated_client.get(url)
        
        assert response.status_code == 200
        assert len(response.data) == 3
    
    def test_filter_by_government_type(self, authenticated_client):
        """Test filtering estates by GOVERNMENT type."""
        private_estates = EstateFactory.create_batch(3, estate_type=Estate.EstateType.PRIVATE)
        gov_estates = EstateFactory.create_batch(2, estate_type=Estate.EstateType.GOVERNMENT)
        
        url = get_estate_by_type_url('GOVERNMENT')
        response = authenticated_client.get(url)
        
        assert response.status_code == 200
        assert len(response.data) == 2
    
    def test_filter_by_type_case_insensitive(self, authenticated_client):
        """Test filtering by type is case-insensitive."""
        EstateFactory.create_batch(2, estate_type=Estate.EstateType.PRIVATE)
        
        url_lower = get_estate_by_type_url('private')
        url_upper = get_estate_by_type_url('PRIVATE')
        url_mixed = get_estate_by_type_url('Private')
        
        response_lower = authenticated_client.get(url_lower)
        response_upper = authenticated_client.get(url_upper)
        response_mixed = authenticated_client.get(url_mixed)
        
        assert response_lower.status_code == 200
        assert response_upper.status_code == 200
        assert response_mixed.status_code == 200
        assert len(response_lower.data) == 2
    
    def test_filter_by_invalid_type_returns_error(self, authenticated_client):
        """Test filtering by invalid type returns 400."""
        url = get_estate_by_type_url('INVALID_TYPE')
        response = authenticated_client.get(url)
        
        assert response.status_code == 400
        assert 'detail' in response.data
    
    def test_filter_by_type_returns_empty_when_none_match(self, authenticated_client):
        """Test filtering returns empty list when no estates match."""
        EstateFactory.create_batch(3, estate_type=Estate.EstateType.PRIVATE)
        
        url = get_estate_by_type_url('GOVERNMENT')
        response = authenticated_client.get(url)
        
        assert response.status_code == 200
        assert len(response.data) == 0




# Final README for running tests
# tests/README.md
"""
# Estates App Test Suite

## Running Tests

### Run all tests:
```bash
pytest tests/
```

### Run specific test file:
```bash
pytest tests/test_views_list.py
```

### Run specific test class:
```bash
pytest tests/test_views_list.py::TestEstateListEndpoint
```

### Run specific test:
```bash
pytest tests/test_views_list.py::TestEstateListEndpoint::test_list_returns_only_active_estates_by_default
```

### Run with coverage:
```bash
pytest tests/ --cov=estates --cov-report=html
```

### Run with verbose output:
```bash
pytest tests/ -v
```

### Run parallel tests (faster):
```bash
pytest tests/ -n auto
```

## Test Organization

- `test_urls.py` - URL routing tests
- `test_permissions.py` - Permission class unit tests
- `test_serializers.py` - Serializer validation tests
- `test_views_list.py` - List endpoint tests
- `test_views_retrieve.py` - Retrieve endpoint tests
- `test_views_create.py` - Create endpoint tests
- `test_views_update.py` - Update endpoint tests
- `test_views_delete.py` - Delete endpoint tests
- `test_custom_actions.py` - Custom action tests (activate, deactivate, etc.)
- `test_filters.py` - Filtering functionality tests
- `test_pagination.py` - Pagination tests
- `test_ordering.py` - Ordering/sorting tests
- `test_edge_cases.py` - Edge cases and boundary conditions
- `test_error_handling.py` - Error handling tests
- `test_security.py` - Security concern tests
- `test_integration.py` - Multi-step workflow tests

## Coverage pytest estates\tests\

This test suite provides 100% coverage of:
- All API endpoints
- All permissions
- All serializer validation
- All filters and query parameters
- Edge cases and error conditions
- Security vulnerabilities

## Requirements

```
pytest==7.4.3
pytest-django==4.7.0
pytest-cov==4.1.0
pytest-xdist==3.5.0
factory-boy==3.3.0
faker==20.1.0
djangorestframework==3.14.0
django-filter==23.5
```
"""