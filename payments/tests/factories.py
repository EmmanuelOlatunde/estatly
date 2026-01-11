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

fake = Faker()


class UserFactory(DjangoModelFactory):
    """Factory for User model."""
    
    class Meta:
        model = "auth.User"
    
    username = factory.Sequence(lambda n: f"user{n}")
    email = factory.LazyAttribute(lambda obj: f"{obj.username}@example.com")
    first_name = factory.Faker("first_name")
    last_name = factory.Faker("last_name")
    is_active = True
    is_staff = False
    is_superuser = False
    
    @factory.lazy_attribute
    def is_estate_manager(self):
        """Add is_estate_manager attribute for permission checks."""
        return True


class EstateFactory(DjangoModelFactory):
    """Factory for Estate model."""
    
    class Meta:
        model = "estates.Estate"
    
    name = factory.Faker("company")
    address = factory.Faker("address")
    created_by = factory.SubFactory(UserFactory)


class UnitFactory(DjangoModelFactory):
    """Factory for Unit model."""
    
    class Meta:
        model = "units.Unit"
    
    unit_number = factory.Sequence(lambda n: f"UNIT-{n:03d}")
    address = factory.Faker("street_address")
    estate = factory.SubFactory(EstateFactory)


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
    estate = factory.SubFactory(EstateFactory)
    created_by = factory.SubFactory(UserFactory)


class FeeAssignmentFactory(DjangoModelFactory):
    """Factory for FeeAssignment model."""
    
    class Meta:
        model = "payments.FeeAssignment"
    
    fee = factory.SubFactory(FeeFactory)
    unit = factory.SubFactory(UnitFactory)
    status = "unpaid"


class PaymentFactory(DjangoModelFactory):
    """Factory for Payment model."""
    
    class Meta:
        model = "payments.Payment"
    
    fee_assignment = factory.SubFactory(FeeAssignmentFactory)
    amount = factory.LazyAttribute(lambda obj: obj.fee_assignment.fee.amount)
    payment_method = factory.Iterator(["bank_transfer", "cash"])
    payment_date = factory.LazyFunction(timezone.now)
    reference_number = factory.Sequence(lambda n: f"REF-{n:06d}")
    notes = factory.Faker("sentence")
    recorded_by = factory.SubFactory(UserFactory)


class ReceiptFactory(DjangoModelFactory):
    """Factory for Receipt model."""
    
    class Meta:
        model = "payments.Receipt"
    
    receipt_number = factory.Sequence(
        lambda n: f"RCP-{timezone.now().strftime('%Y%m%d')}-{n:06d}"
    )
    payment = factory.SubFactory(PaymentFactory)
    estate_name = factory.LazyAttribute(
        lambda obj: obj.payment.fee_assignment.fee.estate.name
    )
    unit_identifier = factory.LazyAttribute(
        lambda obj: obj.payment.fee_assignment.unit.unit_number
    )
    fee_name = factory.LazyAttribute(
        lambda obj: obj.payment.fee_assignment.fee.name
    )
    amount = factory.LazyAttribute(lambda obj: obj.payment.amount)
    payment_date = factory.LazyAttribute(lambda obj: obj.payment.payment_date)
    payment_method = factory.LazyAttribute(
        lambda obj: obj.payment.get_payment_method_display()
    )