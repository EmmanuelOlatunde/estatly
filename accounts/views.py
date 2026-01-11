# accounts/views.py
"""
API views for accounts app.

Provides REST API endpoints for user management and authentication.
"""
from drf_yasg.utils import swagger_auto_schema
from django.utils import timezone
from django.contrib.auth import get_user_model
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from . import services
from .permissions import IsSuperAdminOrSelf
from .serializers import (
    ChangePasswordSerializer,
    LoginSerializer,
    PasswordResetConfirmSerializer,
    PasswordResetRequestSerializer,
    UserCreateSerializer,
    UserSerializer,
    UserUpdateSerializer,
)

from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework_simplejwt.tokens import RefreshToken


from .swagger import (
    register_schema,
    login_schema,
    password_reset_request_schema,
    password_reset_confirm_schema,
    change_password_schema,
    me_schema,
    update_profile_schema,
    activate_user_schema,
    deactivate_user_schema,
)

User = get_user_model()

class CustomTokenObtainPairView(TokenObtainPairView):
    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user = serializer.user
        refresh = RefreshToken.for_user(user)

        return Response({
            'refresh': str(refresh),
            'access': str(refresh.access_token),
            'user': UserSerializer(user).data
        }, status=status.HTTP_200_OK)

class UserViewSet(viewsets.ModelViewSet):
    """
    ViewSet for User model.

    Provides CRUD operations for user management.
    Super admins can manage all users, regular users can only view/update themselves.
    """

    queryset = User.objects.all()
    permission_classes = [IsAuthenticated, IsSuperAdminOrSelf]
    serializer_class = UserSerializer

    @swagger_auto_schema(
        operation_description="List users",
        responses={200: UserSerializer(many=True)},
    )
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_description="Retrieve a user",
        responses={200: UserSerializer},
    )
    def retrieve(self, request, *args, **kwargs):
        return super().retrieve(request, *args, **kwargs)

    def get_serializer_class(self):
        """Return appropriate serializer based on action."""
        if self.action == 'create':
            return UserCreateSerializer
        elif self.action in ['update', 'partial_update']:
            return UserUpdateSerializer
        return UserSerializer

    def get_queryset(self):
        """Filter queryset based on user permissions."""
        if getattr(self, 'swagger_fake_view', False):
            return User.objects.none()
        
        user = self.request.user

        if user.is_super_admin():
            return User.objects.all()

        return User.objects.filter(id=user.id)

    @swagger_auto_schema(
        operation_description="Create a user",
        request_body=UserCreateSerializer,
        responses={201: UserSerializer},
    )
    def create(self, request, *args, **kwargs):
        return super().create(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_description="Update a user",
        request_body=UserUpdateSerializer,
        responses={200: UserSerializer},
    )
    def update(self, request, *args, **kwargs):
        return super().update(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_description="Partially update a user",
        request_body=UserUpdateSerializer,
        responses={200: UserSerializer},
    )
    def partial_update(self, request, *args, **kwargs):
        return super().partial_update(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_description="Delete a user",
        responses={204: 'User deleted'},
    )
    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()

        if instance == request.user:
            return Response(
                {"detail": "You cannot delete your own account."},
                status=status.HTTP_403_FORBIDDEN,
            )

        return super().destroy(request, *args, **kwargs)

    @me_schema
    @action(detail=False, methods=['get'], permission_classes=[IsAuthenticated])
    def me(self, request):
        """
        Get current authenticated user's profile.

        Returns:
            Current user's data
        """
        serializer = self.get_serializer(request.user)
        return Response(serializer.data)



    @update_profile_schema
    @action(detail=False, methods=['patch'], permission_classes=[IsAuthenticated])
    def update_profile(self, request):
        """
        Update current authenticated user's profile.
        """
        if not request.data:
            return Response(
                {"detail": "Request body cannot be empty."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        serializer = UserUpdateSerializer(
            request.user,
            data=request.data,
            partial=True
        )
        serializer.is_valid(raise_exception=True)

        user = services.update_user_profile(
            user=request.user,
            **serializer.validated_data
        )

        return Response(UserSerializer(user).data)



    @change_password_schema
    @action(detail=False, methods=['post'], permission_classes=[IsAuthenticated])
    def change_password(self, request):
        """
        Change current user's password.

        Requires old password for verification.

        Returns:
            Success message
        """
        serializer = ChangePasswordSerializer(
            data=request.data,
            context={'request': request}
        )
        serializer.is_valid(raise_exception=True)

        services.change_user_password(
            user=request.user,
            old_password=serializer.validated_data['old_password'],
            new_password=serializer.validated_data['new_password']
        )

        return Response(
            {'detail': 'Password changed successfully'},
            status=status.HTTP_200_OK
        )

    @deactivate_user_schema
    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated])
    def deactivate(self, request, pk=None):
        """
        Deactivate a user account.

        Only super admins can deactivate users.

        Returns:
            Success message
        """
        user = self.get_object()

        try:
            services.deactivate_user(user=user)
            return Response(
                {'detail': 'User deactivated successfully'},
                status=status.HTTP_200_OK
            )
        except ValueError as e:
            return Response(
                {'detail': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )

    @activate_user_schema
    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated])
    def activate(self, request, pk=None):
        """
        Activate a user account.

        Only super admins can activate users.

        Returns:
            Success message
        """
        user = self.get_object()
        services.activate_user(user=user)

        return Response(
            {'detail': 'User activated successfully'},
            status=status.HTTP_200_OK
        )


class RegisterView(APIView):
    """
    API view for user registration.

    Allows new users to create an account.
    """

    permission_classes = [AllowAny]
    serializer_class = UserCreateSerializer
    
    @register_schema
    def post(self, request):
        """
        Register a new user account.

        Args:
            request: HTTP request with user data

        Returns:
            Created user data
        """
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            user = services.create_user(**serializer.validated_data)

            return Response(
                UserSerializer(user).data,
                status=status.HTTP_201_CREATED
            )

        except ValueError as e:
            return Response(
                {'detail': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )


class LoginView(APIView):
    permission_classes = [AllowAny]
    serializer_class = LoginSerializer

    @login_schema
    def post(self, request):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            user = services.authenticate_user(
                email=serializer.validated_data['email'],
                password=serializer.validated_data['password']
            )

            if user is None:
                return Response(
                    {'detail': 'Invalid email or password'},
                    status=status.HTTP_401_UNAUTHORIZED
                )

            # --- FIX: update last_login ---
            user.last_login = timezone.now()
            user.save(update_fields=["last_login"])

            return Response(
                UserSerializer(user).data,
                status=status.HTTP_200_OK
            )

        except ValueError as e:
            return Response(
                {'detail': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )

class PasswordResetRequestView(APIView):
    """
    API view for requesting password reset.

    Generates reset token and sends to user's email.
    """
    
    permission_classes = [AllowAny]
    serializer_class = PasswordResetRequestSerializer

    @password_reset_request_schema
    def post(self, request):
        """
        Generate password reset token for user.

        Args:
            request: HTTP request with email

        Returns:
            Success message and token (in production, send via email)
        """
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            reset_token = services.generate_password_reset_token(
                email=serializer.validated_data['email']
            )

            return Response(
                {
                    'detail': 'Password reset token generated successfully',
                    'token': reset_token.token,
                },
                status=status.HTTP_200_OK
            )

        except ValueError as e:
            return Response(
                {'detail': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )


class PasswordResetConfirmView(APIView):
    """
    API view for confirming password reset.

    Validates token and sets new password.
    """

    permission_classes = [AllowAny]
    serializer_class = PasswordResetConfirmSerializer

    @password_reset_confirm_schema
    def post(self, request):
        """
        Reset password using token.

        Args:
            request: HTTP request with token and new password

        Returns:
            Success message
        """
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            services.reset_password_with_token(
                token=serializer.validated_data['token'],
                new_password=serializer.validated_data['new_password']
            )

            return Response(
                {'detail': 'Password reset successfully'},
                status=status.HTTP_200_OK
            )

        except ValueError as e:
            return Response(
                {'detail': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )