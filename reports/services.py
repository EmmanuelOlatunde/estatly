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

User = get_user_model()
logger = logging.getLogger(__name__)


def get_fee_payment_status(
    *,
    fee_id: str,
    user
) -> Dict[str, Any]:
    """
    Generate payment status report for a specific fee.
    
    Shows total collected amount and list of units/tenants who haven't paid.
    
    Args:
        fee_id: UUID of the fee to report on
        user: User instance requesting the report (must be landlord/owner)
        
    Returns:
        Dictionary containing:
            - fee_id: UUID of the fee
            - fee_name: Name of the fee
            - fee_type: Type of fee
            - total_expected: Total amount expected
            - total_collected: Total amount collected
            - total_pending: Total amount pending
            - payment_rate: Percentage collected
            - total_units: Number of units liable
            - paid_units: Number that paid
            - unpaid_units_count: Number that haven't paid
            - unpaid_units: List of unpaid unit details
            
    Raises:
        ValueError: If fee doesn't exist or user doesn't have permission
    """
    # Import models here to avoid circular imports
    try:
        from payments.models import Payment
    except ImportError:
        logger.error("Cannot import Payment model")
        raise ValueError("Payment system not configured")
    
    # Try to import Fee from different possible locations
    Fee = None
    fee = None
    
    # Check if fees are in payments app
    try:
        from payments.models import Fee
        logger.info("Fee model found in payments app")
    except ImportError:
        pass
    
    # Check if there's a separate fees app
    if Fee is None:
        try:
            from payments.models import Fee
            logger.info("Fee model found in fees app")
        except ImportError:
            pass
    
    # Check if fees are in estates app
    if Fee is None:
        try:
            from estates.models import Fee
            logger.info("Fee model found in estates app")
        except ImportError:
            pass
    
    if Fee is None:
        logger.error("Fee model not found in any expected location")
        raise ValueError("Fee model not configured")
    
    logger.info(f"Generating payment status report for fee {fee_id} by user {user.id}")
    
    # Try to get the fee with permission check
    try:
        # Assuming fee is related to estate owned by user
        fee = Fee.objects.select_related('estate').get(id=fee_id)
        
        # Check permission - adjust based on your actual model structure
        if hasattr(fee, 'estate'):
            if not (hasattr(fee.estate, 'owner') and fee.estate.owner == user):
                raise ValueError("You don't have permission to view this fee")
        elif hasattr(fee, 'property'):
            if not (hasattr(fee.property, 'landlord') and fee.property.landlord == user):
                raise ValueError("You don't have permission to view this fee")
        
    except Fee.DoesNotExist:
        logger.error(f"Fee {fee_id} not found")
        raise ValueError("Fee not found")
    
    # Import Unit model
    try:
        from units.models import Unit
    except ImportError:
        logger.error("Cannot import Unit model")
        raise ValueError("Unit system not configured")
    
    # Get all occupied units in the estate/property
    estate_field = 'estate' if hasattr(fee, 'estate') else 'property'
    estate_obj = getattr(fee, estate_field)
    
    occupied_units = Unit.objects.filter(
        **{estate_field: estate_obj},
        is_occupied=True
    ).select_related('tenant', estate_field)
    
    total_units = occupied_units.count()
    
    # Calculate expected amount
    total_expected = fee.amount * total_units
    
    # Get all payments for this fee
    payments = Payment.objects.filter(
        fee=fee,
        status__in=['completed', 'verified', 'paid']
    ).select_related('unit__tenant')
    
    # Calculate collected amount
    total_collected = payments.aggregate(
        total=Sum('amount')
    )['total'] or Decimal('0.00')
    
    # Get units that have paid
    paid_unit_ids = set(payments.values_list('unit_id', flat=True))
    
    # Get unpaid units
    unpaid_units = occupied_units.exclude(id__in=paid_unit_ids)
    
    # Calculate days overdue
    today = timezone.now().date()
    days_overdue = (today - fee.due_date).days if fee.due_date < today else 0
    
    # Build unpaid units list
    unpaid_units_data = []
    for unit in unpaid_units:
        tenant_name = "Vacant"
        tenant_email = ""
        tenant_id = None
        
        if hasattr(unit, 'tenant') and unit.tenant:
            tenant = unit.tenant
            if hasattr(tenant, 'user'):
                tenant_name = tenant.user.get_full_name() or tenant.user.username
                tenant_email = tenant.user.email
                tenant_id = tenant.user.id
            elif hasattr(tenant, 'name'):
                tenant_name = tenant.name
                tenant_email = getattr(tenant, 'email', '')
                tenant_id = tenant.id
        
        unpaid_units_data.append({
            'unit_id': unit.id,
            'unit_name': getattr(unit, 'unit_number', None) or getattr(unit, 'name', str(unit.id)),
            'tenant_id': tenant_id,
            'tenant_name': tenant_name,
            'tenant_email': tenant_email,
            'estate_name': getattr(estate_obj, 'name', str(estate_obj.id)),
            'estate_id': estate_obj.id,
            'amount_due': fee.amount,
            'due_date': fee.due_date,
            'days_overdue': max(0, days_overdue)
        })
    
    paid_units_count = len(paid_unit_ids)
    unpaid_units_count = unpaid_units.count()
    total_pending = total_expected - total_collected
    
    # Calculate payment rate
    payment_rate = Decimal('0.00')
    if total_expected > 0:
        payment_rate = (total_collected / total_expected * 100).quantize(Decimal('0.01'))
    
    logger.info(
        f"Fee {fee_id} report: {paid_units_count}/{total_units} paid, "
        f"{total_collected}/{total_expected} collected"
    )
    
    return {
        'fee_id': fee.id,
        'fee_name': fee.name,
        'fee_type': getattr(fee, 'fee_type', 'unknown'),
        'total_expected': total_expected,
        'total_collected': total_collected,
        'total_pending': total_pending,
        'payment_rate': payment_rate,
        'total_units': total_units,
        'paid_units': paid_units_count,
        'unpaid_units_count': unpaid_units_count,
        'unpaid_units': unpaid_units_data
    }


def get_overall_payment_summary(
    *,
    user,
    estate_id: Optional[str] = None
) -> Dict[str, Any]:
    """
    Generate overall payment summary across all fees.
    
    Optionally filter by a specific estate.
    
    Args:
        user: User instance requesting the report
        estate_id: Optional UUID to filter by specific estate
        
    Returns:
        Dictionary containing:
            - total_fees: Number of fees
            - total_expected_all_fees: Total expected across all fees
            - total_collected_all_fees: Total collected across all fees
            - total_pending_all_fees: Total pending across all fees
            - overall_payment_rate: Overall collection percentage
            - fees_summary: List of summary for each fee
            
    Raises:
        ValueError: If estate doesn't exist or user doesn't have permission
    """
    # Import models
    try:
        from payments.models import Payment
        from units.models import Unit
    except ImportError as e:
        logger.error(f"Cannot import required models: {e}")
        raise ValueError("Required models not configured")
    
    # Try to import Fee from different locations
    Fee = None
    try:
        from payments.models import Fee
    except ImportError:
        try:
            from payments.models import Fee
        except ImportError:
            try:
                from estates.models import Fee
            except ImportError:
                pass
    
    if Fee is None:
        logger.error("Fee model not found")
        raise ValueError("Fee model not configured")
    
    # Try to import Estate
    Estate = None
    try:
        from estates.models import Estate
    except ImportError:
        try:
            from units.models import Unit as Estate
        except ImportError:
            pass
    
    logger.info(
        f"Generating overall payment summary for user {user.id}, "
        f"estate_id={estate_id}"
    )
    
    # Build query for fees
    fees_query = Q()
    
    # Determine the ownership field
    if hasattr(Fee, 'estate'):
        if Estate and hasattr(Estate, 'owner'):
            fees_query &= Q(estate__owner=user)
        elif Estate and hasattr(Estate, 'landlord'):
            fees_query &= Q(estate__landlord=user)
    elif hasattr(Fee, 'property'):
        fees_query &= Q(property__landlord=user)
    
    if estate_id:
        if Estate:
            try:
                estate_obj = Estate.objects.get(id=estate_id)
                # Check ownership
                if hasattr(estate_obj, 'owner') and estate_obj.owner != user:
                    raise ValueError("You don't have permission to view this estate")
                elif hasattr(estate_obj, 'landlord') and estate_obj.landlord != user:
                    raise ValueError("You don't have permission to view this estate")
                
                if hasattr(Fee, 'estate'):
                    fees_query &= Q(estate_id=estate_id)
                elif hasattr(Fee, 'property'):
                    fees_query &= Q(property_id=estate_id)
                    
                logger.info(f"Filtering report by estate {estate_id}")
            except Estate.DoesNotExist:
                logger.error(f"Estate {estate_id} not found")
                raise ValueError("Estate not found")
    
    fees = Fee.objects.filter(fees_query)
    
    total_fees = fees.count()
    
    if total_fees == 0:
        logger.info("No fees found for the given criteria")
        return {
            'total_fees': 0,
            'total_expected_all_fees': Decimal('0.00'),
            'total_collected_all_fees': Decimal('0.00'),
            'total_pending_all_fees': Decimal('0.00'),
            'overall_payment_rate': Decimal('0.00'),
            'fees_summary': []
        }
    
    fees_summary = []
    total_expected_all = Decimal('0.00')
    total_collected_all = Decimal('0.00')
    
    for fee in fees:
        # Get estate/property object
        estate_field = 'estate' if hasattr(fee, 'estate') else 'property'
        estate_obj = getattr(fee, estate_field)
        
        # Get occupied units count
        occupied_units_count = Unit.objects.filter(
            **{estate_field: estate_obj},
            is_occupied=True
        ).count()
        
        # Expected amount
        expected = fee.amount * occupied_units_count
        
        # Collected amount
        collected = Payment.objects.filter(
            fee=fee,
            status__in=['completed', 'verified', 'paid']
        ).aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
        
        # Count paid units
        paid_count = Payment.objects.filter(
            fee=fee,
            status__in=['completed', 'verified', 'paid']
        ).values('unit').distinct().count()
        
        pending = expected - collected
        
        # Calculate payment rate
        rate = Decimal('0.00')
        if expected > 0:
            rate = (collected / expected * 100).quantize(Decimal('0.01'))
        
        fees_summary.append({
            'fee_id': fee.id,
            'fee_name': fee.name,
            'fee_type': getattr(fee, 'fee_type', 'unknown'),
            'total_expected': expected,
            'total_collected': collected,
            'total_pending': pending,
            'payment_rate': rate,
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
        'total_expected_all_fees': total_expected_all,
        'total_collected_all_fees': total_collected_all,
        'total_pending_all_fees': total_pending_all,
        'overall_payment_rate': overall_rate,
        'fees_summary': fees_summary
    }


def get_estate_payment_summary(
    *,
    estate_id: str,
    user
) -> Dict[str, Any]:
    """
    Generate payment summary for a specific estate.
    
    Convenience function that calls get_overall_payment_summary with estate filter.
    
    Args:
        estate_id: UUID of the estate
        user: User instance of the landlord/owner
        
    Returns:
        Dictionary with payment summary for the estate
        
    Raises:
        ValueError: If estate doesn't exist or user doesn't have permission
    """
    logger.info(f"Generating estate payment summary for estate {estate_id}")
    
    return get_overall_payment_summary(
        user=user,
        estate_id=estate_id
    )