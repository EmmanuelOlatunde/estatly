# payments/serializers.py

"""
Serializers for the payments app.

Handles serialization and validation for fees, payments, and receipts.
"""

from rest_framework import serializers
from django.utils import timezone
from .models import Fee, FeeAssignment, Payment, Receipt
from decimal import Decimal, ROUND_HALF_UP



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
    estate = serializers.PrimaryKeyRelatedField(read_only=True)

    total_assigned_units = serializers.IntegerField(read_only=True)
    total_paid_count = serializers.IntegerField(read_only=True)
    total_unpaid_count = serializers.IntegerField(read_only=True)
    id = serializers.CharField(read_only=True)
    
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
    """Serializer for creating and updating Fee instances."""
    
    # Explicitly define amount field to accept any decimal places
    # then round them in validation
    amount = serializers.DecimalField(
        max_digits=15,  # Allow more digits for input
        decimal_places=2,  # Allow up to 5 decimal places on input
        help_text="Fee amount (will be rounded to 2 decimal places)"
    )
    
    assign_to_all_units = serializers.BooleanField(
        write_only=True,
        default=False,
        required=False,
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
    
    def validate_amount(self, value):
        """
        Validate and round amount to 2 decimal places.
        
        Accepts amounts with up to 5 decimal places and rounds
        them to 2 decimal places using ROUND_HALF_UP.
        """
        if value <= 0:
            raise serializers.ValidationError(
                "Amount must be greater than zero."
            )
        
        # Round to 2 decimal places using ROUND_HALF_UP
        # This ensures 0.125 rounds to 0.13, not 0.12
        rounded = value.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
        
        return rounded
    
    def validate_due_date(self, value):
        """Ensure due date is not in the past."""
        if value < timezone.now().date():
            raise serializers.ValidationError("Due date cannot be in the past.")
        return value
    
    def validate(self, attrs):
        """
        Validate assignment method for creation.
        
        For updates, assignment fields are optional.
        """
        # Only validate assignment on CREATE, not UPDATE
        if self.instance is None:  # This is a create operation
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
    """Serializer for fee assignments with receipt and PDF document information."""
    
    unit_identifier = serializers.CharField(source='unit.identifier', read_only=True)
    receipt_id = serializers.SerializerMethodField()
    receipt_number = serializers.SerializerMethodField()
    pdf_status = serializers.SerializerMethodField()  # NEW: PDF generation status
    pdf_document_id = serializers.SerializerMethodField()  # NEW: Document ID for direct access
    
    class Meta:
        model = FeeAssignment
        fields = [
            'id',
            'fee',
            'unit',
            'unit_identifier',
            'status',
            'created_at',
            'updated_at',
            'receipt_id',
            'receipt_number',
            'pdf_status',  # NEW
            'pdf_document_id',  # NEW
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def get_receipt_id(self, obj):
        """Get receipt ID if payment exists and has a receipt."""
        try:
            if hasattr(obj, 'payment') and hasattr(obj.payment, 'receipt'):
                return str(obj.payment.receipt.id)
        except (Payment.DoesNotExist, Receipt.DoesNotExist):
            pass
        return None
    
    def get_receipt_number(self, obj):
        """Get receipt number if payment exists and has a receipt."""
        try:
            if hasattr(obj, 'payment') and hasattr(obj.payment, 'receipt'):
                return obj.payment.receipt.receipt_number
        except (Payment.DoesNotExist, Receipt.DoesNotExist):
            pass
        return None
    
    def get_pdf_status(self, obj):
        """
        Get PDF document generation status.
        
        Returns:
            - 'pending': PDF is being generated
            - 'completed': PDF is ready for download
            - 'failed': PDF generation failed
            - 'not_found': No PDF document exists
            - None: No payment/receipt exists
        """
        try:
            if not hasattr(obj, 'payment'):
                return None
            
            from documents.models import Document, DocumentType
            
            document = Document.objects.filter(
                document_type=DocumentType.PAYMENT_RECEIPT,
                related_payment_id=obj.payment.id,
                is_deleted=False,
            ).first()
            
            if not document:
                return 'not_found'
            
            return document.status
            
        except (Payment.DoesNotExist, Exception):
            return None
    
    def get_pdf_document_id(self, obj):
        """
        Get PDF document ID for direct download access.
        
        Returns document ID if available, None otherwise.
        """
        try:
            if not hasattr(obj, 'payment'):
                return None
            
            from documents.models import Document, DocumentType, DocumentStatus
            
            document = Document.objects.filter(
                document_type=DocumentType.PAYMENT_RECEIPT,
                related_payment_id=obj.payment.id,
                is_deleted=False,
                status=DocumentStatus.COMPLETED,
            ).first()
            
            return str(document.id) if document else None
            
        except (Payment.DoesNotExist, Exception):
            return None

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
    id = serializers.UUIDField(read_only=True)
    
    # ✓ FIX: Use DateTimeField for Payment.payment_date (which is a DateTimeField in the model)
    payment_date = serializers.DateTimeField(read_only=True)
    
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
            'payment_date',  # ✓ Add this as read-only
        ]
    
    def get_has_receipt(self, obj):
        """Check if this payment has an associated receipt."""
        return hasattr(obj, 'receipt') and obj.receipt is not None

class PaymentCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating payments."""
    
    fee_assignment = serializers.PrimaryKeyRelatedField(queryset=FeeAssignment.objects.all())
    
    class Meta:
        model = Payment
        fields = [
            'fee_assignment',
            'amount',
            'payment_method',
            'payment_date',
            'reference_number',
            'notes',
        ]
    
    def validate_fee_assignment(self, value):
        """Validate fee_assignment is not already paid."""
        if value.status == FeeAssignment.PaymentStatus.PAID:
            raise serializers.ValidationError(
                "This fee has already been marked as paid."
            )
        
        # Check user has access to this estate
        user = self.context['request'].user
        if value.fee.estate.id != user.estate.id:
            raise serializers.ValidationError(
                "You do not have permission to create payments for this fee."
            )
        
        return value
    
    def validate_amount(self, value):
        """Validate amount is positive."""
        if value <= 0:
            raise serializers.ValidationError("Amount must be greater than zero.")
        return value
    
    def validate(self, attrs):
        """Validate amount matches fee amount."""
        fee_assignment = attrs.get('fee_assignment')
        amount = attrs.get('amount')
        
        if fee_assignment and amount:
            if amount != fee_assignment.fee.amount:
                raise serializers.ValidationError({
                    'amount': f"Payment amount ({amount}) must match fee amount ({fee_assignment.fee.amount})"
                })
        
        return attrs
    
class ReceiptSerializer(serializers.ModelSerializer):
    """Serializer for reading Receipt data."""
    
    payment_id = serializers.UUIDField(source='payment.id', read_only=True)
    id = serializers.UUIDField(read_only=True)
    
    # ✓ FIX: Add payment_date as DateField for Receipt model
    # Check your Receipt model - if it has payment_date as a DateField, use this:
    payment_date = serializers.DateField(read_only=True)

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
            'payment_date',  # ✓ Add this
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
            'payment_date',  # ✓ Add here too
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