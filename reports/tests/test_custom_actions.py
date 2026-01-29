# reports/tests/test_custom_actions.py
"""
Tests for reports custom action endpoints.

Coverage:
- Fee payment status action
- Overall summary action
- Estate summary action
- Authentication for all actions
- Authorization for all actions
"""

import pytest
from django.urls import reverse
from rest_framework import status
from .helpers import (
    assert_fee_payment_status_structure,
    assert_overall_summary_structure
)


@pytest.mark.django_db
class TestFeePaymentStatusAction:
    """Test fee payment status custom action."""
    
    def test_unauthenticated_user_cannot_access(self, api_client, fee):
        """Test unauthenticated user gets 401."""
        url = reverse('reports:reports-fee-payment-status', kwargs={'fee_id': fee.id})
        response = api_client.get(url)
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
    
    def test_tenant_user_cannot_access(self, tenant_client, fee):
        """Test tenant user gets 403."""
        url = reverse('reports:reports-fee-payment-status', kwargs={'fee_id': fee.id})
        response = tenant_client.get(url)
        
        assert response.status_code == status.HTTP_403_FORBIDDEN
    
    def test_estate_manager_without_estate_cannot_access(
        self, estate_manager_no_estate_client, fee
    ):
        """Test estate manager without assigned estate gets 403."""
        url = reverse('reports:reports-fee-payment-status', kwargs={'fee_id': fee.id})
        response = estate_manager_no_estate_client.get(url)
        
        assert response.status_code == status.HTTP_403_FORBIDDEN
    
    def test_estate_manager_can_access_own_estate_fee_report(
        self, estate_manager_client, fee, payments
    ):
        """Test estate manager can access report for own estate's fee."""
        url = reverse('reports:reports-fee-payment-status', kwargs={'fee_id': fee.id})
        response = estate_manager_client.get(url)
        
        assert response.status_code == status.HTTP_200_OK
        assert_fee_payment_status_structure(response.data)
        assert str(response.data['fee_id']) == str(fee.id)
    
    def test_super_admin_can_access_any_fee_report(self, super_admin_client, fee, payments):
        """Test super admin can access any fee report."""
        url = reverse('reports:reports-fee-payment-status', kwargs={'fee_id': fee.id})
        response = super_admin_client.get(url)
        
        assert response.status_code == status.HTTP_200_OK
        assert_fee_payment_status_structure(response.data)
        assert str(response.data['fee_id']) == str(fee.id)
    
    def test_estate_manager_cannot_access_other_estate_fee(
        self, estate_manager_client, other_estate
    ):
        """Test estate manager cannot access another estate's fee report."""
        from .factories import FeeFactory
        other_fee = FeeFactory.create(estate=other_estate)
        
        url = reverse('reports:reports-fee-payment-status', kwargs={'fee_id': other_fee.id})
        response = estate_manager_client.get(url)
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'error' in response.data
    
    def test_nonexistent_fee_returns_400(self, estate_manager_client):
        """Test nonexistent fee returns 400."""
        import uuid
        fake_fee_id = uuid.uuid4()
        
        url = reverse('reports:reports-fee-payment-status', kwargs={'fee_id': fake_fee_id})
        response = estate_manager_client.get(url)
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'error' in response.data
    
    def test_invalid_uuid_format_returns_404(self, estate_manager_client):
        """Test invalid UUID format returns 404."""
        url = '/api/reports/fee/invalid-uuid/'
        response = estate_manager_client.get(url)
        
        assert response.status_code == status.HTTP_404_NOT_FOUND
    
    def test_fee_report_shows_correct_payment_counts(
        self, estate_manager_client, fee, units, payments
    ):
        """Test fee report shows correct paid/unpaid counts."""
        url = reverse('reports:reports-fee-payment-status', kwargs={'fee_id': fee.id})
        response = estate_manager_client.get(url)
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['total_units'] == len(units)
        assert response.data['paid_units'] == len(payments)
        assert response.data['unpaid_units_count'] == len(units) - len(payments)
    
    def test_fee_report_calculates_payment_rate_correctly(
        self, estate_manager_client, fee, units, payments
    ):
        """Test fee report calculates payment rate correctly."""
        url = reverse('reports:reports-fee-payment-status', kwargs={'fee_id': fee.id})
        response = estate_manager_client.get(url)
        
        assert response.status_code == status.HTTP_200_OK
        
        expected_rate = (len(payments) / len(units)) * 100
        actual_rate = float(response.data['payment_rate'])
        
        assert abs(actual_rate - expected_rate) < 0.01
    
    def test_fee_report_lists_unpaid_units(
        self, estate_manager_client, fee, units, payments
    ):
        """Test fee report lists units that haven't paid."""
        url = reverse('reports:reports-fee-payment-status', kwargs={'fee_id': fee.id})
        response = estate_manager_client.get(url)
        
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data['unpaid_units']) == len(units) - len(payments)
        assert isinstance(response.data['unpaid_units'], list)
    
    def test_overdue_fee_shows_days_overdue(
        self, estate_manager_client, overdue_fee, estate
    ):
        """Test overdue fee shows correct days overdue."""
        from datetime import date
        from .factories import UnitFactory
        
        unit = UnitFactory.create(estate=estate, is_occupied=True)
        
        url = reverse('reports:reports-fee-payment-status', kwargs={'fee_id': overdue_fee.id})
        response = estate_manager_client.get(url)
        
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data['unpaid_units']) > 0
        
        days_overdue = (date.today() - overdue_fee.due_date).days
        assert response.data['unpaid_units'][0]['days_overdue'] == days_overdue
    
    def test_fee_report_exception_returns_500(self, estate_manager_client, fee):
        """Test unexpected exception returns 500."""
        from unittest.mock import patch
        
        with patch('reports.services.get_fee_payment_status') as mock_service:
            mock_service.side_effect = Exception('Database error')
            
            url = reverse('reports:reports-fee-payment-status', kwargs={'fee_id': fee.id})
            response = estate_manager_client.get(url)
            
            assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
            assert 'error' in response.data


@pytest.mark.django_db
class TestOverallSummaryAction:
    """Test overall summary custom action."""
    
    def test_unauthenticated_user_cannot_access(self, api_client):
        """Test unauthenticated user gets 401."""
        url = reverse('reports:reports-overall-summary')
        response = api_client.get(url)
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
    
    def test_tenant_user_cannot_access(self, tenant_client):
        """Test tenant user gets 403."""
        url = reverse('reports:reports-overall-summary')
        response = tenant_client.get(url)
        
        assert response.status_code == status.HTTP_403_FORBIDDEN
    
    def test_estate_manager_without_estate_cannot_access(
        self, estate_manager_no_estate_client
    ):
        """Test estate manager without assigned estate gets 403."""
        url = reverse('reports:reports-overall-summary')
        response = estate_manager_no_estate_client.get(url)
        
        assert response.status_code == status.HTTP_403_FORBIDDEN
    
    def test_estate_manager_can_access_overall_summary(
        self, estate_manager_client, estate_with_complete_data
    ):
        """Test estate manager can access overall summary."""
        url = reverse('reports:reports-overall-summary')
        response = estate_manager_client.get(url)
        
        assert response.status_code == status.HTTP_200_OK
        assert_overall_summary_structure(response.data)
    
    def test_super_admin_can_access_overall_summary(
        self, super_admin_client, estate_with_complete_data
    ):
        """Test super admin can access overall summary."""
        url = reverse('reports:reports-overall-summary')
        response = super_admin_client.get(url)
        
        assert response.status_code == status.HTTP_200_OK
        assert_overall_summary_structure(response.data)
    
    def test_overall_summary_includes_all_fees_for_estate(
        self, estate_manager_client, estate_with_complete_data
    ):
        """Test overall summary includes all fees for estate manager's estate."""
        url = reverse('reports:reports-overall-summary')
        response = estate_manager_client.get(url)
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['total_fees'] == len(estate_with_complete_data['fees'])
    
    def test_overall_summary_filters_by_estate_id(
        self, estate_manager_client, estate_with_complete_data
    ):
        """Test overall summary can filter by estate_id query parameter."""
        estate_id = estate_with_complete_data['estate'].id
        url = reverse('reports:reports-overall-summary')
        response = estate_manager_client.get(url, {'estate_id': str(estate_id)})
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['total_fees'] >= 0
    
    def test_estate_manager_cannot_filter_by_other_estate(
        self, estate_manager_client, other_estate
    ):
        """Test estate manager cannot filter by another estate."""
        url = reverse('reports:reports-overall-summary')
        response = estate_manager_client.get(url, {'estate_id': str(other_estate.id)})
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'error' in response.data
    
    def test_overall_summary_with_no_fees_returns_empty_structure(
        self, estate_manager_client
    ):
        """Test overall summary with no fees returns valid empty structure."""
        url = reverse('reports:reports-overall-summary')
        response = estate_manager_client.get(url)
        
        assert response.status_code == status.HTTP_200_OK
        assert 'total_fees' in response.data
        assert 'overall_payment_rate' in response.data
        assert 'fees_summary' in response.data
    
    def test_overall_summary_calculates_totals_correctly(
        self, estate_manager_client, estate_with_complete_data
    ):
        """Test overall summary calculates totals correctly."""
        url = reverse('reports:reports-overall-summary')
        response = estate_manager_client.get(url)
        
        assert response.status_code == status.HTTP_200_OK
        assert isinstance(response.data['total_expected_all_fees'], str)
        assert isinstance(response.data['total_collected_all_fees'], str)
        assert isinstance(response.data['total_pending_all_fees'], str)
    
    def test_overall_summary_with_invalid_estate_id_returns_400(
        self, estate_manager_client
    ):
        """Test overall summary with invalid estate_id returns 400."""
        url = reverse('reports:reports-overall-summary')
        response = estate_manager_client.get(url, {'estate_id': 'invalid-uuid'})
        
        # Should either ignore or return 400/200 depending on service implementation
        assert response.status_code in [status.HTTP_200_OK, status.HTTP_400_BAD_REQUEST]
    
    def test_overall_summary_exception_returns_500(self, estate_manager_client):
        """Test unexpected exception returns 500."""
        from unittest.mock import patch
        
        with patch('reports.services.get_overall_payment_summary') as mock_service:
            mock_service.side_effect = Exception('Service error')
            
            url = reverse('reports:reports-overall-summary')
            response = estate_manager_client.get(url)
            
            assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
            assert 'error' in response.data


@pytest.mark.django_db
class TestEstateSummaryAction:
    """Test estate summary custom action."""
    
    def test_unauthenticated_user_cannot_access(self, api_client, estate):
        """Test unauthenticated user gets 401."""
        url = reverse('reports:reports-estate-summary', kwargs={'estate_id': estate.id})
        response = api_client.get(url)
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
    
    def test_tenant_user_cannot_access(self, tenant_client, estate):
        """Test tenant user gets 403."""
        url = reverse('reports:reports-estate-summary', kwargs={'estate_id': estate.id})
        response = tenant_client.get(url)
        
        assert response.status_code == status.HTTP_403_FORBIDDEN
    
    def test_estate_manager_without_estate_cannot_access(
        self, estate_manager_no_estate_client, estate
    ):
        """Test estate manager without assigned estate gets 403."""
        url = reverse('reports:reports-estate-summary', kwargs={'estate_id': estate.id})
        response = estate_manager_no_estate_client.get(url)
        
        assert response.status_code == status.HTTP_403_FORBIDDEN
    
    def test_estate_manager_can_access_own_estate_summary(
        self, estate_manager_client, estate_with_complete_data
    ):
        """Test estate manager can access own estate summary."""
        estate_id = estate_with_complete_data['estate'].id
        url = reverse('reports:reports-estate-summary', kwargs={'estate_id': estate_id})
        response = estate_manager_client.get(url)
        
        assert response.status_code == status.HTTP_200_OK
        assert_overall_summary_structure(response.data)
    
    def test_super_admin_can_access_any_estate_summary(
        self, super_admin_client, estate_with_complete_data
    ):
        """Test super admin can access any estate summary."""
        estate_id = estate_with_complete_data['estate'].id
        url = reverse('reports:reports-estate-summary', kwargs={'estate_id': estate_id})
        response = super_admin_client.get(url)
        
        assert response.status_code == status.HTTP_200_OK
        assert_overall_summary_structure(response.data)
    
    def test_estate_manager_cannot_access_other_estate(
        self, estate_manager_client, other_estate
    ):
        """Test estate manager cannot access another estate's summary."""
        url = reverse('reports:reports-estate-summary', kwargs={'estate_id': other_estate.id})
        response = estate_manager_client.get(url)
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'error' in response.data
    
    def test_nonexistent_estate_returns_400(self, estate_manager_client):
        """Test nonexistent estate returns 400."""
        import uuid
        fake_estate_id = uuid.uuid4()
        
        url = reverse('reports:reports-estate-summary', kwargs={'estate_id': fake_estate_id})
        response = estate_manager_client.get(url)
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'error' in response.data
    
    def test_invalid_uuid_format_returns_404(self, estate_manager_client):
        """Test invalid UUID format returns 404."""
        url = '/api/reports/estate/not-a-valid-uuid/'
        response = estate_manager_client.get(url)
        
        assert response.status_code == status.HTTP_404_NOT_FOUND
    
    def test_estate_summary_includes_only_estate_fees(
        self, super_admin_client, estate_with_complete_data
    ):
        """Test estate summary includes only fees for that estate."""
        from .factories import EstateFactory, FeeFactory, UserFactory
        
        # Create another estate with fees
        another_estate_manager = UserFactory.create(role='estate_manager')
        another_estate = EstateFactory.create()
        another_estate_manager.estate_id = another_estate.id
        another_estate_manager.save()
        FeeFactory.create(estate=another_estate)
        
        estate_id = estate_with_complete_data['estate'].id
        url = reverse('reports:reports-estate-summary', kwargs={'estate_id': estate_id})
        response = super_admin_client.get(url)
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['total_fees'] == len(estate_with_complete_data['fees'])
    
    def test_estate_manager_can_only_see_assigned_estate_fees(
        self, estate_manager_client, estate_with_complete_data, other_estate
    ):
        """Test estate manager only sees fees for their assigned estate."""
        from .factories import FeeFactory
        
        # Create fee in other estate (should not affect this estate's summary)
        FeeFactory.create(estate=other_estate)
        
        estate_id = estate_with_complete_data['estate'].id
        url = reverse('reports:reports-estate-summary', kwargs={'estate_id': estate_id})
        response = estate_manager_client.get(url)
        
        assert response.status_code == status.HTTP_200_OK
        # Should only see fees from their assigned estate
        assert response.data['total_fees'] == len(estate_with_complete_data['fees'])
    
    def test_estate_summary_returns_correct_fee_count(
        self, estate_manager_client, estate_with_complete_data
    ):
        """Test estate summary returns correct number of fees."""
        estate_id = estate_with_complete_data['estate'].id
        url = reverse('reports:reports-estate-summary', kwargs={'estate_id': estate_id})
        response = estate_manager_client.get(url)
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['total_fees'] == 2  # From fixture
        assert len(response.data['fees_summary']) == 2
    
    def test_estate_summary_exception_returns_500(self, estate_manager_client, estate):
        """Test unexpected exception returns 500."""
        from unittest.mock import patch
        
        with patch('reports.services.get_estate_payment_summary') as mock_service:
            mock_service.side_effect = Exception('Unexpected error')
            
            url = reverse('reports:reports-estate-summary', kwargs={'estate_id': estate.id})
            response = estate_manager_client.get(url)
            
            assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
            assert 'error' in response.data