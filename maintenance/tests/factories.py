# tests/factories.py

"""
Factory Boy factories for maintenance app models.

Provides factories for creating test data with realistic, varied values.
"""

import factory
from factory.django import DjangoModelFactory
from faker import Faker
from django.contrib.auth import get_user_model
from units.models import Unit
from estates.models import Estate 

User = get_user_model()
fake = Faker() 


class UserFactory(DjangoModelFactory):
    """Factory for creating test users."""
    
    class Meta:
        model = User
        skip_postgeneration_save=True
    
    email = factory.Sequence(lambda n: f"user{n}@example.com")
    first_name = factory.Faker("first_name")
    last_name = factory.Faker("last_name")
    is_active = True
    is_staff = False
    is_superuser = False
    password = factory.PostGenerationMethodCall('set_password', 'testpass123')


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



class MaintenanceTicketFactory(DjangoModelFactory):
    """Factory for creating test maintenance tickets."""
    
    class Meta:
        model = "maintenance.MaintenanceTicket"
    
    title = factory.Faker("sentence", nb_words=6)
    description = factory.Faker("paragraph", nb_sentences=3)
    category = factory.Iterator(['WATER', 'ELECTRICITY', 'SECURITY', 'WASTE', 'OTHER'])
    status = 'OPEN'
    created_by = factory.SubFactory(UserFactory)
    estate = factory.SubFactory(EstateFactory)
    unit = None
    resolved_at = None