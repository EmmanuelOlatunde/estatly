# reports/tests/test_urls.py
"""
Tests for reports app URL routing.

Coverage:
- URL pattern resolution
- URL reverse lookup
- Router registration
"""

import pytest
from django.urls import reverse, resolve
import uuid


@pytest.mark.django_db
class TestReportsURLs:
    """Test URL routing for reports endpoints."""
    
    def test_fee_payment_status_url_resolves(self):
        """Test fee payment status URL resolves correctly."""
        fee_id = uuid.uuid4()
        url = reverse('reports:reports-fee-payment-status', kwargs={'fee_id': fee_id})
        assert url == f'/api/reports/fee/{fee_id}/'
        
        resolver = resolve(url)
        assert resolver.view_name == 'reports:reports-fee-payment-status'
    
    def test_overall_summary_url_resolves(self):
        """Test overall summary URL resolves correctly."""
        url = reverse('reports:reports-overall-summary')
        assert url == '/api/reports/overall-summary/'
        
        resolver = resolve(url)
        assert resolver.view_name == 'reports:reports-overall-summary'
    
    def test_estate_summary_url_resolves(self):
        """Test estate summary URL resolves correctly."""
        estate_id = uuid.uuid4()
        url = reverse('reports:reports-estate-summary', kwargs={'estate_id': estate_id})
        assert url == f'/api/reports/estate/{estate_id}/'
        
        resolver = resolve(url)
        assert resolver.view_name == 'reports:reports-estate-summary'
    
    def test_all_report_urls_use_correct_app_namespace(self):
        """Test all URLs use 'reports' namespace."""
        fee_id = uuid.uuid4()
        estate_id = uuid.uuid4()
        
        urls = [
            reverse('reports:reports-fee-payment-status', kwargs={'fee_id': fee_id}),
            reverse('reports:reports-overall-summary'),
            reverse('reports:reports-estate-summary', kwargs={'estate_id': estate_id}),
        ]
        
        for url in urls:
            assert url.startswith('/api/reports/')