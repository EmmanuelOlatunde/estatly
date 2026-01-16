# tests/factories.py

"""
Factory Boy factories for payments app models.

Provides realistic test data generation for all models.
"""

import factory
from factory.django import DjangoModelFactory
from faker import Faker
from decimal import Decimal
from django.utils import timezone
from datetime import timedelta
from accounts.models import User  # Import your custom User model
from units.models import Unit
from estates.models import Estate 


fake = Faker()


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


class EstateManagerFactory(UserFactory):
    """Factory for estate manager users."""
    role = User.Role.ESTATE_MANAGER
    is_staff = False


class SuperAdminFactory(UserFactory):
    """Factory for super admin users."""
    role = User.Role.SUPER_ADMIN
    is_staff = True
    is_superuser = True


class EstateFactory(DjangoModelFactory):
    """Factory for Estate model."""
    
    class Meta:
        model = Estate
        skip_postgeneration_save = True

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
    """Factory for Unit model."""
    
    class Meta:
        model = Unit
        skip_postgeneration_save = True
    
    identifier = factory.Sequence(lambda n: f"Unit {n}")
    unit_type = factory.Iterator([
        Unit.UnitType.HOUSE,
        Unit.UnitType.FLAT,
        Unit.UnitType.APARTMENT,
        Unit.UnitType.STUDIO,
    ])
    estate = factory.SubFactory(EstateFactory)  
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


class ReceiptFactory(DjangoModelFactory):
    class Meta:
        model = "payments.Receipt"

    payment = factory.SubFactory(PaymentFactory)
    receipt_number = factory.Sequence(
        lambda n: f"RCP-{timezone.now().strftime('%Y%m%d')}-{n:06d}"
    )
    estate_name = factory.LazyAttribute(lambda o: o.payment.fee_assignment.fee.estate.name)
    unit_identifier = factory.LazyAttribute(lambda o: o.payment.fee_assignment.unit.identifier)
    fee_name = factory.LazyAttribute(lambda o: o.payment.fee_assignment.fee.name)
    amount = factory.LazyAttribute(lambda o: o.payment.amount)
    payment_date = factory.LazyAttribute(lambda o: o.payment.payment_date.date())  # ✅ FIX
    payment_method = factory.LazyAttribute(lambda o: o.payment.payment_method)

       

    @classmethod
    def _create(cls, model_class, *args, **kwargs):
        """
        Enforce one-receipt-per-payment.
        If a receipt already exists for this payment, reuse it.
        """
        payment = kwargs.get("payment")

        if payment is not None:
            receipt, _ = model_class.objects.get_or_create(
                payment=payment,
                defaults=kwargs,
            )
            return receipt

        return super()._create(model_class, *args, **kwargs)
