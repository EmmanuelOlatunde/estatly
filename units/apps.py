"""
App configuration for units app.
"""

from django.apps import AppConfig


class UnitsConfig(AppConfig):
    """Configuration for the units app."""
    
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'units'
    verbose_name = 'Property Units'
    
    def ready(self):
        """Import signals when app is ready."""
        # Import signals here if needed in future
        pass