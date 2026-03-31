from django.contrib import admin
from .models import Expense


@admin.register(Expense)
class ExpenseAdmin(admin.ModelAdmin):
    list_display = ["title", "amount", "category", "date", "estate", "recorded_by"]
    list_filter = ["category", "estate"]
    search_fields = ["title", "description"]
    ordering = ["-date"]