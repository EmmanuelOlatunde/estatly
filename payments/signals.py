# payments/signals.py

"""
Django signals for the payments app.

Handles automatic actions when payments and receipts are created.
"""

from django.db.models.signals import post_save, pre_delete
from django.dispatch import receiver
from django.core.exceptions import ValidationError
from .models import Payment, FeeAssignment


@receiver(post_save, sender=Payment)
def update_fee_assignment_and_generate_receipt(sender, instance, created, **kwargs):
    """
    Automatically update FeeAssignment status and generate receipt when payment is created.
    
    This ensures receipts are generated even when payments are created via admin panel.
    """
    if created:
        # Update fee assignment status
        fee_assignment = instance.fee_assignment
        if fee_assignment.status != FeeAssignment.PaymentStatus.PAID:
            fee_assignment.status = FeeAssignment.PaymentStatus.PAID
            fee_assignment.save(update_fields=['status', 'updated_at'])
        
        # Generate receipt if it doesn't exist
        if not hasattr(instance, 'receipt'):
            from . import services
            try:
                services.generate_receipt_for_payment(payment=instance)
            except Exception as e:
                # Log the error but don't prevent payment creation
                import logging
                logger = logging.getLogger(__name__)
                logger.error(f"Failed to generate receipt for payment {instance.id}: {str(e)}")




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