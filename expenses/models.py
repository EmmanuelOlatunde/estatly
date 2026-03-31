import uuid
from django.db import models
from django.conf import settings


class Expense(models.Model):

    class Category(models.TextChoices):
        WATER = "water", "Water"
        ELECTRICITY = "electricity", "Electricity"
        SECURITY = "security", "Security"
        WASTE = "waste", "Waste"
        OTHER = "other", "Other"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    estate = models.ForeignKey(
        "estates.Estate",
        on_delete=models.CASCADE,
        related_name="expenses"
    )

    title = models.CharField(max_length=255)
    amount = models.DecimalField(max_digits=12, decimal_places=2)

    category = models.CharField(
        max_length=20,
        choices=Category.choices,
        default=Category.OTHER
    )

    description = models.TextField(blank=True)
    date = models.DateField()  # when the money was ACTUALLY spent

    recorded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name="recorded_expenses"
    )

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-date", "-created_at"]

    def __str__(self):
        return f"{self.title} — ₦{self.amount}"