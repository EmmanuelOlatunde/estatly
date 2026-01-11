# payments/apps.py

from django.apps import AppConfig


class PaymentsConfig(AppConfig):
    """Configuration for the payments app."""
    
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'payments'
    verbose_name = 'Payments & Fees'
    
    def ready(self):
        """Import signals when app is ready."""
        try:
            import payments.signals
        except ImportError:
            pass