# payments/signals.py

"""
Django signals for the payments app.

Handles automatic actions when payments and receipts are created.
"""

from django.db.models.signals import post_save, pre_delete
from django.dispatch import receiver
from rest_framework.exceptions import ValidationError
from .models import Payment, FeeAssignment


@receiver(post_save, sender=Payment)
def update_fee_assignment_status(sender, instance, created, **kwargs):
    """
    Automatically update FeeAssignment status when payment is created.
    
    Receipt generation is handled by the service layer in perform_create(),
    not here, to avoid double-generation.
    """
    if created:
        # Update fee assignment status to PAID
        fee_assignment = instance.fee_assignment
        if fee_assignment.status != FeeAssignment.PaymentStatus.PAID:
            fee_assignment.status = FeeAssignment.PaymentStatus.PAID
            fee_assignment.save(update_fields=['status', 'updated_at'])


@receiver(pre_delete, sender=Payment)
def prevent_payment_deletion(sender, instance, **kwargs):
    """
    Prevent deletion of payments that have receipts.
    
    This maintains data integrity and audit trail.
    """
    if hasattr(instance, 'receipt'):
        raise ValidationError(
            "Cannot delete payment with an associated receipt. "
            "Delete the receipt first if necessary."
        )


@receiver(pre_delete, sender=FeeAssignment)
def prevent_paid_assignment_deletion(sender, instance, **kwargs):
    """
    Prevent deletion of fee assignments that have been paid.
    
    This maintains payment history integrity.
    """
    if instance.status == FeeAssignment.PaymentStatus.PAID:
        raise ValidationError(
            "Cannot delete a paid fee assignment. "
            "This would compromise payment records."
        )