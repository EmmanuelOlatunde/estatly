# estate/admin.py
"""
Django admin configuration for estate app.
"""

from django import forms
from django.contrib import admin
from accounts.models import User
from .models import Estate



class EstateAdminForm(forms.ModelForm):
    """
    Admin form to allow assigning ONE estate manager during estate creation.
    """

    manager = forms.ModelChoiceField(
        queryset=User.objects.filter(role=User.Role.ESTATE_MANAGER),
        required=False,
        # estate__isnull=True,
        help_text="Assign an estate manager to this estate"
    )

    class Meta:
        model = Estate
        fields = "__all__"


@admin.register(Estate)
class EstateAdmin(admin.ModelAdmin):
    """Admin interface for Estate model."""
    form = EstateAdminForm

    list_display = [
        'name',
        'manager',

        'estate_type',
        'approximate_units',
        'total_units',        # 👈 total units
        'active_units',       # 👈 active units
        'fee_frequency',
        'is_active',
        'created_at',
    ]
    
    list_filter = [
        'estate_type',
        'fee_frequency',
        'is_active',
        'created_at',
    ]
    
    search_fields = [
        'name',
        'description',
        'address',
    ]
    
    readonly_fields = [
        'id',
        'created_at',
        'updated_at',
    ]
    
    fieldsets = (
        ('Basic Information', {
            'fields': (
                'name',
                'estate_type',
                'description',
            )
        }),
        ('Details', {
            'fields': (
                'approximate_units',
                'fee_frequency',
                'address',
            )
        }),
        ('Assignment', {
            'fields': (
                'manager',
            )
        }),

        ('Status', {
            'fields': (
                'is_active',
            )
        }),
        ('System Information', {
            'fields': (
                'id',
                'created_at',
                'updated_at',
            ),
            'classes': ('collapse',)
        }),
    )
    
    ordering = ['-created_at']
    
    actions = ['activate_estates', 'deactivate_estates']
    
    def activate_estates(self, request, queryset):
        """Bulk activate estates."""
        updated = queryset.update(is_active=True)
        self.message_user(
            request,
            f'{updated} estate(s) activated successfully.'
        )
    activate_estates.short_description = 'Activate selected estates'
    
    def deactivate_estates(self, request, queryset):
        """Bulk deactivate estates."""
        updated = queryset.update(is_active=False)
        self.message_user(
            request,
            f'{updated} estate(s) deactivated successfully.'
        )
    deactivate_estates.short_description = 'Deactivate selected estates'
    

    # Add methods to expose properties in admin
    def total_units(self, obj):
        return obj.total_units
    total_units.short_description = 'Total Units'

    def active_units(self, obj):
        return obj.active_units
    active_units.short_description = 'Active Units'

    def manager(self, obj):
        try:
            return obj.user.email
        except User.DoesNotExist:
            return "—"

    manager.short_description = "Estate Manager"

    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)

        new_manager = form.cleaned_data.get("manager")

        # Remove old manager if exists
        try:
            old_manager = obj.user
        except User.DoesNotExist:
            old_manager = None

        if old_manager and old_manager != new_manager:
            old_manager.estate = None
            old_manager.save(update_fields=["estate"])

        if new_manager:
            new_manager.estate = obj
            new_manager.save(update_fields=["estate"])

