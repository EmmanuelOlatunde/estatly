# accounts/services.py
"""
Business logic for accounts app.

Contains all domain logic for user management and authentication.
"""

import secrets
from datetime import timedelta
from typing import Optional

from django.contrib.auth import authenticate, get_user_model
from django.db import transaction
from django.utils import timezone

from .models import PasswordResetToken
from django.contrib.auth.models import AbstractBaseUser

User = get_user_model()


def create_user(
    *,
    email: str,
    password: str,
    first_name: str = '',
    last_name: str = '',
    role: str = User.Role.ESTATE_MANAGER,
    **kwargs
) -> AbstractBaseUser:
    """
    Create a new user account.

    Args:
        email: User's email address
        password: User's password
        first_name: User's first name
        last_name: User's last name
        role: User's role (defaults to ESTATE_MANAGER)
        **kwargs: Additional user fields

    Returns:
        The created User instance

    Raises:
        ValueError: If validation fails or email already exists
    """
    email = email.lower().strip()

    if User.objects.filter(email=email).exists():
        raise ValueError(f'User with email {email} already exists')
    
    # Remove password_confirm from kwargs if it exists
    kwargs.pop('password_confirm', None)


    user = User.objects.create_user(
        email=email,
        password=password,
        first_name=first_name.strip(),
        last_name=last_name.strip(),
        role=role,
        **kwargs
    )

    return user


def update_user_profile(
    *,
    user: AbstractBaseUser,
    first_name: Optional[str] = None,
    last_name: Optional[str] = None
) -> AbstractBaseUser:
    """
    Update user profile information.

    Args:
        user: User instance to update
        first_name: New first name (optional)
        last_name: New last name (optional)

    Returns:
        Updated User instance

    Raises:
        ValueError: If validation fails
    """
    if first_name is not None:
        user.first_name = first_name.strip()

    if last_name is not None:
        user.last_name = last_name.strip()

    user.full_clean()
    user.save(update_fields=['first_name', 'last_name', 'updated_at'])

    return user


def change_user_password(
    *,
    user: AbstractBaseUser,
    old_password: str,
    new_password: str
) -> AbstractBaseUser:
    """
    Change user's password.

    Args:
        user: User instance
        old_password: Current password
        new_password: New password

    Returns:
        Updated User instance

    Raises:
        ValueError: If old password is incorrect
    """
    if not user.check_password(old_password):
        raise ValueError('Current password is incorrect')

    user.set_password(new_password)
    user.save(update_fields=['password', 'updated_at'])

    return user


def authenticate_user(*, email: str, password: str) -> Optional[AbstractBaseUser]:
    """
    Authenticate user with email and password.

    Args:
        email: User's email address
        password: User's password

    Returns:
        User instance if authentication successful, None otherwise

    Raises:
        ValueError: If user is inactive
    """
    email = email.lower().strip()
    user = authenticate(email=email, password=password)

    if user is not None and not user.is_active:
        raise ValueError('User account is inactive')

    return user


def generate_password_reset_token(*, email: str) -> PasswordResetToken:
    """
    Generate password reset token for user.

    Args:
        email: User's email address

    Returns:
        PasswordResetToken instance

    Raises:
        ValueError: If user not found or inactive
    """
    email = email.lower().strip()

    try:
        user = User.objects.get(email=email, is_active=True)
    except User.DoesNotExist:
        raise ValueError('No active user found with this email address')

    with transaction.atomic():
        PasswordResetToken.objects.filter(
            user=user,
            used=False,
            expires_at__gt=timezone.now()
        ).update(used=True)

        token = secrets.token_urlsafe(32)
        expires_at = timezone.now() + timedelta(hours=24)

        reset_token = PasswordResetToken.objects.create(
            user=user,
            token=token,
            expires_at=expires_at
        )

    return reset_token


def reset_password_with_token(*, token: str, new_password: str) -> AbstractBaseUser:
    """
    Reset user password using reset token.

    Args:
        token: Password reset token
        new_password: New password to set

    Returns:
        User instance with updated password

    Raises:
        ValueError: If token is invalid, expired, or already used
    """
    try:
        reset_token = PasswordResetToken.objects.select_related('user').get(
            token=token
        )
    except PasswordResetToken.DoesNotExist:
        raise ValueError('Invalid reset token')

    if not reset_token.is_valid():
        raise ValueError('Reset token has expired or already been used')

    with transaction.atomic():
        user = reset_token.user
        user.set_password(new_password)
        user.save(update_fields=['password', 'updated_at'])

        reset_token.used = True
        reset_token.save(update_fields=['used'])

    return user


def deactivate_user(*, user: AbstractBaseUser) -> AbstractBaseUser:
    """
    Deactivate a user account.

    Args:
        user: User instance to deactivate

    Returns:
        Updated User instance

    Raises:
        ValueError: If user is a super admin
    """
    if user.is_super_admin():
        raise ValueError('Cannot deactivate super admin account')

    user.is_active = False
    user.save(update_fields=['is_active', 'updated_at'])

    return user


def activate_user(*, user: AbstractBaseUser) -> AbstractBaseUser:
    """
    Activate a user account.

    Args:
        user: User instance to activate

    Returns:
        Updated User instance
    """
    user.is_active = True
    user.save(update_fields=['is_active', 'updated_at'])

    return user


def get_user_by_email(*, email: str) -> Optional[AbstractBaseUser]:
    """
    Retrieve user by email address.

    Args:
        email: User's email address

    Returns:
        User instance if found, None otherwise
    """
    email = email.lower().strip()

    try:
        return User.objects.get(email=email)
    except User.DoesNotExist:
        return None


def get_active_users_queryset():
    """
    Get queryset of all active users.

    Returns:
        QuerySet of active User instances
    """
    return User.objects.filter(is_active=True)


def get_estate_managers_queryset():
    """
    Get queryset of all estate managers.

    Returns:
        QuerySet of User instances with ESTATE_MANAGER role
    """
    return User.objects.filter(
        role=User.Role.ESTATE_MANAGER,
        is_active=True
    )