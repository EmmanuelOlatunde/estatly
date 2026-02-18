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


# ── Add to reports/services.py ───────────────────────────────────────────────

def get_estate_audit_report(*, user, estate_id: str) -> dict:
    """
    Estate-wide full audit report.

    Returns one row per (unit, fee) assignment covering:
      - unit & owner details
      - fee details (name, type, amount, due date)
      - assignment status (paid / unpaid / partial / waived)
      - full payment transaction detail when paid
        (amount, date/time, method, reference, who recorded it)

    This is the transparency report — every unit's complete
    payment picture across all fees in one place.
    """
    from decimal import Decimal
    from datetime import date as date_type
    from payments.models import Fee, FeeAssignment, Payment

    logger.info(
        f"Generating estate audit report for user {user.id}, estate_id={estate_id}"
    )

    # ── 1. Permission check ────────────────────────────────────────────────
    try:
        estate = Estate.objects.get(id=estate_id)
    except Estate.DoesNotExist:
        raise ValueError("Estate not found")

    if user.role == User.Role.ESTATE_MANAGER:
        manager_estate = _get_user_estate(user)
        if str(manager_estate.id) != str(estate_id):
            raise ValueError("Cannot access another estate's data")

    # ── 2. Load all assignments for this estate ────────────────────────────
    assignments = (
        FeeAssignment.objects
        .filter(fee__estate=estate)
        .select_related(
            'fee',
            'unit',
            'unit__owner',
        )
        .order_by('unit__identifier', 'fee__name')
    )

    # ── 3. Load all payments keyed by assignment ───────────────────────────
    # One payment per assignment is the normal case; fetch them all up front.
    payments_by_assignment = {}
    payments_qs = (
        Payment.objects
        .filter(fee_assignment__fee__estate=estate)
        .select_related('fee_assignment', 'recorded_by')  # adjust if field differs
    )
    for p in payments_qs:
        # If multiple payments exist per assignment (partial), keep the latest.
        aid = p.fee_assignment_id
        if aid not in payments_by_assignment:
            payments_by_assignment[aid] = p
        else:
            existing = payments_by_assignment[aid]
            # Keep most recent
            if getattr(p, 'created_at', None) and getattr(existing, 'created_at', None):
                if p.created_at > existing.created_at:
                    payments_by_assignment[aid] = p

    # ── 4. Build rows ──────────────────────────────────────────────────────
    today = date_type.today()
    rows = []
    total_expected = Decimal('0.00')
    total_collected = Decimal('0.00')
    paid_count = 0
    unpaid_count = 0
    unit_ids = set()
    fee_ids = set()

    for assignment in assignments:
        fee  = assignment.fee
        unit = assignment.unit
        owner = unit.owner

        unit_ids.add(str(unit.id))
        fee_ids.add(str(fee.id))

        # Determine status
        status = assignment.status  # 'paid', 'unpaid', 'partial', 'waived', etc.
        # Normalise to our four values
        if status not in ('paid', 'partial', 'waived'):
            status = 'unpaid'

        # Days overdue
        days_overdue = 0
        if fee.due_date and today > fee.due_date and status != 'paid':
            days_overdue = (today - fee.due_date).days

        # Payment transaction
        payment = payments_by_assignment.get(assignment.id)
        payment_id = str(payment.id) if payment else None
        amount_paid = str(payment.amount) if payment else None

        # Timestamp — adapt field name to your Payment model
        payment_date = None
        if payment:
            ts = getattr(payment, 'created_at', None) or getattr(payment, 'payment_date', None)
            payment_date = ts.isoformat() if ts else None

        payment_method = getattr(payment, 'payment_method', None) if payment else None
        reference = (
            getattr(payment, 'reference_number', None) or
            getattr(payment, 'transaction_ref', None)
        ) if payment else None
        recorded_by_user = getattr(payment, 'recorded_by', None) if payment else None
        recorded_by = recorded_by_user.get_full_name() if recorded_by_user else None
        notes = getattr(payment, 'notes', None) if payment else None

        total_expected += fee.amount
        if status == 'paid':
            paid_count += 1
            total_collected += Decimal(amount_paid) if amount_paid else fee.amount
        else:
            unpaid_count += 1

        rows.append({
            # Unit
            'unit_id':         str(unit.id),
            'unit_name':       unit.identifier,
            'owner_id':        str(owner.id) if owner else None,
            'owner_name':      owner.get_full_name() if owner else None,
            'owner_email':     owner.email if owner else None,
            # Fee
            'fee_id':          str(fee.id),
            'fee_name':        fee.name,
            'fee_type':        getattr(fee, 'fee_type', 'standard'),
            'fee_amount':      str(fee.amount),
            'due_date':        fee.due_date.isoformat() if fee.due_date else None,
            # Assignment
            'status':          status,
            'days_overdue':    days_overdue,
            # Payment transaction
            'payment_id':      payment_id,
            'amount_paid':     amount_paid,
            'payment_date':    payment_date,
            'payment_method':  payment_method,
            'reference_number':       reference,
            'recorded_by':     recorded_by,
            'notes':           notes,
        })

    total_pending = total_expected - total_collected
    overall_rate = Decimal('0.00')
    if total_expected > 0:
        overall_rate = (total_collected / total_expected * 100).quantize(Decimal('0.01'))

    logger.info(
        f"Estate audit: {len(rows)} assignments, {paid_count} paid, "
        f"{unpaid_count} unpaid, rate={overall_rate}%"
    )

    return {
        'estate_id':             str(estate.id),
        'estate_name':           estate.name,
        'generated_at':          date_type.today().isoformat(),
        'total_units':           len(unit_ids),
        'total_fees':            len(fee_ids),
        'total_assignments':     len(rows),
        'paid_count':            paid_count,
        'unpaid_count':          unpaid_count,
        'total_expected':        str(total_expected),
        'total_collected':       str(total_collected),
        'total_pending':         str(total_pending),
        'overall_payment_rate':  str(overall_rate),
        'rows':                  rows,
    }

