# payments/admin.py

"""
Django admin configuration for the payments app.

Provides admin interface for managing fees, payments, and receipts.
"""

from django.contrib import admin
from django.utils.html import format_html
from .models import Fee, FeeAssignment, Payment, Receipt


@admin.register(Fee)
class FeeAdmin(admin.ModelAdmin):
    """Admin interface for Fee model."""
    
    list_display = [
        'name',
        'amount',
        'due_date',
        'estate',
        'created_by',
        'assigned_units_count',
        'paid_count',
        'created_at',
    ]
    list_filter = ['due_date', 'created_at', 'estate']
    search_fields = ['name', 'description', 'estate__name']
    readonly_fields = ['id', 'created_at', 'updated_at']
    date_hierarchy = 'due_date'
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('id', 'name', 'description', 'amount', 'due_date')
        }),
        ('Relationships', {
            'fields': ('estate', 'created_by')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def assigned_units_count(self, obj):
        """Display count of assigned units."""
        return obj.fee_assignments.count()
    assigned_units_count.short_description = 'Units Assigned'
    
    def paid_count(self, obj):
        """Display count of paid assignments with color coding."""
        paid = obj.total_paid_count
        total = obj.total_assigned_units
        color = 'green' if paid == total else 'orange' if paid > 0 else 'red'
        return format_html(
            '<span style="color: {};">{}/{}</span>',
            color,
            paid,
            total
        )
    paid_count.short_description = 'Paid/Total'


class FeeAssignmentInline(admin.TabularInline):
    """Inline for viewing fee assignments."""
    
    model = FeeAssignment
    extra = 0
    readonly_fields = ['id', 'status', 'created_at']
    can_delete = False


@admin.register(FeeAssignment)
class FeeAssignmentAdmin(admin.ModelAdmin):
    """Admin interface for FeeAssignment model."""
    
    list_display = [
        'fee',
        'unit',
        'status',
        'has_payment',
        'created_at',
    ]
    list_filter = ['status', 'created_at', 'fee__estate']
    search_fields = [
        'fee__name',
        'unit__identifier',
        'unit__address',
    ]
    readonly_fields = ['id', 'created_at', 'updated_at']
    
    fieldsets = (
        ('Assignment Details', {
            'fields': ('id', 'fee', 'unit', 'status')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def has_payment(self, obj):
        """Check if assignment has a payment."""
        return hasattr(obj, 'payment')
    has_payment.boolean = True
    has_payment.short_description = 'Paid'


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    """Admin interface for Payment model."""
    
    list_display = [
        'get_fee_name',
        'get_unit',
        'fee_assignment',
        'amount',
        'payment_method',
        'payment_date',
        'recorded_by',
        'has_receipt',
    ]
    list_filter = [
        'payment_method',
        'payment_date',
        'created_at',
    ]
    search_fields = [
        'reference_number',
        'fee_assignment__fee__name',
        'fee_assignment__unit__identifier',
    ]
    readonly_fields = [
        'id',
        
        'created_at',
        'updated_at',
    ]
    date_hierarchy = 'payment_date'
    
    fieldsets = (
        ('Payment Details', {
            'fields': (
                'id',
                'fee_assignment',
                'amount',
                'payment_method',
                'payment_date',
            )
        }),
        ('Additional Information', {
            'fields': ('reference_number', 'notes', 'recorded_by')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def get_fee_name(self, obj):
        """Get fee name from assignment."""
        return obj.fee_assignment.fee.name
    get_fee_name.short_description = 'Fee'
    get_fee_name.admin_order_field = 'fee_assignment__fee__name'
    
    def get_unit(self, obj):
        """Get unit from assignment."""
        return obj.fee_assignment.unit.identifier
    get_unit.short_description = 'Unit'
    get_unit.admin_order_field = 'fee_assignment__unit__identifier'
    
    def has_receipt(self, obj):
        """Check if payment has a receipt."""
        return hasattr(obj, 'receipt')
    has_receipt.boolean = True
    has_receipt.short_description = 'Receipt'


@admin.register(Receipt)
class ReceiptAdmin(admin.ModelAdmin):
    """Admin interface for Receipt model."""
    
    list_display = [
        'receipt_number',
        'fee_name',
        'unit_identifier',
        'amount',
        'payment_date',
        'issued_at',
    ]
    list_filter = ['issued_at', 'payment_date']
    search_fields = [
        'receipt_number',
        'fee_name',
        'unit_identifier',
        'estate_name',
    ]
    readonly_fields = [
        'id',
        'receipt_number',
        'payment',
        'estate_name',
        'unit_identifier',
        'fee_name',
        'amount',
        'payment_date',
        'payment_method',
        'issued_at',
    ]
    
    fieldsets = (
        ('Receipt Information', {
            'fields': (
                'id',
                'receipt_number',
                'payment',
                'issued_at',
            )
        }),
        ('Payment Details (Cached)', {
            'fields': (
                'estate_name',
                'unit_identifier',
                'fee_name',
                'amount',
                'payment_date',
                'payment_method',
            )
        }),
    )
    
    def has_add_permission(self, request):
        """Disable manual receipt creation."""
        return False
    
    def has_delete_permission(self, request, obj=None):
        """Disable receipt deletion."""
        return False