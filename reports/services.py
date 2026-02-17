# reports/services.py
"""
Business logic for reports app.

All report generation and computation happens here.
"""

import logging
from decimal import Decimal
from typing import Dict, Optional, Any

from django.db.models import Sum
from django.contrib.auth import get_user_model
from datetime import date
from payments.models import Fee, FeeAssignment, Payment
from estates.models import Estate

User = get_user_model()
logger = logging.getLogger(__name__)


def _get_user_estate(user):
    """
    Safely retrieve the estate for an estate manager via reverse OneToOne.

    Returns the Estate instance, or raises ValueError if none is assigned.
    This replaces all uses of user.estate_id, which no longer exists after
    the relationship was moved to Estate.manager (OneToOneField).
    """
    try:
        return user.estate
    except Estate.DoesNotExist:
        raise ValueError("Estate manager must have an assigned estate")


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
    if user.role == User.Role.ESTATE_MANAGER:
        estate = _get_user_estate(user)
        if str(fee.estate_id) != str(estate.id):
            raise ValueError("You don't have permission to view this fee")

    # ------------------------------------------------------------------
    # 3. Total liable units (units with FeeAssignments for this fee)
    # ------------------------------------------------------------------
    all_assignments = FeeAssignment.objects.filter(fee=fee)
    total_units = all_assignments.count()

    # ------------------------------------------------------------------
    # 4. Paid units (via FeeAssignment)
    # ------------------------------------------------------------------
    paid_assignments = all_assignments.filter(
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
    # 6. Unpaid units detail
    # NOTE: field names use 'owner_*' to match UnpaidUnitSerializer which
    # expects owner_id / owner_name / owner_email (not tenant_*)
    # ------------------------------------------------------------------
    unpaid_assignments = all_assignments.exclude(
        status=FeeAssignment.PaymentStatus.PAID
    ).select_related('unit', 'unit__owner', 'unit__estate')

    today = date.today()
    unpaid_units = []

    for assignment in unpaid_assignments:
        unit = assignment.unit
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
    # 7. Final response
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

    For SUPER_ADMIN: queries all estates, or filters by estate_id if provided.
    For ESTATE_MANAGER: always scoped to their own estate. The estate_id query
    param is ignored — context is derived from the authenticated user only.
    This prevents a manager from requesting another estate's data via URL params.
    """
    logger.info(
        f"Generating overall payment summary for user {user.id}, "
        f"estate_id={estate_id}"
    )

    # ------------------------------------------------------------------
    # Determine estate scope
    # ------------------------------------------------------------------
    if user.role == User.Role.SUPER_ADMIN:
        if estate_id:
            estates = Estate.objects.filter(id=estate_id)
            if not estates.exists():
                raise ValueError("Estate not found")
        else:
            estates = Estate.objects.all()
    else:
        # ESTATE_MANAGER — scope is always derived from user, never from params
        estate = _get_user_estate(user)
        estates = Estate.objects.filter(id=estate.id)

    # ------------------------------------------------------------------
    # Aggregate across fees
    # ------------------------------------------------------------------
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
            'fees_summary': [],
        }

    fees_summary = []
    total_expected_all = Decimal('0.00')
    total_collected_all = Decimal('0.00')

    for fee in fees:
        total_assignments = FeeAssignment.objects.filter(fee=fee).count()
        expected = fee.amount * total_assignments

        collected = (
            Payment.objects.filter(
                fee_assignment__fee=fee,
                fee_assignment__status=FeeAssignment.PaymentStatus.PAID
            ).aggregate(total=Sum('amount'))['total']
            or Decimal('0.00')
        )

        paid_count = FeeAssignment.objects.filter(
            fee=fee,
            status=FeeAssignment.PaymentStatus.PAID
        ).count()

        pending = expected - collected

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
            'total_units': total_assignments,
            'paid_units': paid_count,
            'unpaid_units_count': total_assignments - paid_count,
        })

        total_expected_all += expected
        total_collected_all += collected

    total_pending_all = total_expected_all - total_collected_all

    overall_rate = Decimal('0.00')
    if total_expected_all > 0:
        overall_rate = (
            total_collected_all / total_expected_all * 100
        ).quantize(Decimal('0.01'))

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
        'fees_summary': fees_summary,
    }


def get_estate_payment_summary(
    *,
    user,
    estate_id: str
) -> Dict[str, Any]:
    """
    Generate payment summary for a specific estate.

    For ESTATE_MANAGER: estate_id in the URL must match their assigned estate.
    Context is re-verified via _get_user_estate rather than trusting user.estate_id.
    """
    logger.info(
        f"Generating estate payment summary for user {user.id}, "
        f"estate_id={estate_id}"
    )

    # Verify estate exists
    try:
        Estate.objects.get(id=estate_id)
    except Estate.DoesNotExist:
        raise ValueError("Estate not found")

    # Check permissions for estate managers
    if user.role == User.Role.ESTATE_MANAGER:
        estate = _get_user_estate(user)
        if str(estate.id) != str(estate_id):
            raise ValueError("Cannot access other estate's data")

    # Delegate to overall summary with the estate filter applied
    return get_overall_payment_summary(
        user=user,
        estate_id=estate_id,
    )