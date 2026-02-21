# estates/admin.py

from django import forms
from django.contrib import admin
from django.db.models import Q
from accounts.models import User
from .models import Estate


class EstateAdminForm(forms.ModelForm):
    manager = forms.ModelChoiceField(
        queryset=User.objects.filter(
            role=User.Role.ESTATE_MANAGER,
            estate__isnull=True
        ),
        required=True,
        help_text="Assign an estate manager (only unassigned managers shown)"
    )

    class Meta:
        model = Estate
        fields = "__all__"


@admin.register(Estate)
class EstateAdmin(admin.ModelAdmin):
    form = EstateAdminForm

    list_display = [
        'name',
        'manager',          # direct field — no custom method needed
        'estate_type',
        'approximate_units',
        'total_units',
        'active_units',
        'fee_frequency',
        'is_active',
        'created_at',
    ]

    list_filter = ['estate_type', 'fee_frequency', 'is_active', 'created_at']
    search_fields = ['name', 'description', 'address']
    readonly_fields = ['id', 'created_at', 'updated_at']

    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'estate_type', 'description')
        }),
        ('Details', {
            'fields': ('approximate_units', 'fee_frequency', 'address')
        }),
        ('Assignment', {
            'fields': ('manager',)
        }),
        ('Status', {
            'fields': ('is_active',)
        }),
        ('System Information', {
            'fields': ('id', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    ordering = ['-created_at']
    actions = ['activate_estates', 'deactivate_estates']

    def activate_estates(self, request, queryset):
        updated = queryset.update(is_active=True)
        self.message_user(request, f'{updated} estate(s) activated successfully.')
    activate_estates.short_description = 'Activate selected estates'

    def deactivate_estates(self, request, queryset):
        updated = queryset.update(is_active=False)
        self.message_user(request, f'{updated} estate(s) deactivated successfully.')
    deactivate_estates.short_description = 'Deactivate selected estates'

    def total_units(self, obj):
        return obj.total_units
    total_units.short_description = 'Total Units'

    def active_units(self, obj):
        return obj.active_units
    active_units.short_description = 'Active Units'

    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)
        if obj:
            # When editing, include the current manager in the queryset
            # even though they're already assigned
            form.base_fields['manager'].queryset = User.objects.filter(
                role=User.Role.ESTATE_MANAGER
            ).filter(
                Q(estate__isnull=True) | Q(estate=obj)
            )
            form.base_fields['manager'].initial = obj.manager
        return form

    def save_model(self, request, obj, form, change):
        # Estate.manager is a direct OneToOneField on Estate.
        # Django handles the assignment automatically when the form saves.
        # No manual user.estate reassignment needed.
        super().save_model(request, obj, form, change)