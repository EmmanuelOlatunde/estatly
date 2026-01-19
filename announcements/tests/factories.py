# tests/factories.py

"""
Factory Boy factories for announcements app models.

Provides factories for creating test data with realistic values.
"""

import factory
from factory.django import DjangoModelFactory
from django.contrib.auth import get_user_model
from announcements.models import Announcement

User = get_user_model()




class UserFactory(DjangoModelFactory):
    """Factory for User model."""
    
    class Meta:
        model = User  # Use your custom User model
        skip_postgeneration_save = True
    
    email = factory.Sequence(lambda n: f"user{n}@example.com")
    first_name = factory.Faker("first_name")
    last_name = factory.Faker("last_name")
    is_active = True
    is_staff = False
    is_superuser = False
    
    @factory.post_generation
    def password(self, create, extracted, **kwargs):
        """Set password after user creation."""
        if not create:
            return
        self.set_password(extracted or 'testpass123')


class AnnouncementFactory(DjangoModelFactory):
    """Factory for creating Announcement instances."""
    
    class Meta:
        model = Announcement
    
    title = factory.Faker("sentence", nb_words=6)
    message = factory.Faker("paragraph", nb_sentences=5)
    created_by = factory.SubFactory(UserFactory, is_staff=True)
    is_active = True


class InactiveAnnouncementFactory(AnnouncementFactory):
    """Factory for creating inactive announcements."""
    
    is_active = False


class LongAnnouncementFactory(AnnouncementFactory):
    """Factory for creating announcements with long content."""
    
    title = factory.Faker("sentence", nb_words=20)
    message = factory.Faker("text", max_nb_chars=2000)


class ShortAnnouncementFactory(AnnouncementFactory):
    """Factory for creating announcements with minimal content."""
    
    title = "Min"
    message = "Short msg."