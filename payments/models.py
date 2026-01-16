# payments/models.py

"""
Models for the payments app.

Handles fees, fee assignments to units, payments, and receipts.
"""

import uuid
from decimal import Decimal
from django.db import models
from django.contrib.auth import get_user_model
from django.core.validators import MinValueValidator
from django.core.exceptions import ValidationError
from django.utils import timezone

User = get_user_model()


class Fee(models.Model):
    """
    Represents a fee that can be assigned to units.
    
    Examples: "Security Levy 2025", "Annual Service Charge", "Water Bill Q1"
    """
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255, help_text="Fee name (e.g., 'Security Levy 2025')")
    description = models.TextField(blank=True, help_text="Optional detailed description")
    amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))],
        help_text="Fee amount"
    )
    due_date = models.DateField(help_text="Payment due date")
    estate = models.ForeignKey(
        'estates.Estate',
        on_delete=models.CASCADE,
        related_name='fees',
        help_text="Estate this fee belongs to"
    )
    created_by = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        related_name='created_fees',
        help_text="User who created this fee"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Fee'
        verbose_name_plural = 'Fees'
        indexes = [
            models.Index(fields=['estate', '-created_at']),
            models.Index(fields=['due_date']),
        ]
    
    def __str__(self):
        return f"{self.name} - {self.amount}"
    
    def clean(self):
        """Validate fee data."""
        if self.due_date and self.due_date < timezone.now().date():
            raise ValidationError({'due_date': 'Due date cannot be in the past.'})
    
    @property
    def total_assigned_units(self):
        """Return count of units assigned to this fee."""
        return self.fee_assignments.count()
    
    @property
    def total_paid_count(self):
        """Return count of paid fee assignments."""
        return self.fee_assignments.filter(status='paid').count()
    
    @property
    def total_unpaid_count(self):
        """Return count of unpaid fee assignments."""
        return self.fee_assignments.filter(status='unpaid').count()


class FeeAssignment(models.Model):
    """
    Links a Fee to a specific Unit with payment status tracking.
    
    This is the join table that allows tracking payment status per unit.
    """
    
    class PaymentStatus(models.TextChoices):
        UNPAID = 'unpaid', 'Unpaid'
        PAID = 'paid', 'Paid'
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    fee = models.ForeignKey(
        Fee,
        on_delete=models.CASCADE,
        related_name='fee_assignments',
        help_text="The fee being assigned"
    )
    unit = models.ForeignKey(
        'units.Unit',
        on_delete=models.CASCADE,
        related_name='fee_assignments',
        help_text="The unit this fee applies to"
    )
    status = models.CharField(
        max_length=10,
        choices=PaymentStatus.choices,
        default=PaymentStatus.UNPAID,
        help_text="Payment status"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Fee Assignment'
        verbose_name_plural = 'Fee Assignments'
        unique_together = [['fee', 'unit']]
        indexes = [
            models.Index(fields=['fee', 'status']),
            models.Index(fields=['unit', 'status']),
        ]
    
    def __str__(self):
        return f"{self.fee.name} → {self.unit} ({self.status})"
    
    def clean(self):
        """Validate fee assignment."""
        if self.fee and self.unit:
            if self.fee.estate_id != self.unit.estate_id:
                raise ValidationError(
                    "Fee and Unit must belong to the same estate."
                )


class Payment(models.Model):
    """
    Represents a payment made for a specific fee assignment.
    
    Records when, how, and by whom a fee was paid.
    """
    
    class PaymentMethod(models.TextChoices):
        BANK_TRANSFER = 'bank_transfer', 'Bank Transfer'
        CASH = 'cash', 'Cash'
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    fee_assignment = models.OneToOneField(
        FeeAssignment,
        on_delete=models.PROTECT,
        related_name='payment',
        help_text="The fee assignment this payment is for"
    )
    amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))],
        help_text="Amount paid"
    )
    payment_method = models.CharField(
        max_length=20,
        choices=PaymentMethod.choices,
        help_text="Method of payment"
    )
    payment_date = models.DateTimeField(
        default=timezone.now,
        help_text="When the payment was made"
    )
    reference_number = models.CharField(
        max_length=100,
        blank=True,
        help_text="Optional payment reference (e.g., transaction ID)"
    )
    notes = models.TextField(
        blank=True,
        help_text="Optional payment notes"
    )
    recorded_by = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        related_name='recorded_payments',
        help_text="User who recorded this payment"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-payment_date']
        verbose_name = 'Payment'
        verbose_name_plural = 'Payments'
        indexes = [
            models.Index(fields=['-payment_date']),
            models.Index(fields=['fee_assignment']),
        ]
    
    def __str__(self):
        return f"Payment {self.amount} for {self.fee_assignment.fee.name}"
    
    def clean(self):
        """Validate payment data."""
        if self.fee_assignment and self.amount:
            if self.amount != self.fee_assignment.fee.amount:
                raise ValidationError({
                    'amount': f'Payment amount must match fee amount ({self.fee_assignment.fee.amount})'
                })


class Receipt(models.Model):
    payment = models.OneToOneField(Payment, on_delete=models.CASCADE, related_name='receipt')
    receipt_number = models.CharField(max_length=50, unique=True)
    estate_name = models.CharField(max_length=255)
    unit_identifier = models.CharField(max_length=255)
    fee_name = models.CharField(max_length=255)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    payment_date = models.DateField()
    payment_method = models.CharField(max_length=50)
    issued_at = models.DateTimeField(auto_now_add=True)
    
    def save(self, *args, **kwargs):
        """Auto-generate receipt number if not set."""
        if not self.receipt_number:
            # Format: RCP-YYYYMMDD-XXXXX (where X is sequential)
            today = timezone.now().date()
            date_str = today.strftime('%Y%m%d')
            
            # Count existing receipts for today
            today_count = Receipt.objects.filter(
                receipt_number__startswith=f'RCP-{date_str}'
            ).count() + 1
            
            self.receipt_number = f'RCP-{date_str}-{today_count:05d}'
        
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f'Receipt {self.receipt_number}'