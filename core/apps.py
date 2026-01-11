
# core/apps.py
"""
App configuration for core.
"""

from django.apps import AppConfig


class CoreConfig(AppConfig):
    """Configuration for the core app."""
    
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'core'
    verbose_name = 'Core System'

    def ready(self):
        """Initialize app when Django starts."""
        pass  # No signals needed in MVP


