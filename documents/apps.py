"""
App configuration for documents app.
"""

from django.apps import AppConfig


class DocumentsConfig(AppConfig):
    """Configuration for the documents application."""
    
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'documents'
    verbose_name = 'Documents'
    
    def ready(self):
        """Import signals when app is ready."""
        try:
            import documents.signals  # noqa
        except ImportError:
            pass