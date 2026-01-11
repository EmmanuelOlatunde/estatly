# estates/apps.py
"""
App configuration for estates application.
"""

from django.apps import AppConfig


class EstatesConfig(AppConfig):
    """Configuration for the Estates app."""
    
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'estates'
    verbose_name = 'Estate Management'

    def ready(self):
        """Import signals when app is ready."""
        try:
            import estates.signals  # noqa
        except ImportError:
            pass
