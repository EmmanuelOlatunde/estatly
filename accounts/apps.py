# accounts/apps.py
"""
App configuration for accounts app.
"""

from django.apps import AppConfig


class AccountsConfig(AppConfig):
    """Configuration for accounts app."""

    default_auto_field = 'django.db.models.BigAutoField'
    name = 'accounts'
    verbose_name = 'Accounts'

    def ready(self):
        """
        Import signals when app is ready.

        This method is called when Django starts.
        """
        pass