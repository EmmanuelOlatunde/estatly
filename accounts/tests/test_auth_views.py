# tests/test_auth_views.py
"""
Tests for authentication views (register, login, password reset).

Coverage:
- Registration endpoint
- Login endpoint  
- Password reset request
- Password reset confirm
- Authentication/authorization
- Success and failure paths
- Edge cases
"""

import pytest
from django.urls import reverse
from django.contrib.auth import get_user_model
from .factories import PasswordResetTokenFactory
from .helpers import get_user_payload, assert_user_response_structure

User = get_user_model()


@pytest.mark.django_db
class TestRegisterView:
    """Test user registration endpoint."""

    def test_register_user_success(self, api_client):
        """Test successful user registration."""
        url = reverse('register')
        payload = get_user_payload(email='newuser@example.com')

        response = api_client.post(url, payload, format='json')

        assert response.status_code == 201
        assert_user_response_structure(response.data)
        assert response.data['email'] == 'newuser@example.com'
        assert response.data['first_name'] == 'Test'
        assert response.data['last_name'] == 'User'
        assert response.data['role'] == 'ESTATE_MANAGER'
        assert response.data['is_active'] is True

        user = User.objects.get(email='newuser@example.com')
        assert user is not None
        assert user.check_password('TestPass123!')

    def test_register_user_with_all_fields(self, api_client):
        """Test registration with all optional fields."""
        url = reverse('register')
        payload = get_user_payload(
            email='complete@example.com',
            first_name='John',
            last_name='Doe',
            role='ESTATE_MANAGER'
        )

        response = api_client.post(url, payload, format='json')

        assert response.status_code == 201
        assert response.data['first_name'] == 'John'
        assert response.data['last_name'] == 'Doe'

    def test_register_missing_email(self, api_client):
        """Test registration fails without email."""
        url = reverse('register')
        payload = get_user_payload()
        del payload['email']

        response = api_client.post(url, payload, format='json')

        assert response.status_code == 400
        assert 'email' in response.data

    def test_register_missing_password(self, api_client):
        """Test registration fails without password."""
        url = reverse('register')
        payload = get_user_payload()
        del payload['password']

        response = api_client.post(url, payload, format='json')

        assert response.status_code == 400
        assert 'password' in response.data

    def test_register_password_mismatch(self, api_client):
        """Test registration fails when passwords don't match."""
        url = reverse('register')
        payload = get_user_payload()
        payload['password_confirm'] = 'DifferentPassword123!'

        response = api_client.post(url, payload, format='json')

        assert response.status_code == 400
        assert 'password_confirm' in response.data

    def test_register_duplicate_email(self, api_client, authenticated_user):
        """Test registration fails with duplicate email."""
        url = reverse('register')
        payload = get_user_payload(email=authenticated_user.email)

        response = api_client.post(url, payload, format='json')

        assert response.status_code == 400
        assert 'email' in response.data

    def test_register_duplicate_email_case_insensitive(
        self, api_client, authenticated_user
    ):
        """Test email uniqueness is case-insensitive."""
        url = reverse('register')
        payload = get_user_payload(email=authenticated_user.email.upper())

        response = api_client.post(url, payload, format='json')

        assert response.status_code == 400
        assert 'email' in response.data

    def test_register_invalid_email_format(self, api_client):
        """Test registration fails with invalid email format."""
        url = reverse('register')
        payload = get_user_payload(email='invalid-email')

        response = api_client.post(url, payload, format='json')

        assert response.status_code == 400
        assert 'email' in response.data

    def test_register_weak_password(self, api_client):
        """Test registration fails with weak password."""
        url = reverse('register')
        payload = get_user_payload(password='123', password_confirm='123')
        payload['password_confirm'] = '123'

        response = api_client.post(url, payload, format='json')

        assert response.status_code == 400
        assert 'password' in response.data

    def test_register_empty_string_email(self, api_client):
        """Test registration fails with empty email."""
        url = reverse('register')
        payload = get_user_payload(email='')

        response = api_client.post(url, payload, format='json')

        assert response.status_code == 400
        assert 'email' in response.data

    def test_register_tokens_included_in_response(self, api_client):
        """Test JWT tokens are included in registration response."""
        url = reverse('register')
        payload = get_user_payload(email='tokenuser@example.com')

        response = api_client.post(url, payload, format='json')

        assert response.status_code == 201
        assert 'tokens' in response.data
        assert 'access' in response.data['tokens']
        assert 'refresh' in response.data['tokens']


@pytest.mark.django_db
class TestLoginView:
    """Test user login endpoint."""

    def test_login_success(self, api_client, authenticated_user):
        """Test successful login."""
        url = reverse('login')
        payload = {
            'email': authenticated_user.email,
            'password': 'TestPassword123!',
        }

        response = api_client.post(url, payload, format='json')

        assert response.status_code == 200
        assert_user_response_structure(response.data)
        assert response.data['email'] == authenticated_user.email

    def test_login_case_insensitive_email(self, api_client, authenticated_user):
        """Test login works with different email case."""
        url = reverse('login')
        payload = {
            'email': authenticated_user.email.upper(),
            'password': 'TestPassword123!',
        }

        response = api_client.post(url, payload, format='json')

        assert response.status_code == 200
        assert response.data['email'] == authenticated_user.email

    def test_login_wrong_password(self, api_client, authenticated_user):
        """Test login fails with wrong password."""
        url = reverse('login')
        payload = {
            'email': authenticated_user.email,
            'password': 'WrongPassword123!',
        }

        response = api_client.post(url, payload, format='json')

        assert response.status_code == 401
        assert 'detail' in response.data

    def test_login_nonexistent_user(self, api_client):
        """Test login fails for non-existent user."""
        url = reverse('login')
        payload = {
            'email': 'nonexistent@example.com',
            'password': 'TestPassword123!',
        }

        response = api_client.post(url, payload, format='json')

        assert response.status_code == 401
        assert 'detail' in response.data

    def test_login_inactive_user(self, api_client, inactive_user):
        """Test login fails for inactive user."""
        url = reverse('login')
        payload = {
            'email': inactive_user.email,
            'password': 'TestPassword123!',
        }

        response = api_client.post(url, payload, format='json')

        assert response.status_code == 401
        assert 'detail' in response.data

    def test_login_missing_email(self, api_client):
        """Test login fails without email."""
        url = reverse('login')
        payload = {'password': 'TestPassword123!'}

        response = api_client.post(url, payload, format='json')

        assert response.status_code == 400
        assert 'email' in response.data

    def test_login_missing_password(self, api_client, authenticated_user):
        """Test login fails without password."""
        url = reverse('login')
        payload = {'email': authenticated_user.email}

        response = api_client.post(url, payload, format='json')

        assert response.status_code == 400
        assert 'password' in response.data

    def test_login_empty_credentials(self, api_client):
        """Test login fails with empty credentials."""
        url = reverse('login')
        payload = {'email': '', 'password': ''}

        response = api_client.post(url, payload, format='json')

        assert response.status_code == 400


@pytest.mark.django_db
class TestPasswordResetRequestView:
    """Test password reset request endpoint."""

    def test_password_reset_request_success(self, api_client, authenticated_user):
        """Test successful password reset request."""
        url = reverse('password-reset-request')
        payload = {'email': authenticated_user.email}

        response = api_client.post(url, payload, format='json')

        assert response.status_code == 200
        assert 'detail' in response.data
        assert 'token' in response.data

        from accounts.models import PasswordResetToken
        token = PasswordResetToken.objects.filter(
            user=authenticated_user, used=False
        ).first()
        assert token is not None

    def test_password_reset_request_case_insensitive(
        self, api_client, authenticated_user
    ):
        """Test password reset with different email case."""
        url = reverse('password-reset-request')
        payload = {'email': authenticated_user.email.upper()}

        response = api_client.post(url, payload, format='json')

        assert response.status_code == 200

    def test_password_reset_request_nonexistent_email(self, api_client):
        """Test password reset fails for non-existent email."""
        url = reverse('password-reset-request')
        payload = {'email': 'nonexistent@example.com'}

        response = api_client.post(url, payload, format='json')

        assert response.status_code == 400
        assert 'email' in response.data

    def test_password_reset_request_inactive_user(self, api_client, inactive_user):
        """Test password reset fails for inactive user."""
        url = reverse('password-reset-request')
        payload = {'email': inactive_user.email}

        response = api_client.post(url, payload, format='json')

        assert response.status_code == 400
        assert 'email' in response.data

    def test_password_reset_request_missing_email(self, api_client):
        """Test password reset fails without email."""
        url = reverse('password-reset-request')
        payload = {}

        response = api_client.post(url, payload, format='json')

        assert response.status_code == 400
        assert 'email' in response.data

    def test_password_reset_invalidates_old_tokens(
        self, api_client, authenticated_user
    ):
        """Test new reset request invalidates old tokens."""
        old_token = PasswordResetTokenFactory.create(
            user=authenticated_user, used=False
        )

        url = reverse('password-reset-request')
        payload = {'email': authenticated_user.email}

        response = api_client.post(url, payload, format='json')

        assert response.status_code == 200

        old_token.refresh_from_db()
        assert old_token.used is True


@pytest.mark.django_db
class TestPasswordResetConfirmView:
    """Test password reset confirmation endpoint."""

    def test_password_reset_confirm_success(self, api_client, authenticated_user):
        """Test successful password reset confirmation."""
        reset_token = PasswordResetTokenFactory.create(
            user=authenticated_user, used=False
        )

        url = reverse('password-reset-confirm')
        payload = {
            'token': reset_token.token,
            'new_password': 'NewSecurePass123!',
            'new_password_confirm': 'NewSecurePass123!',
        }

        response = api_client.post(url, payload, format='json')

        assert response.status_code == 200
        assert 'detail' in response.data

        authenticated_user.refresh_from_db()
        assert authenticated_user.check_password('NewSecurePass123!')

        reset_token.refresh_from_db()
        assert reset_token.used is True

    def test_password_reset_confirm_invalid_token(self, api_client):
        """Test password reset fails with invalid token."""
        url = reverse('password-reset-confirm')
        payload = {
            'token': 'invalid-token',
            'new_password': 'NewSecurePass123!',
            'new_password_confirm': 'NewSecurePass123!',
        }

        response = api_client.post(url, payload, format='json')

        assert response.status_code == 400
        assert 'detail' in response.data

    def test_password_reset_confirm_used_token(self, api_client, authenticated_user):
        """Test password reset fails with already used token."""
        reset_token = PasswordResetTokenFactory.create(
            user=authenticated_user, used=True
        )

        url = reverse('password-reset-confirm')
        payload = {
            'token': reset_token.token,
            'new_password': 'NewSecurePass123!',
            'new_password_confirm': 'NewSecurePass123!',
        }

        response = api_client.post(url, payload, format='json')

        assert response.status_code == 400
        assert 'detail' in response.data

    def test_password_reset_confirm_password_mismatch(
        self, api_client, authenticated_user
    ):
        """Test password reset fails when passwords don't match."""
        reset_token = PasswordResetTokenFactory.create(
            user=authenticated_user, used=False
        )

        url = reverse('password-reset-confirm')
        payload = {
            'token': reset_token.token,
            'new_password': 'NewSecurePass123!',
            'new_password_confirm': 'DifferentPass123!',
        }

        response = api_client.post(url, payload, format='json')

        assert response.status_code == 400
        assert 'new_password_confirm' in response.data

    def test_password_reset_confirm_missing_token(self, api_client):
        """Test password reset fails without token."""
        url = reverse('password-reset-confirm')
        payload = {
            'new_password': 'NewSecurePass123!',
            'new_password_confirm': 'NewSecurePass123!',
        }

        response = api_client.post(url, payload, format='json')

        assert response.status_code == 400
        assert 'token' in response.data

    def test_password_reset_confirm_weak_password(
        self, api_client, authenticated_user
    ):
        """Test password reset fails with weak password."""
        reset_token = PasswordResetTokenFactory.create(
            user=authenticated_user, used=False
        )

        url = reverse('password-reset-confirm')
        payload = {
            'token': reset_token.token,
            'new_password': '123',
            'new_password_confirm': '123',
        }

        response = api_client.post(url, payload, format='json')

        assert response.status_code == 400
        assert 'new_password' in response.data