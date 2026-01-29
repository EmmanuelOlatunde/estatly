# reports/tests/test_integration.py
"""
Integration tests for reports app workflows.

Coverage:
- Multi-step workflows
- Cross-app interactions
- End-to-end scenarios
"""

import pytest
from django.urls import reverse
from rest_framework import status
from decimal import Decimal
import factory
from .factories import PaymentFactory, FeeAssignmentFactory
from payments.models import FeeAssignment


@pytest.mark.django_db
class TestReportingWorkflows:
    """Test complete reporting workflows."""
    
    def test_complete_fee_lifecycle_reporting(self, estate_manager_client, estate):
        """Test reporting throughout a fee's lifecycle."""
        from .factories import FeeFactory, UnitFactory, PaymentFactory
        
        # Create fee
        fee = FeeFactory.create(estate=estate, amount=Decimal('1000.00'))
        units = UnitFactory.create_batch(5, estate=estate, is_occupied=True)
        
        # Initial report - no payments
        url = reverse('reports:reports-fee-payment-status', kwargs={'fee_id': fee.id})
        response = estate_manager_client.get(url)
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['paid_units'] == 0
        assert response.data['unpaid_units_count'] == 5
        assert response.data['payment_rate'] == '0.00'
        
        # Add some payments
        for i in range(3):
            assignment = FeeAssignmentFactory.create(
                fee=fee,
                unit=units[i],
                status=FeeAssignment.PaymentStatus.PAID
            )
            PaymentFactory.create(
                fee_assignment=assignment,
                amount=fee.amount
            )

        
        # Report after partial payments
        response = estate_manager_client.get(url)
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['paid_units'] == 3
        assert response.data['unpaid_units_count'] == 2
        assert response.data['payment_rate'] == '60.00'
        
        # Complete all payments
        for i in range(3, 5):
            assignment = FeeAssignmentFactory.create(
                fee=fee,
                unit=units[i],
                status=FeeAssignment.PaymentStatus.PAID
            )
            PaymentFactory.create(
                fee_assignment=assignment,
                amount=fee.amount
            )

        
        # Final report - all paid
        response = estate_manager_client.get(url)
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['paid_units'] == 5
        assert response.data['unpaid_units_count'] == 0
        assert response.data['payment_rate'] == '100.00'
    
    def test_landlord_dashboard_workflow(self, estate_manager_client, estate_with_complete_data):
        """Test typical landlord dashboard workflow."""
        # Step 1: Get overall summary
        url = reverse('reports:reports-overall-summary')
        response = estate_manager_client.get(url)
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['total_fees'] > 0
        
        # Step 2: Drill down into specific estate
        estate_id = estate_with_complete_data['estate'].id
        url = reverse('reports:reports-estate-summary', kwargs={'estate_id': estate_id})
        response = estate_manager_client.get(url)
        
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data['fees_summary']) > 0
        
        # Step 3: Check specific fee details
        fee_id = estate_with_complete_data['fee1'].id
        url = reverse('reports:reports-fee-payment-status', kwargs={'fee_id': fee_id})
        response = estate_manager_client.get(url)
        
        assert response.status_code == status.HTTP_200_OK
        assert 'unpaid_units' in response.data
    
    def test_multiple_estates_reporting(self, super_admin_client):
        from .factories import EstateFactory, UnitFactory, FeeFactory, PaymentFactory

        estate1 = EstateFactory.create()
        estate2 = EstateFactory.create()

        units1 = UnitFactory.create_batch(3, estate=estate1, is_occupied=True)
        units2 = UnitFactory.create_batch(5, estate=estate2, is_occupied=True)

        fee1 = FeeFactory.create(estate=estate1, amount=Decimal('1000.00'))
        fee2 = FeeFactory.create(estate=estate2, amount=Decimal('500.00'))

        assignment = FeeAssignmentFactory.create(
            fee=fee1,
            unit=units1[0],
            status=FeeAssignment.PaymentStatus.PAID
        )
        PaymentFactory.create(fee_assignment=assignment, amount=fee1.amount)

        for unit in units2[:3]:
            assignment = FeeAssignmentFactory.create(
                fee=fee2,
                unit=unit,
                status=FeeAssignment.PaymentStatus.PAID
            )
            PaymentFactory.create(fee_assignment=assignment, amount=fee2.amount)

        url = reverse('reports:reports-overall-summary')
        response = super_admin_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert response.data['total_fees'] >= 2
