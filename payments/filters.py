# payments/filters.py

"""
Filter classes for the payments app.

Provides filtering capabilities for fees, payments, and assignments.
"""

import django_filters
from .models import Fee, FeeAssignment, Payment


class FeeFilter(django_filters.FilterSet):
    """Filter for Fee model."""
    
    estate = django_filters.UUIDFilter(field_name='estate__id')
    due_date_from = django_filters.DateFilter(field_name='due_date', lookup_expr='gte')
    due_date_to = django_filters.DateFilter(field_name='due_date', lookup_expr='lte')
    amount_min = django_filters.NumberFilter(field_name='amount', lookup_expr='gte')
    amount_max = django_filters.NumberFilter(field_name='amount', lookup_expr='lte')
    created_by = django_filters.UUIDFilter(field_name='created_by__id')
    
    class Meta:
        model = Fee
        fields = ['estate', 'due_date_from', 'due_date_to', 'amount_min', 'amount_max', 'created_by']


class FeeAssignmentFilter(django_filters.FilterSet):
    """Filter for FeeAssignment model."""
    
    fee = django_filters.UUIDFilter(field_name='fee__id')
    unit = django_filters.UUIDFilter(field_name='unit__id')
    estate = django_filters.UUIDFilter(field_name='fee__estate__id')
    status = django_filters.ChoiceFilter(choices=FeeAssignment.PaymentStatus.choices)
    
    class Meta:
        model = FeeAssignment
        fields = ['fee', 'unit', 'estate', 'status']


class PaymentFilter(django_filters.FilterSet):
    """Filter for Payment model."""
    
    fee_assignment = django_filters.UUIDFilter(field_name='fee_assignment__id')
    fee = django_filters.UUIDFilter(field_name='fee_assignment__fee__id')
    unit = django_filters.UUIDFilter(field_name='fee_assignment__unit__id')
    estate = django_filters.UUIDFilter(field_name='fee_assignment__fee__estate__id')
    payment_method = django_filters.ChoiceFilter(choices=Payment.PaymentMethod.choices)
    payment_date_from = django_filters.DateTimeFilter(field_name='payment_date', lookup_expr='gte')
    payment_date_to = django_filters.DateTimeFilter(field_name='payment_date', lookup_expr='lte')
    recorded_by = django_filters.UUIDFilter(field_name='recorded_by__id')
    
    class Meta:
        model = Payment
        fields = [
            'fee_assignment',
            'fee',
            'unit',
            'estate',
            'payment_method',
            'payment_date_from',
            'payment_date_to',
            'recorded_by',
        ]