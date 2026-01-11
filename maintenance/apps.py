# maintenance/apps.py

"""
App configuration for maintenance app.
"""

from django.apps import AppConfig


class MaintenanceConfig(AppConfig):
    """Configuration for the maintenance app."""
    
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'maintenance'
    verbose_name = 'Maintenance & Issue Tracking'
    
    def ready(self):
        """
        Import signals when the app is ready.
        Currently no signals are needed for MVP.
        """
        pass