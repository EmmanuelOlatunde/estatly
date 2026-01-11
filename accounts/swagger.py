# accounts/swagger.py
"""
Swagger/OpenAPI documentation schemas for accounts app.

Defines custom schema definitions for better API documentation.
"""

from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
from rest_framework import status

from .serializers import (
    ChangePasswordSerializer,
    LoginSerializer,
    PasswordResetConfirmSerializer,
    PasswordResetRequestSerializer,
    UserCreateSerializer,
    UserSerializer,
    UserUpdateSerializer,
)

# Common response schemas
user_response_schema = openapi.Response(
    description="User object",
    schema=openapi.Schema(
        type=openapi.TYPE_OBJECT,
        properties={
            'id': openapi.Schema(type=openapi.TYPE_STRING, format='uuid'),
            'email': openapi.Schema(type=openapi.TYPE_STRING, format='email'),
            'first_name': openapi.Schema(type=openapi.TYPE_STRING),
            'last_name': openapi.Schema(type=openapi.TYPE_STRING),
            'full_name': openapi.Schema(type=openapi.TYPE_STRING),
            'role': openapi.Schema(type=openapi.TYPE_STRING, enum=['SUPER_ADMIN', 'ESTATE_MANAGER']),
            'is_active': openapi.Schema(type=openapi.TYPE_BOOLEAN),
            'date_joined': openapi.Schema(type=openapi.TYPE_STRING, format='date-time'),
            'last_login': openapi.Schema(type=openapi.TYPE_STRING, format='date-time', nullable=True),
            'created_at': openapi.Schema(type=openapi.TYPE_STRING, format='date-time'),
            'updated_at': openapi.Schema(type=openapi.TYPE_STRING, format='date-time'),
        }
    )
)

error_response_schema = openapi.Response(
    description="Error response",
    schema=openapi.Schema(
        type=openapi.TYPE_OBJECT,
        properties={
            'detail': openapi.Schema(type=openapi.TYPE_STRING, description='Error message'),
        }
    )
)

validation_error_schema = openapi.Response(
    description="Validation error",
    schema=openapi.Schema(
        type=openapi.TYPE_OBJECT,
        properties={
            'field_name': openapi.Schema(
                type=openapi.TYPE_ARRAY,
                items=openapi.Schema(type=openapi.TYPE_STRING),
                description='List of validation errors for this field'
            ),
        }
    )
)

# Register endpoint documentation
register_schema = swagger_auto_schema(
    operation_id='register_user',
    operation_description='Register a new user account. Creates a new user with Estate Manager role by default.',
    request_body=UserCreateSerializer,
    responses={
        status.HTTP_201_CREATED: UserSerializer,
        status.HTTP_400_BAD_REQUEST: openapi.Response(
            description="Validation errors",
            examples={
                "application/json": {
                    "email": ["This field is required."],
                    "password": ["This field is required."]
                }
            }
        ),
    },
    tags=['Authentication'],
    
)

# Login endpoint documentation
login_schema = swagger_auto_schema(
    operation_id='login_user',
    operation_description='Authenticate user with email and password. Returns user data on successful authentication.',
    request_body=LoginSerializer,
    responses={
        status.HTTP_200_OK: UserSerializer,
        status.HTTP_401_UNAUTHORIZED: openapi.Response(
            description="Invalid credentials",
            examples={
                "application/json": {
                    "detail": "Invalid email or password"
                }
            }
        ),
        status.HTTP_400_BAD_REQUEST: openapi.Response(
            description="User inactive",
            examples={
                "application/json": {
                    "detail": "User account is inactive"
                }
            }
        ),
    },
    tags=['Authentication'],
    
)

# Password reset request documentation
password_reset_request_schema = swagger_auto_schema(
    operation_id='request_password_reset',
    operation_description='Request a password reset token. Token will be sent to the user email (in production).',
    request_body=PasswordResetRequestSerializer,
    responses={
        status.HTTP_200_OK: openapi.Response(
            description="Password reset token generated",
            examples={
                "application/json": {
                    "detail": "Password reset token generated successfully",
                    "token": "sample-token-string"
                }
            }
        ),
        status.HTTP_400_BAD_REQUEST: openapi.Response(
            description="User not found",
            examples={
                "application/json": {
                    "email": ["No active user found with this email address."]
                }
            }
        ),
    },
    tags=['Authentication'],
    
)

# Password reset confirm documentation
password_reset_confirm_schema = swagger_auto_schema(
    operation_id='confirm_password_reset',
    operation_description='Reset password using the token received via email.',
    request_body=PasswordResetConfirmSerializer,
    responses={
        status.HTTP_200_OK: openapi.Response(
            description="Password reset successful",
            examples={
                "application/json": {
                    "detail": "Password reset successfully"
                }
            }
        ),
        status.HTTP_400_BAD_REQUEST: openapi.Response(
            description="Invalid token or validation error",
            examples={
                "application/json": {
                    "detail": "Invalid reset token"
                }
            }
        ),
    },
    tags=['Authentication'],
    
)

# Change password documentation
change_password_schema = swagger_auto_schema(
    operation_id='change_password',
    operation_description='Change current user password. Requires old password for verification.',
    request_body=ChangePasswordSerializer,
    responses={
        status.HTTP_200_OK: openapi.Response(
            description="Password changed successfully",
            examples={
                "application/json": {
                    "detail": "Password changed successfully"
                }
            }
        ),
        status.HTTP_400_BAD_REQUEST: openapi.Response(
            description="Validation error",
            examples={
                "application/json": {
                    "old_password": ["Old password is incorrect."]
                }
            }
        ),
    },
    tags=['User Management'],
    
)

# Get current user documentation
me_schema = swagger_auto_schema(
    operation_id='get_current_user',
    operation_description='Get current authenticated user profile.',
    responses={
        status.HTTP_200_OK: UserSerializer,
    },
    tags=['User Management'],
    
)

# Update profile documentation
update_profile_schema = swagger_auto_schema(
    operation_id='update_profile',
    operation_description='Update current user profile (first name and last name only).',
    request_body=UserUpdateSerializer,
    responses={
        status.HTTP_200_OK: UserSerializer,
        status.HTTP_400_BAD_REQUEST: openapi.Response(
            description="Validation errors",
            examples={
                "application/json": {
                    "first_name": ["This field may not be blank."]
                }
            }
        ),
    },
    tags=['User Management'],
    
)

# Activate user documentation
activate_user_schema = swagger_auto_schema(
    operation_id='activate_user',
    operation_description='Activate a user account. Requires super admin privileges.',
    responses={
        status.HTTP_200_OK: openapi.Response(
            description="User activated successfully",
            schema=openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    'detail': openapi.Schema(type=openapi.TYPE_STRING),
                }
            )
        ),
        status.HTTP_403_FORBIDDEN: error_response_schema,
    },
    tags=['User Management'],
    
)

# Deactivate user documentation
deactivate_user_schema = swagger_auto_schema(
    operation_id='deactivate_user',
    operation_description='Deactivate a user account. Requires super admin privileges. Cannot deactivate super admin accounts.',
    responses={
        status.HTTP_200_OK: openapi.Response(
            description="User deactivated successfully",
            schema=openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    'detail': openapi.Schema(type=openapi.TYPE_STRING),
                }
            )
        ),
        status.HTTP_400_BAD_REQUEST: error_response_schema,
        status.HTTP_403_FORBIDDEN: error_response_schema,
    },
    tags=['User Management'],
    
)