from rest_framework import viewsets, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db.models import Sum

from .models import Expense
from .serializers import ExpenseSerializer, CreateExpenseSerializer


class ExpenseViewSet(viewsets.ModelViewSet):
    permission_classes = [permissions.IsAuthenticated]
    http_method_names = ["get", "post", "patch", "delete"]

    def get_queryset(self):
        qs = Expense.objects.filter(estate=self.request.user.estate)

        date_from = self.request.query_params.get("date_from")
        date_to   = self.request.query_params.get("date_to")

        if date_from:
            qs = qs.filter(date__gte=date_from)
        if date_to:
            qs = qs.filter(date__lte=date_to)

        return qs

    def get_serializer_class(self):
        if self.action == "create":
            return CreateExpenseSerializer
        return ExpenseSerializer

    def perform_create(self, serializer):
        serializer.save(
            estate=self.request.user.estate,
            recorded_by=self.request.user
        )

    @action(detail=False, methods=["get"], url_path="summary")
    def summary(self, request):
        queryset = self.get_queryset()

        total = queryset.aggregate(
            total=Sum("amount")
        )["total"] or 0

        by_category = queryset.values("category").annotate(
            total=Sum("amount")
        ).order_by("-total")

        return Response({
            "total_expenses": total,
            "by_category": list(by_category),
        })