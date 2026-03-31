from rest_framework import serializers
from .models import Expense


class ExpenseSerializer(serializers.ModelSerializer):
    """
    Used for reading / listing expenses.
    Returns full detail including computed display fields.
    """
    category_display = serializers.CharField(
        source="get_category_display",
        read_only=True
    )
    recorded_by_name = serializers.SerializerMethodField()

    class Meta:
        model = Expense
        fields = [
            "id",
            "title",
            "amount",
            "category",
            "category_display",  # human-readable e.g. "Electricity"
            "description",
            "date",
            "recorded_by_name",
            "created_at",
        ]

    def get_recorded_by_name(self, obj):
        if obj.recorded_by:
            return obj.recorded_by.get_full_name() or obj.recorded_by.email
        return None


class CreateExpenseSerializer(serializers.ModelSerializer):
    """
    Used only for creating expenses.
    Intentionally minimal — estate + recorded_by come from request context.
    """
    class Meta:
        model = Expense
        fields = [
            "title",
            "amount",
            "category",
            "description",
            "date",
        ]

    def validate_amount(self, value):
        if value <= 0:
            raise serializers.ValidationError("Amount must be greater than zero.")
        return value