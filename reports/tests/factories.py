# reports/tests/factories.py
"""
Factory Boy factories for creating test data.

Provides factories for User, Estate, Unit, Fee, and Payment models.
"""

import factory
from factory.django import DjangoModelFactory
from faker import Faker
from decimal import Decimal
from datetime import date, timedelta
from accounts.models import User  
from estates.models import Estate
from units.models import Unit
from announcements.models import Announcement
from payments.models import Fee, Payment, FeeAssignment
from django.utils import timezone


fake = Faker()



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


    
    @factory.post_generation
    def role(obj, create, extracted, **kwargs):
        """Set role after creation."""
        if extracted:
            if hasattr(obj, 'role'):
                obj.role = extracted
                if create:
                    obj.save()

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

class FeeFactory(DjangoModelFactory):
    """Factory for Fee model."""
    
    class Meta:
        model = "payments.Fee"
    
    name = factory.Sequence(lambda n: f"Fee {n} - {fake.catch_phrase()}")
    description = factory.Faker("text", max_nb_chars=200)
    amount = factory.LazyFunction(lambda: Decimal(fake.random_int(min=1000, max=50000)))
    due_date = factory.LazyFunction(
        lambda: (timezone.now() + timedelta(days=30)).date()
    )
    estate = factory.LazyFunction(lambda: Estate.objects.first() or EstateFactory())
    created_by = factory.SubFactory(UserFactory)



class FeeAssignmentFactory(DjangoModelFactory):
    """Factory for FeeAssignment model."""
    
    class Meta:
        model = "payments.FeeAssignment"
    
    fee = factory.SubFactory(FeeFactory)
    unit = factory.LazyFunction(
        lambda: Unit.objects.filter(estate=FeeFactory().estate).first() 
        or UnitFactory(estate=FeeFactory().estate)
    )
    status = "unpaid"

class PaymentFactory(DjangoModelFactory):
    class Meta:
        model = "payments.Payment"
        skip_postgeneration_save = True

    fee_assignment = factory.SubFactory(FeeAssignmentFactory)
    amount = factory.LazyAttribute(lambda o: o.fee_assignment.fee.amount)
    payment_method = factory.Faker('random_element', elements=['bank_transfer', 'cash'])
    payment_date = factory.LazyFunction(timezone.now)  # ✅ FIX
    reference_number = factory.Faker('pystr', max_chars=20)
    recorded_by = factory.LazyFunction(
        lambda: User.objects.filter(role='ESTATE_MANAGER').first() or UserFactory()
    )
    
    @factory.post_generation
    def mark_assignment_paid(self, create, extracted, **kwargs):
        if not create:
            return
        self.fee_assignment.status = FeeAssignment.PaymentStatus.PAID
        self.fee_assignment.save()

class AnnouncementFactory(DjangoModelFactory):
    """Factory for creating Announcement instances."""
    
    class Meta:
        model = Announcement
    
    title = factory.Faker("sentence", nb_words=6)
    message = factory.Faker("paragraph", nb_sentences=5)
    created_by = factory.SubFactory(UserFactory, is_staff=True)
    is_active = True

