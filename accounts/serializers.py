# accounts/serializers.py
"""
Serializers for accounts app.

Handles serialization and validation of User and authentication data.
"""

from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from rest_framework import serializers
from rest_framework_simplejwt.tokens import RefreshToken

User = get_user_model()


class UserSerializer(serializers.ModelSerializer):
    """
    Serializer for User model (read operations).

    Returns user information including computed full name.
    """
    # tokens = serializers.SerializerMethodField()

    full_name = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = [
            'id',
            'email',
            'first_name',
            'last_name',
            'full_name',
            'role',
            'is_active',
            'date_joined',
            'last_login',
            'created_at',
            'updated_at',
            # 'tokens', 
        ]
        read_only_fields = [
            'id',
            'date_joined',
            'last_login',
            'created_at',
            'updated_at',
        ]
    # def get_tokens(self, obj):
    #     refresh = RefreshToken.for_user(obj)
    #     return {
    #         'refresh': str(refresh),
    #         'access': str(refresh.access_token),
    #     }
    def get_full_name(self, obj):
        """Return user's full name."""
        return obj.get_full_name()


class UserCreateSerializer(serializers.ModelSerializer):
    """
    Serializer for creating new users.

    Handles password validation and user creation.
    """

    password = serializers.CharField(
        write_only=True,
        required=True,
        validators=[validate_password],
        style={'input_type': 'password'}
    )
    password_confirm = serializers.CharField(
        write_only=True,
        required=True,
        style={'input_type': 'password'}
    )

    class Meta:
        model = User
        fields = [
            'email',
            'first_name',
            'last_name',
            'password',
            'password_confirm',
            'role',
        ]

    def validate_email(self, value):
        """Validate email is unique."""
        if User.objects.filter(email__iexact=value).exists():
            raise serializers.ValidationError('A user with this email already exists.')
        return value.lower()

    def validate(self, attrs):
        """Validate password confirmation matches."""
        if attrs.get('password') != attrs.get('password_confirm'):
            raise serializers.ValidationError({
                'password_confirm': 'Password fields do not match.'
            })
        return attrs

    def create(self, validated_data):
        """Create user with validated data."""
        validated_data.pop('password_confirm')
        password = validated_data.pop('password')
        user = User.objects.create_user(password=password, **validated_data)
        return user


class UserUpdateSerializer(serializers.ModelSerializer):
    """
    Serializer for updating user profile.

    Allows updating name fields only.
    """

    class Meta:
        model = User
        fields = ['first_name', 'last_name']


class ChangePasswordSerializer(serializers.Serializer):
    """
    Serializer for changing user password.

    Requires current password for security.
    """

    old_password = serializers.CharField(
        required=True,
        write_only=True,
        style={'input_type': 'password'}
    )
    new_password = serializers.CharField(
        required=True,
        write_only=True,
        validators=[validate_password],
        style={'input_type': 'password'}
    )
    new_password_confirm = serializers.CharField(
        required=True,
        write_only=True,
        style={'input_type': 'password'}
    )

    def validate_old_password(self, value):
        """Validate old password is correct."""
        user = self.context['request'].user
        if not user.check_password(value):
            raise serializers.ValidationError('Old password is incorrect.')
        return value

    def validate(self, attrs):
        """Validate new password confirmation matches."""
        if attrs.get('new_password') != attrs.get('new_password_confirm'):
            raise serializers.ValidationError({
                'new_password_confirm': 'New password fields do not match.'
            })
        return attrs


class PasswordResetRequestSerializer(serializers.Serializer):
    """
    Serializer for requesting password reset.

    Validates email and initiates reset process.
    """

    email = serializers.EmailField(required=True)

    def validate_email(self, value):
        """Validate email exists in system."""
        # if not User.objects.filter(email__iexact=value, is_active=True).exists():
        #     raise serializers.ValidationError(
        #         'No active user found with this email address.'
        #     )
        return value.lower()


class PasswordResetConfirmSerializer(serializers.Serializer):
    """
    Serializer for confirming password reset.

    Validates token and sets new password.
    """

    token = serializers.CharField(required=True)
    new_password = serializers.CharField(
        required=True,
        write_only=True,
        validators=[validate_password],
        style={'input_type': 'password'}
    )
    new_password_confirm = serializers.CharField(
        required=True,
        write_only=True,
        style={'input_type': 'password'}
    )

    def validate(self, attrs):
        """Validate new password confirmation matches."""
        if attrs.get('new_password') != attrs.get('new_password_confirm'):
            raise serializers.ValidationError({
                'new_password_confirm': 'Password fields do not match.'
            })
        return attrs


class LoginSerializer(serializers.Serializer):
    """
    Serializer for user login.

    Validates email and password credentials.
    """

    email = serializers.EmailField(required=True)
    password = serializers.CharField(
        required=True,
        write_only=True,
        style={'input_type': 'password'}
    )

    def validate_email(self, value):
        """Normalize email to lowercase."""
        return value.lower()