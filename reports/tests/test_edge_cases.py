# reports/tests/test_edge_cases.py
"""
Tests for edge cases and boundary conditions.

Coverage:
- Empty datasets
- Boundary values
- Special characters
- Concurrent operations
- Timezone edge cases
"""

import pytest
from django.urls import reverse
from rest_framework import status
from decimal import Decimal
from datetime import date, timedelta
import uuid
from payments.models import FeeAssignment


@pytest.mark.django_db
class TestEmptyDatasets:
    """Test behavior with empty datasets."""
    
    def test_overall_summary_with_no_estates(self, estate_manager_client):
        """Test overall summary when landlord has no estates."""
        url = reverse('reports:reports-overall-summary')
        response = estate_manager_client.get(url)
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['total_fees'] == 0
        assert response.data['total_expected_all_fees'] == '0.00'
        assert len(response.data['fees_summary']) == 0
    
    def test_fee_report_with_no_units(self, estate_manager_client, estate):
        """Test fee report when estate has no units."""
        from .factories import FeeFactory
        
        fee = FeeFactory.create(estate=estate)
        url = reverse('reports:reports-fee-payment-status', kwargs={'fee_id': fee.id})
        response = estate_manager_client.get(url)
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['total_units'] == 0
        assert response.data['total_expected'] == '0.00'
    
    def test_fee_report_with_all_vacant_units(self, estate_manager_client, estate):
        """Test fee report when all units are vacant."""
        from .factories import FeeFactory, UnitFactory
        
        fee = FeeFactory.create(estate=estate)
        UnitFactory.create_batch(5, estate=estate, is_occupied=False)
        
        url = reverse('reports:reports-fee-payment-status', kwargs={'fee_id': fee.id})
        response = estate_manager_client.get(url)
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['total_units'] == 0


@pytest.mark.django_db
class TestBoundaryValues:
    """Test boundary value conditions."""
    
    def test_fee_with_zero_amount(self, estate_manager_client, estate):
        """Test fee report with zero amount."""
        from .factories import FeeFactory, UnitFactory
        
        fee = FeeFactory.create(estate=estate, amount=Decimal('0.00'))
        UnitFactory.create_batch(3, estate=estate, is_occupied=True)
        
        url = reverse('reports:reports-fee-payment-status', kwargs={'fee_id': fee.id})
        response = estate_manager_client.get(url)
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['total_expected'] == '0.00'
    
    def test_fee_with_very_large_amount(self, estate_manager_client, estate):
        """Test fee report with very large amount."""
        from .factories import FeeFactory, UnitFactory
        
        fee = FeeFactory.create(estate=estate, amount=Decimal('999999999.99'))
        UnitFactory.create(estate=estate, is_occupied=True)
        
        url = reverse('reports:reports-fee-payment-status', kwargs={'fee_id': fee.id})
        response = estate_manager_client.get(url)
        
        assert response.status_code == status.HTTP_200_OK
        assert Decimal(response.data['total_expected']) == Decimal('999999999.99')
    
    def test_fee_with_many_decimal_places(self, estate_manager_client, estate):
        """Test fee with precise decimal places."""
        from .factories import FeeFactory, UnitFactory
        
        fee = FeeFactory.create(estate=estate, amount=Decimal('100.99'))
        UnitFactory.create(estate=estate, is_occupied=True)
        
        url = reverse('reports:reports-fee-payment-status', kwargs={'fee_id': fee.id})
        response = estate_manager_client.get(url)
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['total_expected'] == '100.99'
    
    def test_100_percent_payment_rate(self, estate_manager_client, fee, units):
        """Test report when payment rate is exactly 100%."""
        from .factories import PaymentFactory, FeeAssignmentFactory
        
        # Create payments for all units
        for unit in units:
            assignment = FeeAssignmentFactory.create(
                fee=fee,
                unit=unit,
                status=FeeAssignment.PaymentStatus.PAID
            )
            PaymentFactory.create(
                fee_assignment=assignment,
                amount=fee.amount
            )

        
        url = reverse('reports:reports-fee-payment-status', kwargs={'fee_id': fee.id})
        response = estate_manager_client.get(url)
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['payment_rate'] == '100.00'
        assert response.data['unpaid_units_count'] == 0
    
    def test_zero_percent_payment_rate(self, estate_manager_client, fee, units):
        """Test report when payment rate is 0%."""
        url = reverse('reports:reports-fee-payment-status', kwargs={'fee_id': fee.id})
        response = estate_manager_client.get(url)
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['payment_rate'] == '0.00'
        assert response.data['unpaid_units_count'] == len(units)


@pytest.mark.django_db
class TestInvalidInputs:
    """Test handling of invalid inputs."""
    
    def test_invalid_uuid_format_for_fee(self, estate_manager_client):
        """Test invalid UUID format for fee ID."""
        url = '/api/reports/fee/not-a-uuid/'
        response = estate_manager_client.get(url)
        
        assert response.status_code in [status.HTTP_404_NOT_FOUND, status.HTTP_400_BAD_REQUEST]
    
    def test_invalid_uuid_format_for_estate(self, estate_manager_client):
        """Test invalid UUID format for estate ID."""
        url = '/api/reports/estate/invalid-uuid/'
        response = estate_manager_client.get(url)
        
        assert response.status_code in [status.HTTP_404_NOT_FOUND, status.HTTP_400_BAD_REQUEST]
    
    def test_invalid_estate_id_query_param(self, estate_manager_client):
        """Test invalid estate_id in query parameters."""
        url = reverse('reports:reports-overall-summary')
        response = estate_manager_client.get(url, {'estate_id': 'not-a-uuid'})
        
        # Should either ignore or return 400
        assert response.status_code in [status.HTTP_200_OK, status.HTTP_400_BAD_REQUEST]


@pytest.mark.django_db
class TestDateEdgeCases:
    """Test date and time edge cases."""
    
    def test_fee_due_today(self, estate_manager_client, estate):
        """Test fee report for fee due today."""
        from .factories import FeeFactory, UnitFactory
        
        fee = FeeFactory.create(estate=estate, due_date=date.today())
        unit = UnitFactory.create(estate=estate, is_occupied=True)
        
        url = reverse('reports:reports-fee-payment-status', kwargs={'fee_id': fee.id})
        response = estate_manager_client.get(url)
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['unpaid_units'][0]['days_overdue'] == 0
    
    def test_fee_due_in_future(self, estate_manager_client, estate):
        """Test fee report for fee due in future."""
        from .factories import FeeFactory, UnitFactory
        
        future_date = date.today() + timedelta(days=30)
        fee = FeeFactory.create(estate=estate, due_date=future_date)
        unit = UnitFactory.create(estate=estate, is_occupied=True)
        
        url = reverse('reports:reports-fee-payment-status', kwargs={'fee_id': fee.id})
        response = estate_manager_client.get(url)
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['unpaid_units'][0]['days_overdue'] == 0
    
    def test_fee_very_overdue(self, estate_manager_client, estate):
        """Test fee report for very overdue fee."""
        from .factories import FeeFactory, UnitFactory
        
        old_date = date.today() - timedelta(days=365)
        fee = FeeFactory.create(estate=estate, due_date=old_date)
        unit = UnitFactory.create(estate=estate, is_occupied=True)
        
        url = reverse('reports:reports-fee-payment-status', kwargs={'fee_id': fee.id})
        response = estate_manager_client.get(url)
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['unpaid_units'][0]['days_overdue'] == 365


@pytest.mark.django_db
class TestSpecialCharacters:
    """Test handling of special characters in data."""
    
    def test_fee_name_with_special_characters(self, estate_manager_client, estate):
        """Test fee report with special characters in fee name."""
        from .factories import FeeFactory, UnitFactory
        
        fee = FeeFactory.create(estate=estate, name="Rent & Utilities (50%)")
        unit = UnitFactory.create(estate=estate, is_occupied=True)
        
        url = reverse('reports:reports-fee-payment-status', kwargs={'fee_id': fee.id})
        response = estate_manager_client.get(url)
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['fee_name'] == "Rent & Utilities (50%)"
    
    def test_unit_name_with_unicode(self, estate_manager_client, estate):
        """Test report with unicode characters in unit name."""
        from .factories import FeeFactory, UnitFactory
        
        fee = FeeFactory.create(estate=estate)
        unit = UnitFactory.create(estate=estate, identifier="Unit 日本語", is_occupied=True)
        
        url = reverse('reports:reports-fee-payment-status', kwargs={'fee_id': fee.id})
        response = estate_manager_client.get(url)
        
        assert response.status_code == status.HTTP_200_OK
        assert any('日本語' in u['unit_name'] for u in response.data['unpaid_units'])


@pytest.mark.django_db
class TestLargeDatasets:
    """Test performance with large datasets."""
    
    def test_fee_report_with_many_units(self, estate_manager_client, estate):
        """Test fee report with 100+ units."""
        from .factories import FeeFactory, UnitFactory
        
        fee = FeeFactory.create(estate=estate)
        UnitFactory.create_batch(100, estate=estate, is_occupied=True)
        
        url = reverse('reports:reports-fee-payment-status', kwargs={'fee_id': fee.id})
        response = estate_manager_client.get(url)
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['total_units'] == 100
        assert len(response.data['unpaid_units']) == 100
    
    def test_overall_summary_with_many_fees(self, estate_manager_client, estate):
        """Test overall summary with many fees."""
        from .factories import FeeFactory
        
        FeeFactory.create_batch(50, estate=estate)
        
        url = reverse('reports:reports-overall-summary')
        response = estate_manager_client.get(url)
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['total_fees'] >= 50
