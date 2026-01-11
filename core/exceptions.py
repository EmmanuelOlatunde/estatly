
# core/exceptions.py
"""
Custom exceptions for the Estatly system.
"""


class EstateContextError(Exception):
    """Raised when estate context is missing or invalid."""
    pass


class InsufficientPermissionsError(Exception):
    """Raised when user lacks required permissions."""
    pass


class PaymentError(Exception):
    """Raised when payment operations fail."""
    pass


class MaintenanceError(Exception):
    """Raised when maintenance operations fail."""
    pass

