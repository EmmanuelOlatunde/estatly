
# core/utils.py
"""
Utility functions for the core app.
"""

import logging
from decimal import Decimal
# from typing import Optional

logger = logging.getLogger(__name__)


def format_currency(amount: Decimal, currency: str = '₦') -> str:
    """
    Format a decimal amount as currency.
    
    Args:
        amount: The amount to format
        currency: Currency symbol (default: Nigerian Naira)
        
    Returns:
        Formatted currency string
    """
    return f"{currency}{amount:,.2f}"


def generate_receipt_number(estate_id: str, payment_id: str) -> str:
    """
    Generate a unique receipt number.
    
    Args:
        estate_id: The estate UUID
        payment_id: The payment UUID
        
    Returns:
        Formatted receipt number
    """
    estate_short = str(estate_id).split('-')[0].upper()
    payment_short = str(payment_id).split('-')[0].upper()
    return f"REC-{estate_short}-{payment_short}"


def sanitize_unit_identifier(identifier: str) -> str:
    """
    Sanitize and format a unit identifier.
    
    Args:
        identifier: Raw unit identifier
        
    Returns:
        Cleaned identifier
    """
    return identifier.strip().upper()

