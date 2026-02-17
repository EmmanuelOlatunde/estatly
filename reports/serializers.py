# reports/serializers.py
"""
Serializers for reports app.
"""

from rest_framework import serializers
from django.contrib.auth import get_user_model

User = get_user_model()


class UnpaidUnitSerializer(serializers.Serializer):
    """
    Serializer for units whose owners have not paid a specific fee.

    Field names match the dict keys produced by services.get_fee_payment_status.
    NOTE: The service uses 'owner_*' keys (not 'tenant_*') because Unit.owner
    is the correct FK name. If you rename it on the model, update both places.
    """

    unit_id = serializers.UUIDField(read_only=True)
    unit_name = serializers.CharField(read_only=True)
    owner_id = serializers.UUIDField(read_only=True, allow_null=True)
    owner_name = serializers.CharField(read_only=True, allow_null=True)
    owner_email = serializers.EmailField(read_only=True, allow_null=True)
    estate_id = serializers.UUIDField(read_only=True)
    estate_name = serializers.CharField(read_only=True)
    amount_due = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)
    due_date = serializers.DateField(read_only=True, allow_null=True)
    days_overdue = serializers.IntegerField(read_only=True)


class FeePaymentStatusSerializer(serializers.Serializer):
    """
    Serializer for payment status report of a specific fee.

    Shows aggregate financials plus a list of unpaid units.
    """

    fee_id = serializers.UUIDField(read_only=True)
    fee_name = serializers.CharField(read_only=True)
    fee_type = serializers.CharField(read_only=True)
    total_expected = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)
    total_collected = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)
    total_pending = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)
    payment_rate = serializers.DecimalField(max_digits=5, decimal_places=2, read_only=True)
    total_units = serializers.IntegerField(read_only=True)
    paid_units = serializers.IntegerField(read_only=True)
    unpaid_units_count = serializers.IntegerField(read_only=True)
    unpaid_units = UnpaidUnitSerializer(many=True, read_only=True)


class FeeSummarySerializer(serializers.Serializer):
    """
    Serializer for a single fee's collection summary.

    Used inside OverallPaymentSummarySerializer and EstatePaymentSummarySerializer.
    No unpaid unit detail — high-level overview only.
    """

    fee_id = serializers.UUIDField(read_only=True)
    fee_name = serializers.CharField(read_only=True)
    fee_type = serializers.CharField(read_only=True)
    total_expected = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)
    total_collected = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)
    total_pending = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)
    payment_rate = serializers.DecimalField(max_digits=5, decimal_places=2, read_only=True)
    total_units = serializers.IntegerField(read_only=True)
    paid_units = serializers.IntegerField(read_only=True)
    unpaid_units_count = serializers.IntegerField(read_only=True)


class OverallPaymentSummarySerializer(serializers.Serializer):
    """
    Serializer for the overall payment summary across all fees.

    Returned by GET /api/reports/overall-summary/
    """

    total_fees = serializers.IntegerField(read_only=True)
    total_expected_all_fees = serializers.DecimalField(max_digits=15, decimal_places=2, read_only=True)
    total_collected_all_fees = serializers.DecimalField(max_digits=15, decimal_places=2, read_only=True)
    total_pending_all_fees = serializers.DecimalField(max_digits=15, decimal_places=2, read_only=True)
    overall_payment_rate = serializers.DecimalField(max_digits=5, decimal_places=2, read_only=True)
    fees_summary = FeeSummarySerializer(many=True, read_only=True)


class EstatePaymentSummarySerializer(serializers.Serializer):
    """
    Serializer for estate-specific payment summary.

    Returned by GET /api/reports/estate/<estate_id>/
    NOTE: get_estate_payment_summary delegates to get_overall_payment_summary,
    so the response shape is identical to OverallPaymentSummarySerializer.
    estate_id / estate_name / total_units / occupied_units are not currently
    returned by the service — add them to the service first before uncommenting.
    """

    total_fees = serializers.IntegerField(read_only=True)
    total_expected_all_fees = serializers.DecimalField(max_digits=15, decimal_places=2, read_only=True)
    total_collected_all_fees = serializers.DecimalField(max_digits=15, decimal_places=2, read_only=True)
    total_pending_all_fees = serializers.DecimalField(max_digits=15, decimal_places=2, read_only=True)
    overall_payment_rate = serializers.DecimalField(max_digits=5, decimal_places=2, read_only=True)
    fees_summary = FeeSummarySerializer(many=True, read_only=True)

    # Uncomment and add to service output when ready:
    # estate_id = serializers.UUIDField(read_only=True)
    # estate_name = serializers.CharField(read_only=True)
    # total_units = serializers.IntegerField(read_only=True)
    # occupied_units = serializers.IntegerField(read_only=True)