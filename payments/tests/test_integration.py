# tests/test_integration.py

"""
Integration tests for payments app.

Tests multi-endpoint workflows and end-to-end scenarios.

Coverage:
- Complete payment workflows
- Multi-step operations
- Cross-endpoint interactions
- Real-world user scenarios
"""

import pytest
from decimal import Decimal
from datetime import timedelta
from django.urls import reverse
from django.utils import timezone
from payments.models import Fee, FeeAssignment, Payment, Receipt


@pytest.mark.django_db
class TestCompletePaymentWorkflow:
    """Test complete fee creation to receipt generation workflow."""
    
    def test_full_payment_lifecycle(
        self, authenticated_client, estate, units, user
    ):
        """
        Test complete workflow:
        1. Create fee
        2. Verify assignments created
        3. Record payment
        4. Verify receipt generated
        5. Verify assignment status updated
        """
        # Step 1: Create fee assigned to all units
        fee_url = reverse("fee-list")
        fee_data = {
            "name": "Monthly Maintenance Fee",
            "description": "Regular maintenance charge",
            "amount": "5000.00",
            "due_date": (timezone.now() + timedelta(days=30)).date().isoformat(),
            "estate": str(estate.id),
            "assign_to_all_units": True,
        }
        
        fee_response = authenticated_client.post(fee_url, fee_data, format="json")
        assert fee_response.status_code == 201
        fee_id = fee_response.data["id"]
        
        # Step 2: Verify fee assignments were created for all units
        fee = Fee.objects.get(id=fee_id)
        assert fee.fee_assignments.count() == len(units)
        assert fee.fee_assignments.filter(status='unpaid').count() == len(units)
        
        # Step 3: Get first assignment and record payment
        assignment = fee.fee_assignments.first()
        payment_url = reverse("payment-list")
        payment_data = {
            "fee_assignment": str(assignment.id),
            "amount": "5000.00",
            "payment_method": "bank_transfer",
            "reference_number": "TXN123456",
            "notes": "Payment via online banking",
        }
        
        payment_response = authenticated_client.post(
            payment_url, payment_data, format="json"
        )
        assert payment_response.status_code == 201
        payment_id = payment_response.data["id"]
        
        # Step 4: Verify receipt was auto-generated
        payment = Payment.objects.get(id=payment_id)
        assert hasattr(payment, 'receipt')
        receipt = payment.receipt
        assert receipt.receipt_number.startswith("RCP-")
        assert receipt.amount == Decimal("5000.00")
        assert receipt.estate_name == estate.name
        
        # Step 5: Verify assignment status was updated to paid
        assignment.refresh_from_db()
        assert assignment.status == 'paid'
        
        # Step 6: Verify fee payment summary
        summary_url = reverse("fee-payment-summary", args=[fee_id])
        summary_response = authenticated_client.get(summary_url)
        assert summary_response.status_code == 200
        assert summary_response.data["total_assigned_units"] == len(units)
        assert summary_response.data["total_paid"] == 1
        assert summary_response.data["total_unpaid"] == len(units) - 1
    
    def test_multiple_payments_workflow(
        self, authenticated_client, fee_with_assignments, user
    ):
        """Test paying multiple fee assignments sequentially."""
        fee = fee_with_assignments
        assignments = list(fee.fee_assignments.all()[:3])
        
        payment_url = reverse("payment-list")
        payment_ids = []
        
        # Record payments for 3 assignments
        for i, assignment in enumerate(assignments):
            payment_data = {
                "fee_assignment": str(assignment.id),
                "amount": str(assignment.fee.amount),
                "payment_method": "cash" if i % 2 == 0 else "bank_transfer",
                "reference_number": f"REF-{i+1}",
            }
            
            response = authenticated_client.post(
                payment_url, payment_data, format="json"
            )
            assert response.status_code == 201
            payment_ids.append(response.data["id"])
        
        # Verify all payments were created
        assert Payment.objects.filter(id__in=payment_ids).count() == 3
        
        # Verify all receipts were generated
        receipts = Receipt.objects.filter(payment_id__in=payment_ids)
        assert receipts.count() == 3
        
        # Verify all receipt numbers are unique
        receipt_numbers = list(receipts.values_list('receipt_number', flat=True))
        assert len(set(receipt_numbers)) == 3
        
        # Verify fee payment summary
        fee.refresh_from_db()
        assert fee.fee_assignments.filter(status='paid').count() == 3
        assert fee.fee_assignments.filter(status='unpaid').count() == 2
    
    def test_create_fee_assign_additional_units_then_pay(
        self, authenticated_client, estate, units, user
    ):
        """
        Test workflow:
        1. Create fee for 2 units
        2. Assign to 2 more units
        3. Pay all 4 assignments
        """
        # Step 1: Create fee for first 2 units
        fee_url = reverse("fee-list")
        initial_unit_ids = [str(unit.id) for unit in units[:2]]
        fee_data = {
            "name": "Special Assessment",
            "amount": "10000.00",
            "due_date": (timezone.now() + timedelta(days=60)).date().isoformat(),
            "estate": str(estate.id),
            "unit_ids": initial_unit_ids,
        }
        
        response = authenticated_client.post(fee_url, fee_data, format="json")
        assert response.status_code == 201
        fee_id = response.data["id"]
        
        fee = Fee.objects.get(id=fee_id)
        assert fee.fee_assignments.count() == 2
        
        # Step 2: Assign to 2 more units
        assign_url = reverse("fee-assign-to-units", args=[fee_id])
        additional_unit_ids = [str(unit.id) for unit in units[2:4]]
        assign_data = {"unit_ids": additional_unit_ids}
        
        response = authenticated_client.post(assign_url, assign_data, format="json")
        assert response.status_code == 201
        
        fee.refresh_from_db()
        assert fee.fee_assignments.count() == 4
        
        # Step 3: Pay all 4 assignments
        payment_url = reverse("payment-list")
        for assignment in fee.fee_assignments.all():
            payment_data = {
                "fee_assignment": str(assignment.id),
                "amount": str(fee.amount),
                "payment_method": "bank_transfer",
            }
            response = authenticated_client.post(
                payment_url, payment_data, format="json"
            )
            assert response.status_code == 201
        
        # Verify all are paid
        fee.refresh_from_db()
        assert fee.fee_assignments.filter(status='paid').count() == 4
        assert fee.fee_assignments.filter(status='unpaid').count() == 0


@pytest.mark.django_db
class TestMultiEstateScenarios:
    """Test scenarios involving multiple estates."""
    
    def test_fees_isolated_by_estate(
        self, authenticated_client, estate, other_estate, units, other_units, user
    ):
        """Test that fees are properly isolated by estate."""
        # Create fee for estate 1
        fee_url = reverse("fee-list")
        fee1_data = {
            "name": "Estate 1 Fee",
            "amount": "3000.00",
            "due_date": (timezone.now() + timedelta(days=30)).date().isoformat(),
            "estate": str(estate.id),
            "assign_to_all_units": True,
        }
        
        response1 = authenticated_client.post(fee_url, fee1_data, format="json")
        assert response1.status_code == 201
        fee1_id = response1.data["id"]
        
        # Create fee for estate 2
        fee2_data = {
            "name": "Estate 2 Fee",
            "amount": "4000.00",
            "due_date": (timezone.now() + timedelta(days=30)).date().isoformat(),
            "estate": str(other_estate.id),
            "assign_to_all_units": True,
        }
        
        response2 = authenticated_client.post(fee_url, fee2_data, format="json")
        assert response2.status_code == 201
        fee2_id = response2.data["id"]
        
        # Verify assignments are isolated
        fee1 = Fee.objects.get(id=fee1_id)
        fee2 = Fee.objects.get(id=fee2_id)
        
        assert fee1.fee_assignments.count() == len(units)
        assert fee2.fee_assignments.count() == len(other_units)
        
        # Verify no cross-estate assignments
        fee1_unit_ids = set(
            fee1.fee_assignments.values_list('unit_id', flat=True)
        )
        fee2_unit_ids = set(
            fee2.fee_assignments.values_list('unit_id', flat=True)
        )
        
        assert len(fee1_unit_ids.intersection(fee2_unit_ids)) == 0


@pytest.mark.django_db
class TestReceiptWorkflows:
    """Test receipt-related workflows."""
    
    def test_receipt_generation_and_retrieval(
        self, authenticated_client, fee_assignment, user
    ):
        """Test receipt is generated and can be retrieved."""
        # Record payment
        payment_url = reverse("payment-list")
        payment_data = {
            "fee_assignment": str(fee_assignment.id),
            "amount": str(fee_assignment.fee.amount),
            "payment_method": "cash",
        }
        
        payment_response = authenticated_client.post(
            payment_url, payment_data, format="json"
        )
        assert payment_response.status_code == 201
        
        # Get receipt via payment
        payment = Payment.objects.get(id=payment_response.data["id"])
        receipt = payment.receipt
        
        # Retrieve receipt via API
        receipt_detail_url = reverse("receipt-detail", args=[receipt.id])
        receipt_response = authenticated_client.get(receipt_detail_url)
        
        assert receipt_response.status_code == 200
        assert receipt_response.data["receipt_number"] == receipt.receipt_number
        assert receipt_response.data["amount"] == str(receipt.amount)
        
        # Test receipt download endpoint
        download_url = reverse("receipt-download", args=[receipt.id])
        download_response = authenticated_client.get(download_url)
        
        assert download_response.status_code == 200
        assert "receipt_number" in download_response.data
    
    def test_list_all_receipts_for_estate(
        self, authenticated_client, fee_with_assignments, user
    ):
        """Test listing all receipts for an estate."""
        fee = fee_with_assignments
        payment_url = reverse("payment-list")
        
        # Create payments for all assignments
        for assignment in fee.fee_assignments.all():
            payment_data = {
                "fee_assignment": str(assignment.id),
                "amount": str(assignment.fee.amount),
                "payment_method": "bank_transfer",
            }
            authenticated_client.post(payment_url, payment_data, format="json")
        
        # List all receipts
        receipt_list_url = reverse("receipt-list")
        response = authenticated_client.get(receipt_list_url)
        
        assert response.status_code == 200
        assert response.data["count"] == 5
        
        # Verify all receipts have unique numbers
        receipt_numbers = [r["receipt_number"] for r in response.data["results"]]
        assert len(set(receipt_numbers)) == 5


@pytest.mark.django_db
class TestErrorRecoveryScenarios:
    """Test error handling and recovery scenarios."""
    
    def test_cannot_pay_same_assignment_twice(
        self, authenticated_client, fee_assignment, user
    ):
        """Test that attempting to pay twice is rejected."""
        payment_url = reverse("payment-list")
        payment_data = {
            "fee_assignment": str(fee_assignment.id),
            "amount": str(fee_assignment.fee.amount),
            "payment_method": "cash",
        }
        
        # First payment succeeds
        response1 = authenticated_client.post(
            payment_url, payment_data, format="json"
        )
        assert response1.status_code == 201
        
        # Second payment fails
        response2 = authenticated_client.post(
            payment_url, payment_data, format="json"
        )
        assert response2.status_code == 400
        assert "fee_assignment" in response2.data
    
    def test_update_fee_after_some_payments(
        self, authenticated_client, fee_with_assignments, user
    ):
        """Test updating fee after some payments have been made."""
        fee = fee_with_assignments
        
        # Pay first assignment
        assignment = fee.fee_assignments.first()
        payment_url = reverse("payment-list")
        payment_data = {
            "fee_assignment": str(assignment.id),
            "amount": str(assignment.fee.amount),
            "payment_method": "cash",
        }
        authenticated_client.post(payment_url, payment_data, format="json")
        
        # Update fee details (should not affect paid assignments)
        fee_url = reverse("fee-detail", args=[fee.id])
        update_data = {
            "name": "Updated Fee Name",
            "description": "Updated description",
        }
        
        response = authenticated_client.patch(fee_url, update_data, format="json")
        assert response.status_code == 200
        
        # Verify payment and receipt are unchanged
        payment = Payment.objects.get(fee_assignment=assignment)
        receipt = payment.receipt
        
        # Receipt should have old fee name (cached)
        assert receipt.fee_name == fee.name  # Old name before update


@pytest.mark.django_db
class TestBulkOperations:
    """Test bulk operation scenarios."""
    
    def test_create_fee_for_large_estate(
        self, authenticated_client, estate, user
    ):
        """Test creating fee for estate with many units."""
        from .factories import UnitFactory
        
        # Create 50 units
        units = [UnitFactory.create(estate=estate) for _ in range(50)]
        
        # Create fee assigned to all units
        fee_url = reverse("fee-list")
        fee_data = {
            "name": "Bulk Fee",
            "amount": "1000.00",
            "due_date": (timezone.now() + timedelta(days=30)).date().isoformat(),
            "estate": str(estate.id),
            "assign_to_all_units": True,
        }
        
        response = authenticated_client.post(fee_url, fee_data, format="json")
        assert response.status_code == 201
        
        fee = Fee.objects.get(id=response.data["id"])
        assert fee.fee_assignments.count() == 50
    
    def test_pay_multiple_fees_for_single_unit(
        self, authenticated_client, estate, units, user
    ):
        """Test paying multiple different fees for same unit."""
        from .factories import FeeFactory, FeeAssignmentFactory
        
        unit = units[0]
        
        # Create 3 different fees, all assigned to same unit
        fees = []
        for i in range(3):
            fee = FeeFactory.create(
                estate=estate,
                created_by=user,
                name=f"Fee {i+1}",
                amount=Decimal("1000.00") * (i + 1)
            )
            FeeAssignmentFactory.create(fee=fee, unit=unit)
            fees.append(fee)
        
        # Pay all 3 fees
        payment_url = reverse("payment-list")
        for fee in fees:
            assignment = fee.fee_assignments.get(unit=unit)
            payment_data = {
                "fee_assignment": str(assignment.id),
                "amount": str(fee.amount),
                "payment_method": "bank_transfer",
            }
            response = authenticated_client.post(
                payment_url, payment_data, format="json"
            )
            assert response.status_code == 201
        
        # Verify all payments and receipts created
        assert Payment.objects.filter(
            fee_assignment__unit=unit
        ).count() == 3
        
        assert Receipt.objects.filter(
            payment__fee_assignment__unit=unit
        ).count() == 3


@pytest.mark.django_db
class TestRealisticUserScenarios:
    """Test realistic end-to-end user scenarios."""
    
    def test_estate_manager_monthly_workflow(
        self, authenticated_client, estate, units, user
    ):
        """
        Simulate estate manager's monthly workflow:
        1. Create monthly fee
        2. Check payment status throughout month
        3. Record payments as they come in
        4. Generate final report
        """
        # Week 1: Create monthly fee
        fee_url = reverse("fee-list")
        fee_data = {
            "name": "January 2026 Maintenance",
            "amount": "5000.00",
            "due_date": (timezone.now() + timedelta(days=30)).date().isoformat(),
            "estate": str(estate.id),
            "assign_to_all_units": True,
        }
        
        fee_response = authenticated_client.post(fee_url, fee_data, format="json")
        assert fee_response.status_code == 201
        fee_id = fee_response.data["id"]
        
        # Week 2: Check initial status (all unpaid)
        summary_url = reverse("fee-payment-summary", args=[fee_id])
        response = authenticated_client.get(summary_url)
        assert response.data["total_unpaid"] == 5
        assert response.data["payment_completion_rate"] == 0
        
        # Week 3: Record 3 payments
        payment_url = reverse("payment-list")
        fee = Fee.objects.get(id=fee_id)
        for assignment in list(fee.fee_assignments.all())[:3]:
            payment_data = {
                "fee_assignment": str(assignment.id),
                "amount": str(fee.amount),
                "payment_method": "bank_transfer",
            }
            authenticated_client.post(payment_url, payment_data, format="json")
        
        # Week 4: Check progress
        response = authenticated_client.get(summary_url)
        assert response.data["total_paid"] == 3
        assert response.data["total_unpaid"] == 2
        assert response.data["payment_completion_rate"] == 60.0
        
        # Week 5: Record remaining payments
        for assignment in fee.fee_assignments.filter(status='unpaid'):
            payment_data = {
                "fee_assignment": str(assignment.id),
                "amount": str(fee.amount),
                "payment_method": "cash",
            }
            authenticated_client.post(payment_url, payment_data, format="json")
        
        # Final check: All paid
        response = authenticated_client.get(summary_url)
        assert response.data["payment_completion_rate"] == 100.0
        
        # List all receipts
        receipt_url = reverse("receipt-list")
        receipt_response = authenticated_client.get(receipt_url)
        assert receipt_response.data["count"] == 5