
# core/constants.py
"""
Shared constants and enums for the Estatly MVP.
"""

from django.db import models


class EstateType(models.TextChoices):
    """Types of estates supported in MVP."""
    GOVERNMENT = 'GOVERNMENT', 'Government Estate'
    PRIVATE = 'PRIVATE', 'Private Estate'


class FeeFrequency(models.TextChoices):
    """Fee payment frequency options."""
    MONTHLY = 'MONTHLY', 'Monthly'
    YEARLY = 'YEARLY', 'Yearly'


class PaymentMethod(models.TextChoices):
    """Payment methods supported in MVP."""
    BANK_TRANSFER = 'BANK_TRANSFER', 'Bank Transfer'
    CASH = 'CASH', 'Cash'


class PaymentStatus(models.TextChoices):
    """Payment status options."""
    UNPAID = 'UNPAID', 'Unpaid'
    PAID = 'PAID', 'Paid'


class MaintenanceCategory(models.TextChoices):
    """Categories for maintenance tickets."""
    WATER = 'WATER', 'Water'
    ELECTRICITY = 'ELECTRICITY', 'Electricity'
    SECURITY = 'SECURITY', 'Security'
    WASTE = 'WASTE', 'Waste'
    OTHER = 'OTHER', 'Other'


class MaintenanceStatus(models.TextChoices):
    """Status options for maintenance tickets."""
    OPEN = 'OPEN', 'Open'
    RESOLVED = 'RESOLVED', 'Resolved'

