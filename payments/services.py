# payments/services.py

"""
Business logic for the payments app.

Contains all domain logic for creating fees, recording payments, and generating receipts.
"""

import uuid
from decimal import Decimal
from typing import List, Optional, TYPE_CHECKING
from datetime import datetime

from django.db import transaction
from django.utils import timezone
from django.contrib.auth import get_user_model
from rest_framework.exceptions import ValidationError

from .models import Fee, FeeAssignment, Payment, Receipt


if TYPE_CHECKING:
    from django.contrib.auth.models import AbstractBaseUser

User = get_user_model()


def create_fee(
    *,
    name: str,
    amount: Decimal,
    due_date: datetime,
    estate_id: uuid.UUID,
    created_by: "AbstractBaseUser",
    description: str = "",
    assign_to_all_units: bool = False,
    unit_ids: Optional[List[uuid.UUID]] = None
) -> Fee:
    """
    Create a new fee and assign it to units.
    
    Args:
        name: Fee name (e.g., "Security Levy 2025")
        amount: Fee amount
        due_date: Payment due date
        estate_id: UUID of the estate this fee belongs to
        created_by: User creating the fee
        description: Optional detailed description
        assign_to_all_units: If True, assign to all units in estate
        unit_ids: List of unit UUIDs to assign fee to (if not assigning to all)
    
    Returns:
        The created Fee instance with assignments
    
    Raises:
        ValidationError: If validation fails
        ValueError: If neither assign_to_all_units nor unit_ids is provided
    """
    from units.models import Unit
    from estates.models import Estate
    
    if not assign_to_all_units and not unit_ids:
        raise ValueError(
            "Must either set assign_to_all_units=True or provide unit_ids"
        )
    
    with transaction.atomic():
        estate = Estate.objects.get(id=estate_id)
        
        fee = Fee.objects.create(
            name=name,
            description=description,
            amount=amount,
            due_date=due_date,
            estate=estate,
            created_by=created_by
        )
        
        fee.full_clean()
        fee.save()
        
        if assign_to_all_units:
            units = Unit.objects.filter(estate=estate)
        else:
            units = Unit.objects.filter(id__in=unit_ids, estate=estate)
            
            requested_count = len(unit_ids) if unit_ids else 0
            found_count = units.count()
            if found_count != requested_count:
                raise ValidationError(
                    f"Some unit IDs are invalid or don't belong to this estate. "
                    f"Requested: {requested_count}, Found: {found_count}"
                )
        
        assignments = [
            FeeAssignment(fee=fee, unit=unit)
            for unit in units
        ]
        FeeAssignment.objects.bulk_create(assignments)
    
    return fee


def assign_fee_to_units(
    *,
    fee: Fee,
    unit_ids: List[uuid.UUID]
) -> List[FeeAssignment]:
    """
    Assign an existing fee to additional units.
    
    Args:
        fee: The Fee instance to assign
        unit_ids: List of unit UUIDs to assign the fee to
    
    Returns:
        List of created FeeAssignment instances
    
    Raises:
        ValidationError: If any unit doesn't belong to the fee's estate or already has this fee
    """
    from units.models import Unit
    
    with transaction.atomic():
        units = Unit.objects.filter(id__in=unit_ids, estate=fee.estate)
        
        if units.count() != len(unit_ids):
            raise ValidationError(
                "Some unit IDs are invalid or don't belong to this fee's estate"
            )
        
        existing_assignments = FeeAssignment.objects.filter(
            fee=fee,
            unit__in=units
        ).values_list('unit_id', flat=True)
        
        if existing_assignments:
            raise ValidationError(
                f"Fee is already assigned to {len(existing_assignments)} of these units"
            )
        
        assignments = [
            FeeAssignment(fee=fee, unit=unit)
            for unit in units
        ]
        created_assignments = FeeAssignment.objects.bulk_create(assignments)
    
    return created_assignments


def mark_fee_as_paid(
    *,
    fee_assignment: FeeAssignment,
    amount: Decimal,
    payment_method: str,
    recorded_by: "AbstractBaseUser",
    payment_date: Optional[datetime] = None,
    reference_number: str = "",
    notes: str = ""
) -> Payment:
    """
    Mark a fee assignment as paid by creating a payment record.
    """
    if fee_assignment.status == FeeAssignment.PaymentStatus.PAID:
        raise ValidationError("This fee has already been marked as paid")
    
    try:
        existing_payment = fee_assignment.payment
        raise ValidationError("A payment record already exists for this fee")
    except Payment.DoesNotExist:
        pass
    
    if amount != fee_assignment.fee.amount:
        raise ValidationError(
            f"Payment amount ({amount}) must match fee amount ({fee_assignment.fee.amount})"
        )
    
    # Rest of implementation...
    payment = Payment.objects.create(
        fee_assignment=fee_assignment,
        amount=amount,
        payment_method=payment_method,
        payment_date=payment_date or timezone.now(),
        reference_number=reference_number,
        notes=notes,
        recorded_by=recorded_by
    )
    
    fee_assignment.status = FeeAssignment.PaymentStatus.PAID
    fee_assignment.save()
    
    # Let the model auto-generate receipt_number
    Receipt.objects.create(
        payment=payment,
        # receipt_number will be auto-generated in save()
        estate_name=fee_assignment.fee.estate.name,
        unit_identifier=fee_assignment.unit.identifier,
        fee_name=fee_assignment.fee.name,
        amount=payment.amount,
        payment_date=payment.payment_date.date(),
        payment_method=payment.payment_method
    )
    
    return payment


def generate_receipt_for_payment(*, payment: Payment) -> Receipt:
    """
    Generate a receipt for a payment.
    
    Args:
        payment: The Payment instance to generate a receipt for
    
    Returns:
        The created Receipt instance
    
    Raises:
        ValidationError: If receipt already exists for this payment
    """
    # Use hasattr to safely check if the OneToOneField relation exists
    # This is cleaner than exception handling for control flow
    if hasattr(payment, 'receipt'):
        raise ValidationError("Receipt already exists for this payment")
    
    receipt_number = _generate_receipt_number()
    
    receipt = Receipt.objects.create(
        receipt_number=receipt_number,
        payment=payment,
        estate_name=payment.fee_assignment.fee.estate.name,
        unit_identifier=payment.fee_assignment.unit.identifier,
        fee_name=payment.fee_assignment.fee.name,
        amount=payment.amount,
        payment_date=payment.payment_date.date(),  
        payment_method=payment.get_payment_method_display()
    )
    
    return receipt
    
    
def _generate_receipt_number() -> str:
    """
    Generate a unique receipt number.
    
    Format: RCP-YYYYMMDD-XXXXXX where XXXXXX is a random hex string.
    
    Returns:
        Unique receipt number string
    """
    date_str = timezone.now().strftime('%Y%m%d')
    random_suffix = uuid.uuid4().hex[:6].upper()
    receipt_number = f"RCP-{date_str}-{random_suffix}"
    
    while Receipt.objects.filter(receipt_number=receipt_number).exists():
        random_suffix = uuid.uuid4().hex[:6].upper()
        receipt_number = f"RCP-{date_str}-{random_suffix}"
    
    return receipt_number


def get_fee_payment_summary(*, fee: Fee) -> dict:
    """
    Get payment summary statistics for a fee.
    
    Args:
        fee: The Fee instance to summarize
    
    Returns:
        Dictionary containing payment statistics
    """
    assignments = fee.fee_assignments.all()
    total_assigned = assignments.count()
    total_paid = assignments.filter(status=FeeAssignment.PaymentStatus.PAID).count()
    total_unpaid = assignments.filter(status=FeeAssignment.PaymentStatus.UNPAID).count()
    
    total_expected_revenue = fee.amount * total_assigned
    total_collected_revenue = fee.amount * total_paid
    total_outstanding_revenue = fee.amount * total_unpaid
    
    return {
        'total_assigned_units': total_assigned,
        'total_paid': total_paid,
        'total_unpaid': total_unpaid,
        'payment_completion_rate': (total_paid / total_assigned * 100) if total_assigned > 0 else 0,
        'total_expected_revenue': total_expected_revenue,
        'total_collected_revenue': total_collected_revenue,
        'total_outstanding_revenue': total_outstanding_revenue,
    }


def get_unit_payment_history(*, unit_id: uuid.UUID) -> List[dict]:
    """
    Get payment history for a specific unit.
    
    Args:
        unit_id: UUID of the unit
    
    Returns:
        List of payment records with fee and receipt information
    """
    assignments = FeeAssignment.objects.filter(
        unit_id=unit_id
    ).select_related(
        'fee',
        'fee__estate',
        'payment',
        'payment__receipt'
    ).order_by('-fee__due_date')
    
    history = []
    for assignment in assignments:
        record = {
            'fee_id': assignment.fee.id,
            'fee_name': assignment.fee.name,
            'amount': assignment.fee.amount,
            'due_date': assignment.fee.due_date,
            'status': assignment.status,
            'payment': None,
            'receipt': None,
        }
        
        try:
            payment = assignment.payment
            record['payment'] = {
                'id': payment.id,
                'payment_method': payment.payment_method,
                'payment_date': payment.payment_date,
                'reference_number': payment.reference_number,
            }
            
            try:
                receipt = payment.receipt
                record['receipt'] = {
                    'id': receipt.id,
                    'receipt_number': receipt.receipt_number,
                }
            except Receipt.DoesNotExist:
                pass
                
        except Payment.DoesNotExist:
            pass
        
        history.append(record)
    
    return history