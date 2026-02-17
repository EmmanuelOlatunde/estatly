# estate/admin.py
"""
Django admin configuration for estate app.
"""

from django import forms
from django.contrib import admin
from accounts.models import User
from .models import Estate
from django.db import models



class EstateAdminForm(forms.ModelForm):
    """
    Admin form to allow assigning ONE estate manager during estate creation.
    """

    manager = forms.ModelChoiceField(
        queryset=User.objects.filter(role=User.Role.ESTATE_MANAGER, estate__isnull=True),
        required=False,
        help_text="Assign an estate manager to this estate (only unassigned managers are shown)"
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
        'total_units',        # total units
        'active_units',       # active units
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
        """
        Display the estate manager for this estate.
        
        Since User has FK to Estate (with related_name="users"),
        we access managers through the reverse relation.
        """
        # Get the first estate manager assigned to this estate
        manager = obj.users.filter(role=User.Role.ESTATE_MANAGER).first()
        
        if manager:
            return manager.email
        return "No manager assigned"

    manager.short_description = "Estate Manager"

    def get_form(self, request, obj=None, **kwargs):
        """
        Customize the form to show the current manager if editing an existing estate.
        """
        form = super().get_form(request, obj, **kwargs)
        
        if obj:
            # Pre-populate the manager field with the current manager
            current_manager = obj.users.filter(role=User.Role.ESTATE_MANAGER).first()
            if current_manager:
                # Update queryset to include current manager even if they're already assigned
                form.base_fields['manager'].queryset = User.objects.filter(
                    role=User.Role.ESTATE_MANAGER
                ).filter(
                    models.Q(estate__isnull=True) | models.Q(estate=obj)
                )
                form.base_fields['manager'].initial = current_manager
        
        return form

    def save_model(self, request, obj, form, change):
        """
        Save the estate and handle manager assignment.
        """
        from django.db import models
        
        super().save_model(request, obj, form, change)

        new_manager = form.cleaned_data.get("manager")

        # Get current manager (if any)
        current_manager = obj.users.filter(role=User.Role.ESTATE_MANAGER).first()

        # If there's a current manager and it's different from the new one
        if current_manager and current_manager != new_manager:
            # Remove the old manager's assignment
            current_manager.estate = None
            current_manager.save(update_fields=["estate"])

        # Assign the new manager
        if new_manager:
            new_manager.estate = obj
            new_manager.save(update_fields=["estate"])