# reports/tests/test_serializers.py
"""
Tests for reports app serializers.

Coverage:
- Field validation
- Serialization output
- Required fields
- Data types
"""

import pytest
from decimal import Decimal
from datetime import date
from reports.serializers import (
    UnpaidUnitSerializer,
    FeePaymentStatusSerializer,
    FeeSummarySerializer,
    OverallPaymentSummarySerializer
)
import uuid


@pytest.mark.django_db
class TestUnpaidUnitSerializer:
    """Test UnpaidUnitSerializer."""
    
    def test_serializer_contains_expected_fields(self):
        """Test serializer has all expected fields."""
        data = {
            'unit_id': uuid.uuid4(),
            'unit_name': 'Unit 101',
            'tenant_id': uuid.uuid4(),
            'tenant_name': 'John Doe',
            'tenant_email': 'john@example.com',
            'estate_name': 'Sunset Apartments',
            'estate_id': uuid.uuid4(),
            'amount_due': Decimal('1000.00'),
            'due_date': date.today(),
            'days_overdue': 5
        }
        
        serializer = UnpaidUnitSerializer(data)
        
        assert 'unit_id' in serializer.data
        assert 'unit_name' in serializer.data
        assert 'tenant_name' in serializer.data
        assert 'tenant_email' in serializer.data
        assert 'amount_due' in serializer.data
        assert 'days_overdue' in serializer.data
    
    def test_serializer_handles_null_tenant(self):
        """Test serializer handles vacant units correctly."""
        data = {
            'unit_id': uuid.uuid4(),
            'unit_name': 'Unit 102',
            'tenant_id': None,
            'tenant_name': 'Vacant',
            'tenant_email': '',
            'estate_name': 'Sunset Apartments',
            'estate_id': uuid.uuid4(),
            'amount_due': Decimal('1000.00'),
            'due_date': date.today(),
            'days_overdue': 0
        }
        
        serializer = UnpaidUnitSerializer(data)
        
        assert serializer.data['tenant_id'] is None
        assert serializer.data['tenant_name'] == 'Vacant'


@pytest.mark.django_db
class TestFeePaymentStatusSerializer:
    """Test FeePaymentStatusSerializer."""
    
    def test_serializer_contains_all_required_fields(self):
        """Test serializer has all required fields."""
        data = {
            'fee_id': uuid.uuid4(),
            'fee_name': 'Monthly Rent',
            'fee_type': 'monthly',
            'total_expected': Decimal('10000.00'),
            'total_collected': Decimal('7000.00'),
            'total_pending': Decimal('3000.00'),
            'payment_rate': Decimal('70.00'),
            'total_units': 10,
            'paid_units': 7,
            'unpaid_units_count': 3,
            'unpaid_units': []
        }
        
        serializer = FeePaymentStatusSerializer(data)
        
        required_fields = [
            'fee_id', 'fee_name', 'fee_type', 'total_expected',
            'total_collected', 'total_pending', 'payment_rate',
            'total_units', 'paid_units', 'unpaid_units_count', 'unpaid_units'
        ]
        
        for field in required_fields:
            assert field in serializer.data
    
    def test_serializer_decimal_fields_formatted_correctly(self):
        """Test decimal fields are formatted correctly."""
        data = {
            'fee_id': uuid.uuid4(),
            'fee_name': 'Security Deposit',
            'fee_type': 'one_time',
            'total_expected': Decimal('5000.50'),
            'total_collected': Decimal('5000.50'),
            'total_pending': Decimal('0.00'),
            'payment_rate': Decimal('100.00'),
            'total_units': 5,
            'paid_units': 5,
            'unpaid_units_count': 0,
            'unpaid_units': []
        }
        
        serializer = FeePaymentStatusSerializer(data)
        
        assert serializer.data['total_expected'] == '5000.50'
        assert serializer.data['payment_rate'] == '100.00'


@pytest.mark.django_db
class TestFeeSummarySerializer:
    """Test FeeSummarySerializer."""
    
    def test_serializer_outputs_summary_without_unpaid_list(self):
        """Test serializer provides summary without detailed unpaid list."""
        data = {
            'fee_id': uuid.uuid4(),
            'fee_name': 'Water Bill',
            'fee_type': 'monthly',
            'total_expected': Decimal('2000.00'),
            'total_collected': Decimal('1500.00'),
            'total_pending': Decimal('500.00'),
            'payment_rate': Decimal('75.00'),
            'total_units': 10,
            'paid_units': 7,
            'unpaid_units_count': 3
        }
        
        serializer = FeeSummarySerializer(data)
        
        assert 'unpaid_units' not in serializer.data
        assert serializer.data['unpaid_units_count'] == 3


@pytest.mark.django_db
class TestOverallPaymentSummarySerializer:
    """Test OverallPaymentSummarySerializer."""
    
    def test_serializer_contains_aggregate_fields(self):
        """Test serializer has all aggregate fields."""
        data = {
            'total_fees': 5,
            'total_expected_all_fees': Decimal('50000.00'),
            'total_collected_all_fees': Decimal('35000.00'),
            'total_pending_all_fees': Decimal('15000.00'),
            'overall_payment_rate': Decimal('70.00'),
            'fees_summary': []
        }
        
        serializer = OverallPaymentSummarySerializer(data)
        
        assert serializer.data['total_fees'] == 5
        assert serializer.data['overall_payment_rate'] == '70.00'
        assert isinstance(serializer.data['fees_summary'], list)
    
    def test_serializer_handles_empty_fees_summary(self):
        """Test serializer handles no fees correctly."""
        data = {
            'total_fees': 0,
            'total_expected_all_fees': Decimal('0.00'),
            'total_collected_all_fees': Decimal('0.00'),
            'total_pending_all_fees': Decimal('0.00'),
            'overall_payment_rate': Decimal('0.00'),
            'fees_summary': []
        }
        
        serializer = OverallPaymentSummarySerializer(data)
        
        assert serializer.data['total_fees'] == 0
        assert len(serializer.data['fees_summary']) == 0