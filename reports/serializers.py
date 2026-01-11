# reports/serializers.py
"""
Serializers for reports app.
"""

from rest_framework import serializers
from django.contrib.auth import get_user_model

User = get_user_model()


class UnpaidUnitSerializer(serializers.Serializer):
    """
    Serializer for units/tenants who haven't paid a specific fee.
    
    Used in fee payment status reports.
    """
    
    unit_id = serializers.UUIDField(
        read_only=True,
        help_text="Unique identifier for the unit"
    )
    unit_name = serializers.CharField(
        read_only=True,
        help_text="Name/number of the unit"
    )
    tenant_id = serializers.UUIDField(
        read_only=True,
        allow_null=True,
        help_text="Unique identifier for the tenant (user)"
    )
    tenant_name = serializers.CharField(
        read_only=True,
        help_text="Full name of the tenant"
    )
    tenant_email = serializers.EmailField(
        read_only=True,
        help_text="Email address of the tenant"
    )
    estate_name = serializers.CharField(
        read_only=True,
        help_text="Name of the estate/property"
    )
    estate_id = serializers.UUIDField(
        read_only=True,
        help_text="Unique identifier for the estate"
    )
    amount_due = serializers.DecimalField(
        max_digits=12,
        decimal_places=2,
        read_only=True,
        help_text="Amount the tenant owes for this fee"
    )
    due_date = serializers.DateField(
        read_only=True,
        help_text="When the payment was due"
    )
    days_overdue = serializers.IntegerField(
        read_only=True,
        help_text="Number of days the payment is overdue"
    )


class FeePaymentStatusSerializer(serializers.Serializer):
    """
    Serializer for payment status report of a specific fee.
    
    Shows who has paid and who hasn't for a given fee.
    """
    
    fee_id = serializers.UUIDField(
        read_only=True,
        help_text="Unique identifier for the fee"
    )
    fee_name = serializers.CharField(
        read_only=True,
        help_text="Name of the fee"
    )
    fee_type = serializers.CharField(
        read_only=True,
        help_text="Type of fee (monthly, annual, one-time)"
    )
    total_expected = serializers.DecimalField(
        max_digits=12,
        decimal_places=2,
        read_only=True,
        help_text="Total amount expected from all units"
    )
    total_collected = serializers.DecimalField(
        max_digits=12,
        decimal_places=2,
        read_only=True,
        help_text="Total amount collected so far"
    )
    total_pending = serializers.DecimalField(
        max_digits=12,
        decimal_places=2,
        read_only=True,
        help_text="Total amount still pending"
    )
    payment_rate = serializers.DecimalField(
        max_digits=5,
        decimal_places=2,
        read_only=True,
        help_text="Percentage of expected amount collected"
    )
    total_units = serializers.IntegerField(
        read_only=True,
        help_text="Total number of units liable for this fee"
    )
    paid_units = serializers.IntegerField(
        read_only=True,
        help_text="Number of units that have paid"
    )
    unpaid_units_count = serializers.IntegerField(
        read_only=True,
        help_text="Number of units that haven't paid"
    )
    unpaid_units = UnpaidUnitSerializer(
        many=True,
        read_only=True,
        help_text="List of units that haven't paid"
    )


class FeeSummarySerializer(serializers.Serializer):
    """
    Serializer for summarized fee collection information.
    
    Provides high-level overview without detailed unpaid unit list.
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
    Serializer for overall payment summary across all fees.
    
    Provides a high-level dashboard view of all payment collections.
    """
    
    total_fees = serializers.IntegerField(
        read_only=True,
        help_text="Total number of active fees"
    )
    total_expected_all_fees = serializers.DecimalField(
        max_digits=15,
        decimal_places=2,
        read_only=True,
        help_text="Total expected across all fees"
    )
    total_collected_all_fees = serializers.DecimalField(
        max_digits=15,
        decimal_places=2,
        read_only=True,
        help_text="Total collected across all fees"
    )
    total_pending_all_fees = serializers.DecimalField(
        max_digits=15,
        decimal_places=2,
        read_only=True,
        help_text="Total pending across all fees"
    )
    overall_payment_rate = serializers.DecimalField(
        max_digits=5,
        decimal_places=2,
        read_only=True,
        help_text="Overall collection rate percentage"
    )
    fees_summary = FeeSummarySerializer(
        many=True,
        read_only=True,
        help_text="Summary for each individual fee"
    )


class EstatePaymentSummarySerializer(serializers.Serializer):
    """
    Serializer for estate-specific payment summary.
    """
    
    estate_id = serializers.UUIDField(read_only=True)
    estate_name = serializers.CharField(read_only=True)
    total_units = serializers.IntegerField(read_only=True)
    occupied_units = serializers.IntegerField(read_only=True)
    total_fees = serializers.IntegerField(read_only=True)
    total_expected = serializers.DecimalField(max_digits=15, decimal_places=2, read_only=True)
    total_collected = serializers.DecimalField(max_digits=15, decimal_places=2, read_only=True)
    total_pending = serializers.DecimalField(max_digits=15, decimal_places=2, read_only=True)
    payment_rate = serializers.DecimalField(max_digits=5, decimal_places=2, read_only=True)
    fees_summary = FeeSummarySerializer(many=True, read_only=True)