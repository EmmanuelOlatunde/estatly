"""
Factory Boy factories for units app models.

Provides factories for creating test data with realistic values.
"""

import factory
from factory.django import DjangoModelFactory
from django.contrib.auth import get_user_model
from units.models import Unit
from estates.models import Estate  

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
    def password(self, create, extracted, **kwargs):
        """Set password for the user."""
        if create:
            self.set_password(extracted or "testpass123")

class EstateFactory(DjangoModelFactory):
    """Factory for Estate model."""

    class Meta:
        model = Estate

    name = factory.Faker("company")
    estate_type = factory.Iterator(
        Estate.EstateType.choices, getter=lambda c: c[0]
    )
    approximate_units = factory.Faker("random_int", min=10, max=100)
    fee_frequency = factory.Iterator(
        Estate.FeeFrequency.choices, getter=lambda c: c[0]
    )
    is_active = True


class UnitFactory(DjangoModelFactory):
    """Factory for creating Unit instances."""
    
    class Meta:
        model = Unit
    
    identifier = factory.Sequence(lambda n: f"Unit {n}")
    unit_type = factory.Iterator([
        Unit.UnitType.HOUSE,
        Unit.UnitType.FLAT,
        Unit.UnitType.APARTMENT,
        Unit.UnitType.STUDIO,
    ])
    estate = factory.SubFactory(EstateFactory)  # <-- Key fix: Auto-create and link an Estate
    owner = factory.SubFactory(UserFactory)
    occupant_name = None
    occupant_phone = None
    description = factory.Faker("text", max_nb_chars=200)
    is_occupied = False
    is_active = True


class OccupiedUnitFactory(UnitFactory):
    """Factory for creating occupied units with occupant information."""
    
    is_occupied = True
    occupant_name = factory.Faker("name")
    occupant_phone = factory.Sequence(lambda n: f"+12345678{n:02d}")


class VacantUnitFactory(UnitFactory):
    """Factory for creating vacant units."""
    
    is_occupied = False
    occupant_name = None
    occupant_phone = None


class InactiveUnitFactory(UnitFactory):
    """Factory for creating inactive units."""
    
    is_active = False