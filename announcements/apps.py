# announcements/apps.py

from django.apps import AppConfig


class AnnouncementsConfig(AppConfig):
    """Configuration for the announcements app."""
    
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'announcements'
    verbose_name = 'Estate Announcements'
    
    def ready(self):
        """Import signals when app is ready."""
        try:
            import announcements.signals  # noqa
        except ImportError:
            pass