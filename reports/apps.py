# reports/apps.py
"""
App configuration for reports application.
"""

from django.apps import AppConfig


class ReportsConfig(AppConfig):
    """Configuration for the reports app."""
    
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'reports'
    verbose_name = 'Reports'
    
    def ready(self):
        """Initialize app when Django starts."""
        pass  # No signals needed for this app