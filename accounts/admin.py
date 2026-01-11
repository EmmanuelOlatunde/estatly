# accounts/admin.py
"""
Django admin configuration for accounts app.

Registers models and customizes admin interface.
"""

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.html import format_html

from .models import PasswordResetToken, User


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    """Admin interface for User model."""

    list_display = [
        'email',
        'first_name',
        'last_name',
        'role',
        'is_active',
        'is_staff',
        'date_joined',
        'last_login',
    ]
    list_filter = [
        'role',
        'is_active',
        'is_staff',
        'is_superuser',
        'date_joined',
    ]
    search_fields = [
        'email',
        'first_name',
        'last_name',
    ]
    ordering = ['-date_joined']
    readonly_fields = [
        'id',
        'date_joined',
        'last_login',
        'created_at',
        'updated_at',
    ]

    fieldsets = (
        (None, {
            'fields': ('id', 'email', 'password')
        }),
        ('Personal Info', {
            'fields': ('first_name', 'last_name', 'role')
        }),
        ('Permissions', {
            'fields': (
                'is_active',
                'is_staff',
                'is_superuser',
                'groups',
                'user_permissions',
            )
        }),
        ('Important Dates', {
            'fields': (
                'date_joined',
                'last_login',
                'created_at',
                'updated_at',
            )
        }),
    )

    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': (
                'email',
                'first_name',
                'last_name',
                'role',
                'password1',
                'password2',
                'is_active',
                'is_staff',
            ),
        }),
    )

    def get_queryset(self, request):
        """Optimize queryset with select_related."""
        qs = super().get_queryset(request)
        return qs.select_related()


@admin.register(PasswordResetToken)
class PasswordResetTokenAdmin(admin.ModelAdmin):
    """Admin interface for PasswordResetToken model."""

    list_display = [
        'user',
        'token_preview',
        'used',
        'expires_at',
        'created_at',
        'is_valid_status',
    ]
    list_filter = [
        'used',
        'expires_at',
        'created_at',
    ]
    search_fields = [
        'user__email',
        'token',
    ]
    readonly_fields = [
        'id',
        'user',
        'token',
        'expires_at',
        'used',
        'created_at',
        'is_valid_status',
    ]
    ordering = ['-created_at']

    fieldsets = (
        (None, {
            'fields': ('id', 'user', 'token')
        }),
        ('Status', {
            'fields': ('used', 'expires_at', 'is_valid_status')
        }),
        ('Timestamps', {
            'fields': ('created_at',)
        }),
    )

    def token_preview(self, obj):
        """Display preview of token."""
        return f'{obj.token[:10]}...'
    token_preview.short_description = 'Token'

    def is_valid_status(self, obj):
        """Display visual indicator of token validity."""
        if obj.is_valid():
            return format_html(
                '<span style="color: green;">✓ Valid</span>'
            )
        return format_html(
            '<span style="color: red;">✗ Invalid</span>'
        )
    is_valid_status.short_description = 'Status'

    def has_add_permission(self, request):
        """Disable manual token creation."""
        return False

    def has_change_permission(self, request, obj=None):
        """Disable token editing."""
        return False

    def get_queryset(self, request):
        """Optimize queryset with select_related."""
        qs = super().get_queryset(request)
        return qs.select_related('user')