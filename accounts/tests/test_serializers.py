# tests/test_serializers.py
"""
Tests for accounts app serializers.

Coverage:
- UserSerializer field validation
- UserCreateSerializer validation
- UserUpdateSerializer validation
- ChangePasswordSerializer validation
- PasswordResetRequestSerializer validation
- PasswordResetConfirmSerializer validation
- LoginSerializer validation
"""

import pytest
from django.contrib.auth import get_user_model
from accounts.serializers import (
    UserSerializer,
    UserCreateSerializer,
    UserUpdateSerializer,
    ChangePasswordSerializer,
    PasswordResetRequestSerializer,
    PasswordResetConfirmSerializer,
    LoginSerializer,
)
from unittest.mock import Mock

User = get_user_model()


@pytest.mark.django_db
class TestUserSerializer:
    """Test UserSerializer."""

    def test_serializer_returns_expected_fields(self, authenticated_user):
        """Test serializer returns all expected fields."""
        serializer = UserSerializer(authenticated_user)
        data = serializer.data

        assert 'id' in data
        assert 'email' in data
        assert 'first_name' in data
        assert 'last_name' in data
        assert 'full_name' in data
        assert 'role' in data
        assert 'is_active' in data
        assert 'date_joined' in data
        assert 'created_at' in data
        assert 'updated_at' in data
        assert 'tokens' in data

    def test_serializer_excludes_password(self, authenticated_user):
        """Test serializer does not include password."""
        serializer = UserSerializer(authenticated_user)
        assert 'password' not in serializer.data

    def test_full_name_method_field(self, authenticated_user):
        """Test full_name computed field."""
        authenticated_user.first_name = 'John'
        authenticated_user.last_name = 'Doe'
        authenticated_user.save()

        serializer = UserSerializer(authenticated_user)
        assert serializer.data['full_name'] == 'John Doe'

    def test_tokens_generated_in_serializer(self, authenticated_user):
        """Test JWT tokens are included in serializer."""
        serializer = UserSerializer(authenticated_user)
        tokens = serializer.data['tokens']

        assert 'access' in tokens
        assert 'refresh' in tokens
        assert isinstance(tokens['access'], str)
        assert isinstance(tokens['refresh'], str)


@pytest.mark.django_db
class TestUserCreateSerializer:
    """Test UserCreateSerializer."""

    def test_valid_user_creation_data(self):
        """Test serializer accepts valid user creation data."""
        data = {
            'email': 'newuser@example.com',
            'first_name': 'New',
            'last_name': 'User',
            'password': 'SecurePass123!',
            'password_confirm': 'SecurePass123!',
            'role': 'ESTATE_MANAGER',
        }
        serializer = UserCreateSerializer(data=data)
        assert serializer.is_valid()

    def test_missing_required_field_email(self):
        """Test serializer rejects missing email."""
        data = {
            'first_name': 'New',
            'last_name': 'User',
            'password': 'SecurePass123!',
            'password_confirm': 'SecurePass123!',
        }
        serializer = UserCreateSerializer(data=data)
        assert not serializer.is_valid()
        assert 'email' in serializer.errors

    def test_missing_required_field_password(self):
        """Test serializer rejects missing password."""
        data = {
            'email': 'newuser@example.com',
            'first_name': 'New',
            'last_name': 'User',
            'password_confirm': 'SecurePass123!',
        }
        serializer = UserCreateSerializer(data=data)
        assert not serializer.is_valid()
        assert 'password' in serializer.errors

    def test_password_mismatch(self):
        """Test serializer rejects mismatched passwords."""
        data = {
            'email': 'newuser@example.com',
            'first_name': 'New',
            'last_name': 'User',
            'password': 'SecurePass123!',
            'password_confirm': 'DifferentPass123!',
            'role': 'ESTATE_MANAGER',
        }
        serializer = UserCreateSerializer(data=data)
        assert not serializer.is_valid()
        assert 'password_confirm' in serializer.errors

    def test_duplicate_email_validation(self, authenticated_user):
        """Test serializer rejects duplicate email."""
        data = {
            'email': authenticated_user.email,
            'first_name': 'New',
            'last_name': 'User',
            'password': 'SecurePass123!',
            'password_confirm': 'SecurePass123!',
        }
        serializer = UserCreateSerializer(data=data)
        assert not serializer.is_valid()
        assert 'email' in serializer.errors

    def test_email_case_insensitive_validation(self, authenticated_user):
        """Test email validation is case-insensitive."""
        data = {
            'email': authenticated_user.email.upper(),
            'first_name': 'New',
            'last_name': 'User',
            'password': 'SecurePass123!',
            'password_confirm': 'SecurePass123!',
        }
        serializer = UserCreateSerializer(data=data)
        assert not serializer.is_valid()
        assert 'email' in serializer.errors

    def test_weak_password_rejected(self):
        """Test serializer rejects weak password."""
        data = {
            'email': 'newuser@example.com',
            'first_name': 'New',
            'last_name': 'User',
            'password': '123',
            'password_confirm': '123',
        }
        serializer = UserCreateSerializer(data=data)
        assert not serializer.is_valid()
        assert 'password' in serializer.errors

    def test_create_method_removes_password_confirm(self):
        """Test create method properly handles password confirmation."""
        data = {
            'email': 'newuser@example.com',
            'first_name': 'New',
            'last_name': 'User',
            'password': 'SecurePass123!',
            'password_confirm': 'SecurePass123!',
            'role': 'ESTATE_MANAGER',
        }
        serializer = UserCreateSerializer(data=data)
        assert serializer.is_valid()
        
        user = serializer.save()
        assert user.email == 'newuser@example.com'
        assert user.check_password('SecurePass123!')


@pytest.mark.django_db
class TestUserUpdateSerializer:
    """Test UserUpdateSerializer."""

    def test_update_first_name(self, authenticated_user):
        """Test updating first name."""
        data = {'first_name': 'Updated'}
        serializer = UserUpdateSerializer(authenticated_user, data=data, partial=True)
        assert serializer.is_valid()

    def test_update_last_name(self, authenticated_user):
        """Test updating last name."""
        data = {'last_name': 'Updated'}
        serializer = UserUpdateSerializer(authenticated_user, data=data, partial=True)
        assert serializer.is_valid()

    def test_cannot_update_email(self, authenticated_user):
        """Test email field is not updatable."""
        data = {'email': 'newemail@example.com'}
        serializer = UserUpdateSerializer(authenticated_user, data=data, partial=True)
        assert serializer.is_valid()
        updated_user = serializer.save()
        assert updated_user.email == authenticated_user.email


@pytest.mark.django_db
class TestChangePasswordSerializer:
    """Test ChangePasswordSerializer."""

    def test_valid_password_change(self, authenticated_user):
        """Test valid password change data."""
        request = Mock(user=authenticated_user)
        data = {
            'old_password': 'TestPassword123!',
            'new_password': 'NewSecurePass123!',
            'new_password_confirm': 'NewSecurePass123!',
        }
        serializer = ChangePasswordSerializer(data=data, context={'request': request})
        assert serializer.is_valid()

    def test_incorrect_old_password(self, authenticated_user):
        """Test incorrect old password rejected."""
        request = Mock(user=authenticated_user)
        data = {
            'old_password': 'WrongPassword123!',
            'new_password': 'NewSecurePass123!',
            'new_password_confirm': 'NewSecurePass123!',
        }
        serializer = ChangePasswordSerializer(data=data, context={'request': request})
        assert not serializer.is_valid()
        assert 'old_password' in serializer.errors

    def test_new_password_mismatch(self, authenticated_user):
        """Test new password confirmation mismatch."""
        request = Mock(user=authenticated_user)
        data = {
            'old_password': 'TestPassword123!',
            'new_password': 'NewSecurePass123!',
            'new_password_confirm': 'DifferentPass123!',
        }
        serializer = ChangePasswordSerializer(data=data, context={'request': request})
        assert not serializer.is_valid()
        assert 'new_password_confirm' in serializer.errors


@pytest.mark.django_db
class TestPasswordResetRequestSerializer:
    """Test PasswordResetRequestSerializer."""

    def test_valid_email(self, authenticated_user):
        """Test valid email for password reset."""
        data = {'email': authenticated_user.email}
        serializer = PasswordResetRequestSerializer(data=data)
        assert serializer.is_valid()

    def test_nonexistent_email(self):
        """Test non-existent email rejected."""
        data = {'email': 'nonexistent@example.com'}
        serializer = PasswordResetRequestSerializer(data=data)
        assert not serializer.is_valid()
        assert 'email' in serializer.errors

    def test_inactive_user_email(self, inactive_user):
        """Test inactive user email rejected."""
        data = {'email': inactive_user.email}
        serializer = PasswordResetRequestSerializer(data=data)
        assert not serializer.is_valid()
        assert 'email' in serializer.errors


@pytest.mark.django_db
class TestPasswordResetConfirmSerializer:
    """Test PasswordResetConfirmSerializer."""

    def test_valid_reset_data(self):
        """Test valid password reset confirmation data."""
        data = {
            'token': 'valid-token-string',
            'new_password': 'NewSecurePass123!',
            'new_password_confirm': 'NewSecurePass123!',
        }
        serializer = PasswordResetConfirmSerializer(data=data)
        assert serializer.is_valid()

    def test_password_mismatch(self):
        """Test password confirmation mismatch."""
        data = {
            'token': 'valid-token-string',
            'new_password': 'NewSecurePass123!',
            'new_password_confirm': 'DifferentPass123!',
        }
        serializer = PasswordResetConfirmSerializer(data=data)
        assert not serializer.is_valid()
        assert 'new_password_confirm' in serializer.errors

    def test_missing_token(self):
        """Test missing token rejected."""
        data = {
            'new_password': 'NewSecurePass123!',
            'new_password_confirm': 'NewSecurePass123!',
        }
        serializer = PasswordResetConfirmSerializer(data=data)
        assert not serializer.is_valid()
        assert 'token' in serializer.errors


@pytest.mark.django_db
class TestLoginSerializer:
    """Test LoginSerializer."""

    def test_valid_login_data(self):
        """Test valid login data."""
        data = {
            'email': 'user@example.com',
            'password': 'SecurePass123!',
        }
        serializer = LoginSerializer(data=data)
        assert serializer.is_valid()

    def test_missing_email(self):
        """Test missing email rejected."""
        data = {'password': 'SecurePass123!'}
        serializer = LoginSerializer(data=data)
        assert not serializer.is_valid()
        assert 'email' in serializer.errors

    def test_missing_password(self):
        """Test missing password rejected."""
        data = {'email': 'user@example.com'}
        serializer = LoginSerializer(data=data)
        assert not serializer.is_valid()
        assert 'password' in serializer.errors

    def test_email_normalization(self):
        """Test email is normalized to lowercase."""
        data = {
            'email': 'USER@EXAMPLE.COM',
            'password': 'SecurePass123!',
        }
        serializer = LoginSerializer(data=data)
        assert serializer.is_valid()
        assert serializer.validated_data['email'] == 'user@example.com'