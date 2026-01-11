# core/validators.py
"""
Custom validators for common fields.
"""

from django.core.exceptions import ValidationError
from django.core.validators import RegexValidator
import re


def validate_phone_number(value: str) -> None:
    """
    Validate Nigerian phone number format.
    
    Args:
        value: Phone number string
        
    Raises:
        ValidationError: If format is invalid
    """
    # Remove spaces and dashes
    cleaned = re.sub(r'[\s\-]', '', value)
    
    # Check if it matches Nigerian format
    pattern = r'^(\+234|0)[789][01]\d{8}$'
    if not re.match(pattern, cleaned):
        raise ValidationError(
            'Invalid phone number. Must be a valid Nigerian phone number.'
        )


phone_validator = RegexValidator(
    regex=r'^(\+234|0)?[789][01]\d{8}$',
    message='Enter a valid Nigerian phone number.'
)


def validate_positive_amount(value):
    """Validate that an amount is positive."""
    if value <= 0:
        raise ValidationError('Amount must be greater than zero.')


