# reports/services.py
"""
Business logic for reports app.

All report generation and computation happens here.
"""

import logging
from decimal import Decimal
from typing import Dict, Optional, Any

from django.db.models import Sum, Q
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import date
from payments.models import Fee, FeeAssignment, Payment
from units.models import Unit
from estates.models import Estate

User = get_user_model()
logger = logging.getLogger(__name__)

# reports/services.py
def get_fee_payment_status(
    *,
    user,
    fee_id: str
) -> Dict[str, Any]:
    """
    Generate payment status report for a specific fee.
    """


    logger.info(
        f"Generating fee payment status for user {user.id}, fee_id={fee_id}"
    )

    # ------------------------------------------------------------------
    # 1. Fetch fee
    # ------------------------------------------------------------------
    try:
        fee = Fee.objects.select_related('estate').get(id=fee_id)
    except Fee.DoesNotExist:
        raise ValueError("Fee not found")

    # ------------------------------------------------------------------
    # 2. Permission checks
    # ------------------------------------------------------------------
    if user.role == 'estate_manager':
        if not user.estate_id:
            raise ValueError("Estate manager must have an assigned estate")

        if str(fee.estate_id) != str(user.estate_id):
            raise ValueError("You don't have permission to view this fee")

    # ------------------------------------------------------------------
    # 3. Total liable units (OCCUPIED units only)
    # ------------------------------------------------------------------
    total_units = Unit.objects.filter(
        estate=fee.estate,
        is_occupied=True
    ).count()

    # ------------------------------------------------------------------
    # 4. Paid units (via FeeAssignment)
    # ------------------------------------------------------------------
    paid_assignments = FeeAssignment.objects.filter(
        fee=fee,
        status=FeeAssignment.PaymentStatus.PAID
    )

    paid_units = paid_assignments.count()
    unpaid_units_count = total_units - paid_units

    # ------------------------------------------------------------------
    # 5. Financial calculations
    # ------------------------------------------------------------------
    total_expected = fee.amount * total_units

    total_collected = (
        Payment.objects.filter(
            fee_assignment__in=paid_assignments
        ).aggregate(total=Sum('amount'))['total']
        or Decimal('0.00')
    )

    total_pending = total_expected - total_collected

    payment_rate = Decimal('0.00')
    if total_units > 0:
        payment_rate = (
            Decimal(paid_units) / Decimal(total_units) * 100
        ).quantize(Decimal('0.01'))

    # ------------------------------------------------------------------
    # 6. Unpaid units (KEY FIX)
    # ------------------------------------------------------------------
    paid_unit_ids = paid_assignments.values_list('unit_id', flat=True)

    unpaid_units_qs = Unit.objects.filter(
        estate=fee.estate,
        is_occupied=True
    ).exclude(id__in=paid_unit_ids)

    today = date.today()
    unpaid_units = []

    for unit in unpaid_units_qs:
        days_overdue = 0
        if fee.due_date and today > fee.due_date:
            days_overdue = (today - fee.due_date).days

        unpaid_units.append({
            'unit_id': str(unit.id),
            'unit_name': unit.identifier,
            'owner_id': str(unit.owner.id) if unit.owner else None,
            'owner_name': unit.owner.get_full_name() if unit.owner else None,
            'owner_email': unit.owner.email if unit.owner else None,
            'estate_id': str(unit.estate.id),
            'estate_name': unit.estate.name,
            'amount_due': str(fee.amount),
            'due_date': fee.due_date,
            'days_overdue': days_overdue,
        })

    # ------------------------------------------------------------------
    # 7. Final response (serializer-aligned)
    # ------------------------------------------------------------------
    return {
        'fee_id': str(fee.id),
        'fee_name': fee.name,
        'fee_type': fee.fee_type if hasattr(fee, 'fee_type') else 'standard',
        'total_expected': str(total_expected),
        'total_collected': str(total_collected),
        'total_pending': str(total_pending),
        'payment_rate': str(payment_rate),
        'total_units': total_units,
        'paid_units': paid_units,
        'unpaid_units_count': unpaid_units_count,
        'unpaid_units': unpaid_units,
    }


def get_overall_payment_summary(
    *,
    user,
    estate_id: Optional[str] = None
) -> Dict[str, Any]:
    """
    Generate overall payment summary across all fees.
    
    Args:
        user: User instance requesting the report
        estate_id: Optional UUID to filter by specific estate
        
    Returns:
        Dictionary containing summary data
    """

    
    logger.info(
        f"Generating overall payment summary for user {user.id}, "
        f"estate_id={estate_id}"
    )
    
    # Determine which estates to query based on user role
    if user.role == 'super_admin':
        if estate_id:
            estates = Estate.objects.filter(id=estate_id)
            if not estates.exists():
                raise ValueError("Estate not found")
        else:
            estates = Estate.objects.all()
    else:  # estate_manager
        # Must have an estate assigned
        if not user.estate_id:
            raise ValueError("Estate manager must have an assigned estate")
        
        # Can only access their own estate
        if estate_id:
            if str(estate_id) != str(user.estate_id):
                raise ValueError("Cannot access other estate's data")
            estates = Estate.objects.filter(id=user.estate_id)
        else:
            estates = Estate.objects.filter(id=user.estate_id)
    
    # Get all fees for these estates
    fees = Fee.objects.filter(estate__in=estates)
    total_fees = fees.count()
    
    if total_fees == 0:
        logger.info("No fees found for the given criteria")
        return {
            'total_fees': 0,
            'total_expected_all_fees': '0.00',
            'total_collected_all_fees': '0.00',
            'total_pending_all_fees': '0.00',
            'overall_payment_rate': '0.00',
            'fees_summary': []
        }
    
    fees_summary = []
    total_expected_all = Decimal('0.00')
    total_collected_all = Decimal('0.00')
    
    for fee in fees:
        # Get occupied units count for this estate
        occupied_units_count = Unit.objects.filter(
            estate=fee.estate,
            is_occupied=True
        ).count()
        
        # Expected amount
        expected = fee.amount * occupied_units_count
        
        # FIXED: Query through fee_assignment instead of direct fee relationship
        # Collected amount from payments for this fee
        collected = Payment.objects.filter(
            fee_assignment__fee=fee,  # Changed from fee=fee
            fee_assignment__status=FeeAssignment.PaymentStatus.PAID
        ).aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
        
        # Count paid units for this fee
        paid_count = FeeAssignment.objects.filter(
            fee=fee,
            status=FeeAssignment.PaymentStatus.PAID
        ).count()
        
        pending = expected - collected
        
        # Calculate payment rate
        rate = Decimal('0.00')
        if expected > 0:
            rate = (collected / expected * 100).quantize(Decimal('0.01'))
        
        fees_summary.append({
            'fee_id': str(fee.id),
            'fee_name': fee.name,
            'fee_type': fee.fee_type if hasattr(fee, 'fee_type') else 'standard',
            'total_expected': str(expected),
            'total_collected': str(collected),
            'total_pending': str(pending),
            'payment_rate': str(rate),
            'total_units': occupied_units_count,
            'paid_units': paid_count,
            'unpaid_units_count': occupied_units_count - paid_count
        })
        
        total_expected_all += expected
        total_collected_all += collected
    
    total_pending_all = total_expected_all - total_collected_all
    
    # Calculate overall payment rate
    overall_rate = Decimal('0.00')
    if total_expected_all > 0:
        overall_rate = (total_collected_all / total_expected_all * 100).quantize(Decimal('0.01'))
    
    logger.info(
        f"Overall summary: {total_fees} fees, "
        f"{total_collected_all}/{total_expected_all} collected ({overall_rate}%)"
    )
    
    return {
        'total_fees': total_fees,
        'total_expected_all_fees': str(total_expected_all),
        'total_collected_all_fees': str(total_collected_all),
        'total_pending_all_fees': str(total_pending_all),
        'overall_payment_rate': str(overall_rate),
        'fees_summary': fees_summary
    }


def get_estate_payment_summary(
    *,
    user,
    estate_id: str
) -> Dict[str, Any]:
    """
    Generate payment summary for a specific estate.
    
    Args:
        user: User instance requesting the report
        estate_id: UUID of the estate
        
    Returns:
        Dictionary containing estate summary data
    """
    from estates.models import Estate
    
    logger.info(
        f"Generating estate payment summary for user {user.id}, "
        f"estate_id={estate_id}"
    )
    
    # Verify estate exists
    try:
        estate = Estate.objects.get(id=estate_id)
    except Estate.DoesNotExist:
        raise ValueError("Estate not found")
    
    # Check permissions
    if user.role == 'estate_manager':
        if str(user.estate_id) != str(estate_id):
            raise ValueError("Cannot access other estate's data")
    
    # Use the overall summary function with estate filter
    return get_overall_payment_summary(
        user=user,
        estate_id=estate_id
    )