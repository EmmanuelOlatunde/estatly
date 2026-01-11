# tests/factories.py
"""
Factory Boy factories for accounts app models.
"""

import factory
from factory.django import DjangoModelFactory
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import timedelta

User = get_user_model()


class UserFactory(DjangoModelFactory):
    """Factory for User model."""

    class Meta:
        model = User
        skip_postgeneration_save = True

    email = factory.Sequence(lambda n: f'user{n}@example.com')
    first_name = factory.Faker('first_name')
    last_name = factory.Faker('last_name')
    role = User.Role.ESTATE_MANAGER
    is_active = True
    is_staff = False
    is_superuser = False

    @factory.post_generation
    def password(obj, create, extracted, **kwargs):
        """Set password for user."""
        if not create:
            return
        password = extracted if extracted else 'TestPassword123!'
        obj.set_password(password)
        obj.save()


class PasswordResetTokenFactory(DjangoModelFactory):
    """Factory for PasswordResetToken model."""

    class Meta:
        model = 'accounts.PasswordResetToken'

    user = factory.SubFactory(UserFactory)
    token = factory.Faker('sha256')
    expires_at = factory.LazyFunction(lambda: timezone.now() + timedelta(hours=24))
    used = False