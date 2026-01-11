
# tests/test_filters.py
"""
Tests for estate filtering functionality.

Coverage:
- All filter parameters
- Filter combinations
- Edge cases
"""

import pytest
from datetime import  timedelta
from django.utils import timezone
from .helpers import get_estate_list_url
from .factories import EstateFactory
from estates.models import Estate


@pytest.mark.django_db
class TestEstateFilters:
    """Test EstateFilter functionality."""
    
    def test_filter_created_after(self, authenticated_client):
        """Test filtering by created_after date."""
        now = timezone.now()
        old_estate = EstateFactory.create()
        old_estate.created_at = now - timedelta(days=10)
        old_estate.save()
        
        new_estate = EstateFactory.create()
        
        url = get_estate_list_url()
        cutoff = (now - timedelta(days=5)).isoformat()
        response = authenticated_client.get(url, {'created_after': cutoff})
        
        assert response.status_code == 200
        assert len(response.data['results']) == 1
        assert response.data['results'][0]['id'] == str(new_estate.id)
    
    def test_filter_created_before(self, authenticated_client):
        """Test filtering by created_before date."""
        now = timezone.now()
        old_estate = EstateFactory.create()
        old_estate.created_at = now - timedelta(days=10)
        old_estate.save()
        
        new_estate = EstateFactory.create()  # noqa: F841
        
        url = get_estate_list_url()
        cutoff = (now - timedelta(days=5)).isoformat()
        response = authenticated_client.get(url, {'created_before': cutoff})
        
        assert response.status_code == 200
        assert len(response.data['results']) == 1
        assert response.data['results'][0]['id'] == str(old_estate.id)
    
    def test_filter_by_unit_range(self, authenticated_client):
        """Test filtering by min and max units together."""
        EstateFactory.create(approximate_units=50)
        mid_estate = EstateFactory.create(approximate_units=100)
        EstateFactory.create(approximate_units=200)
        
        url = get_estate_list_url()
        response = authenticated_client.get(url, {
            'min_units': '75',
            'max_units': '150'
        })
        
        assert response.status_code == 200
        assert len(response.data['results']) == 1
        assert response.data['results'][0]['id'] == str(mid_estate.id)
    
    def test_filter_with_all_parameters(self, authenticated_client):
        """Test using all filter parameters together."""
        target_estate = EstateFactory.create(
            name="Target Estate",
            estate_type=Estate.EstateType.PRIVATE,
            fee_frequency=Estate.FeeFrequency.MONTHLY,
            is_active=True,
            approximate_units=100
        )
        
        EstateFactory.create(
            estate_type=Estate.EstateType.GOVERNMENT,
            fee_frequency=Estate.FeeFrequency.MONTHLY
        )
        
        url = get_estate_list_url()
        response = authenticated_client.get(url, {
            'name': 'target',
            'estate_type': 'PRIVATE',
            'fee_frequency': 'MONTHLY',
            'is_active': 'true',
            'min_units': '50'
        })
        
        assert response.status_code == 200
        assert len(response.data['results']) == 1
        assert response.data['results'][0]['id'] == str(target_estate.id)

