# accounts/models.py
"""
Models for accounts app.

Defines User model for authentication and profile management.
"""

import uuid
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.core.validators import EmailValidator
from django.db import models
from django.utils import timezone
from estates.models import Estate
from django.core.exceptions import ValidationError


class UserManager(BaseUserManager):
    """Custom manager for User model."""

    def create_user(self, email, password=None, **extra_fields):
        """
        Create and return a regular user with email and password.

        Args:
            email: User's email address
            password: User's password
            **extra_fields: Additional user fields

        Returns:
            User instance

        Raises:
            ValueError: If email is not provided
        """
        if not email:
            raise ValueError('Email address is required')

        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        """
        Create and return a superuser with email and password.

        Args:
            email: Superuser's email address
            password: Superuser's password
            **extra_fields: Additional user fields

        Returns:
            User instance with superuser privileges
        """
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('role', User.Role.SUPER_ADMIN)

        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')

        return self.create_user(email, password, **extra_fields)


class User(AbstractBaseUser, PermissionsMixin):
    """
    Custom user model for Estatly.

    Uses email as the primary authentication identifier.
    Supports two roles: Super Admin and Estate Manager.
    """

    class Role(models.TextChoices):
        """User role choices."""
        SUPER_ADMIN = 'SUPER_ADMIN', 'Super Admin'
        ESTATE_MANAGER = 'ESTATE_MANAGER', 'Estate Manager'
        REGULAR = 'REGULAR', 'Regular'

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    estate = models.OneToOneField(
        Estate,
        on_delete=models.CASCADE,
        null=True,
        blank=True
    )


    email = models.EmailField(
        max_length=255,
        unique=True,
        validators=[EmailValidator()],
        db_index=True
    )
    first_name = models.CharField(max_length=150, blank=True)
    last_name = models.CharField(max_length=150, blank=True)
    role = models.CharField(
        max_length=20,
        choices=Role.choices,
        default=Role.ESTATE_MANAGER,
        db_index=True
    )

    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    is_superuser = models.BooleanField(default=False)

    date_joined = models.DateTimeField(default=timezone.now)
    last_login = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = UserManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['first_name', 'last_name']

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'User'
        verbose_name_plural = 'Users'
        indexes = [
            models.Index(fields=['email']),
            models.Index(fields=['role']),
            models.Index(fields=['is_active']),
        ]

    def __str__(self):
        """Return string representation of user."""
        return self.email

    def get_full_name(self):
        """Return the user's full name."""
        full_name = f'{self.first_name} {self.last_name}'.strip()
        return full_name or self.email

    def get_short_name(self):
        """Return the user's short name."""
        return self.first_name or self.email

    def is_super_admin(self):
        """Check if user is a super admin."""
        return self.role == self.Role.SUPER_ADMIN

    def is_estate_manager(self):
        """Check if user is an estate manager."""
        return self.role == self.Role.ESTATE_MANAGER


    def clean(self):
        """Validate model fields and enforce role rules."""
        super().clean()

        # Always normalize email
        self.email = self.__class__.objects.normalize_email(self.email)

        # Enforce estate-manager invariant
        if self.role == self.Role.ESTATE_MANAGER and not self.estate:
            raise ValidationError({
                "estate": "Estate managers must be assigned to an estate."
            })

        # (Optional hardening)
        if self.role != self.Role.ESTATE_MANAGER and self.estate:
            raise ValidationError({
                "estate": "Only estate managers can be assigned to an estate."
            })


class PasswordResetToken(models.Model):
    """
    Token model for password reset functionality.

    Stores temporary tokens for password reset operations.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='password_reset_tokens'
    )
    token = models.CharField(max_length=100, unique=True, db_index=True)
    expires_at = models.DateTimeField()
    used = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Password Reset Token'
        verbose_name_plural = 'Password Reset Tokens'
        indexes = [
            models.Index(fields=['token']),
            models.Index(fields=['expires_at']),
            models.Index(fields=['user', 'used']),
        ]

    def __str__(self):
        """Return string representation of token."""
        return f'Reset token for {self.user.email}'

    def is_valid(self):
        """Check if token is still valid and unused."""
        return not self.used and timezone.now() < self.expires_at