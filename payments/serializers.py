# payments/serializers.py

"""
Serializers for the payments app.

Handles serialization and validation for fees, payments, and receipts.
"""

from rest_framework import serializers
from django.utils import timezone
from .models import Fee, FeeAssignment, Payment, Receipt


class FeeSerializer(serializers.ModelSerializer):
    """Serializer for reading Fee data."""
    
    created_by_name = serializers.CharField(
        source='created_by.get_full_name',
        read_only=True
    )
    estate_name = serializers.CharField(
        source='estate.name',
        read_only=True
    )
    total_assigned_units = serializers.IntegerField(read_only=True)
    total_paid_count = serializers.IntegerField(read_only=True)
    total_unpaid_count = serializers.IntegerField(read_only=True)
    
    class Meta:
        model = Fee
        fields = [
            'id',
            'name',
            'description',
            'amount',
            'due_date',
            'estate',
            'estate_name',
            'created_by',
            'created_by_name',
            'total_assigned_units',
            'total_paid_count',
            'total_unpaid_count',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['id', 'created_by', 'created_at', 'updated_at']


class FeeCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating Fee instances."""
    
    assign_to_all_units = serializers.BooleanField(
        write_only=True,
        default=False,
        help_text="If true, assign this fee to all units in the estate"
    )
    unit_ids = serializers.ListField(
        child=serializers.UUIDField(),
        write_only=True,
        required=False,
        allow_empty=True,
        help_text="List of unit IDs to assign this fee to (if not assigning to all)"
    )
    
    class Meta:
        model = Fee
        fields = [
            'id',
            'name',
            'description',
            'amount',
            'due_date',
            'estate',
            'assign_to_all_units',
            'unit_ids',
        ]
        read_only_fields = ['id']
    
    def validate_due_date(self, value):
        """Ensure due date is not in the past."""
        if value < timezone.now().date():
            raise serializers.ValidationError("Due date cannot be in the past.")
        return value
    
    def validate(self, attrs):
        """Validate that either assign_to_all_units or unit_ids is provided."""
        assign_all = attrs.get('assign_to_all_units', False)
        unit_ids = attrs.get('unit_ids', [])
        
        if not assign_all and not unit_ids:
            raise serializers.ValidationError(
                "Must either set 'assign_to_all_units' to true or provide 'unit_ids'."
            )
        
        if assign_all and unit_ids:
            raise serializers.ValidationError(
                "Cannot set both 'assign_to_all_units' and 'unit_ids'. Choose one."
            )
        
        return attrs


class FeeAssignmentSerializer(serializers.ModelSerializer):
    """Serializer for reading FeeAssignment data."""
    
    fee_name = serializers.CharField(source='fee.name', read_only=True)
    fee_amount = serializers.DecimalField(
        source='fee.amount',
        max_digits=12,
        decimal_places=2,
        read_only=True
    )
    fee_due_date = serializers.DateField(source='fee.due_date', read_only=True)
    unit_identifier = serializers.CharField(source='unit.identifier', read_only=True)
    unit_address = serializers.CharField(source='unit.address', read_only=True)
    has_payment = serializers.SerializerMethodField()
    
    class Meta:
        model = FeeAssignment
        fields = [
            'id',
            'fee',
            'fee_name',
            'fee_amount',
            'fee_due_date',
            'unit',
            'unit_identifier',
            'unit_address',
            'status',
            'has_payment',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def get_has_payment(self, obj):
        """Check if this assignment has an associated payment."""
        return hasattr(obj, 'payment')


class PaymentSerializer(serializers.ModelSerializer):
    """Serializer for reading Payment data."""
    
    fee_name = serializers.CharField(
        source='fee_assignment.fee.name',
        read_only=True
    )
    unit_identifier = serializers.CharField(
        source='fee_assignment.unit.identifier',
        read_only=True
    )
    estate_name = serializers.CharField(
        source='fee_assignment.fee.estate.name',
        read_only=True
    )
    recorded_by_name = serializers.CharField(
        source='recorded_by.get_full_name',
        read_only=True
    )
    has_receipt = serializers.SerializerMethodField()
    
    class Meta:
        model = Payment
        fields = [
            'id',
            'fee_assignment',
            'fee_name',
            'unit_identifier',
            'estate_name',
            'amount',
            'payment_method',
            'payment_date',
            'reference_number',
            'notes',
            'recorded_by',
            'recorded_by_name',
            'has_receipt',
            'created_at',
            'updated_at',
        ]
        read_only_fields = [
            'id',
            'recorded_by',
            'created_at',
            'updated_at',
        ]
    
    def get_has_receipt(self, obj):
        """Check if this payment has an associated receipt."""
        return hasattr(obj, 'receipt')


class PaymentCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating Payment instances (marking fee as paid)."""
    
    class Meta:
        model = Payment
        fields = [
            'id',
            'fee_assignment',
            'amount',
            'payment_method',
            'payment_date',
            'reference_number',
            'notes',
        ]
        read_only_fields = ['id']
    
    def validate_fee_assignment(self, value):
        """Ensure the fee assignment is not already paid."""
        if value.status == FeeAssignment.PaymentStatus.PAID:
            raise serializers.ValidationError(
                "This fee has already been paid."
            )
        
        if hasattr(value, 'payment'):
            raise serializers.ValidationError(
                "A payment already exists for this fee assignment."
            )
        
        return value
    
    def validate_amount(self, value):
        """Ensure payment amount is positive."""
        if value <= 0:
            raise serializers.ValidationError(
                "Payment amount must be greater than zero."
            )
        return value
    
    def validate(self, attrs):
        """Validate that payment amount matches fee amount."""
        fee_assignment = attrs.get('fee_assignment')
        amount = attrs.get('amount')
        
        if fee_assignment and amount:
            if amount != fee_assignment.fee.amount:
                raise serializers.ValidationError({
                    'amount': f'Payment amount must match the fee amount ({fee_assignment.fee.amount})'
                })
        
        return attrs


class ReceiptSerializer(serializers.ModelSerializer):
    """Serializer for reading Receipt data."""
    
    payment_id = serializers.UUIDField(source='payment.id', read_only=True)
    
    class Meta:
        model = Receipt
        fields = [
            'id',
            'receipt_number',
            'payment',
            'payment_id',
            'estate_name',
            'unit_identifier',
            'fee_name',
            'amount',
            'payment_date',
            'payment_method',
            'issued_at',
        ]
        read_only_fields = [
            'id',
            'receipt_number',
            'estate_name',
            'unit_identifier',
            'fee_name',
            'amount',
            'payment_date',
            'payment_method',
            'issued_at',
        ]


class FeeDetailSerializer(serializers.ModelSerializer):
    """Detailed serializer for Fee with assignments included."""
    
    assignments = FeeAssignmentSerializer(
        source='fee_assignments',
        many=True,
        read_only=True
    )
    created_by_name = serializers.CharField(
        source='created_by.get_full_name',
        read_only=True
    )
    estate_name = serializers.CharField(
        source='estate.name',
        read_only=True
    )
    
    class Meta:
        model = Fee
        fields = [
            'id',
            'name',
            'description',
            'amount',
            'due_date',
            'estate',
            'estate_name',
            'created_by',
            'created_by_name',
            'assignments',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['id', 'created_by', 'created_at', 'updated_at']