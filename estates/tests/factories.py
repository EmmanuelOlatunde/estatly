
# tests/factories.py
"""
Factory Boy factories for estates app models.
"""

import factory
from factory.django import DjangoModelFactory
from django.contrib.auth import get_user_model
from estates.models import Estate

User = get_user_model()


class UserFactory(DjangoModelFactory):
    """Factory for custom email-based User model."""

    class Meta:
        model = User

    email = factory.Sequence(lambda n: f"user{n}@example.com")
    first_name = factory.Faker("first_name")
    last_name = factory.Faker("last_name")
    is_active = True
    is_staff = False
    is_superuser = False

    password = factory.PostGenerationMethodCall(
        "set_password",
        "testpass123"
    )

class EstateFactory(DjangoModelFactory):
    """Factory for Estate model."""
    
    class Meta:
        model = Estate
    
    name = factory.Sequence(lambda n: f"Estate {n}")
    estate_type = factory.Iterator([Estate.EstateType.PRIVATE, Estate.EstateType.GOVERNMENT])
    approximate_units = factory.Faker("random_int", min=10, max=500)
    fee_frequency = factory.Iterator([Estate.FeeFrequency.MONTHLY, Estate.FeeFrequency.YEARLY])
    is_active = True
    description = factory.Faker("text", max_nb_chars=200)
    address = factory.Faker("address")