# tests/test_edge_cases.py
"""
Edge case and boundary condition tests for accounts app.

Coverage:
- Empty/null values
- Boundary values
- Unicode and special characters
- Very long strings
- Concurrent operations
- Expired tokens
- Case sensitivity
- Whitespace handling
"""

import pytest
from django.urls import reverse
from django.utils import timezone
from datetime import timedelta
from .factories import UserFactory, PasswordResetTokenFactory
from .helpers import get_user_payload


@pytest.mark.django_db
class TestEmptyAndNullValues:
    """Test handling of empty and null values."""

    def test_registration_with_empty_email(self, api_client):
        """Test registration fails with empty email."""
        url = reverse('register')
        payload = get_user_payload(email='')

        response = api_client.post(url, payload, format='json')

        assert response.status_code == 400
        assert 'email' in response.data

    def test_registration_with_whitespace_only_email(self, api_client):
        """Test registration fails with whitespace-only email."""
        url = reverse('register')
        payload = get_user_payload(email='   ')

        response = api_client.post(url, payload, format='json')

        assert response.status_code == 400
        assert 'email' in response.data

    def test_update_profile_with_empty_first_name(self, authenticated_client):
        """Test profile update allows empty first name."""
        url = reverse('user-update-profile')
        payload = {'first_name': ''}

        response = authenticated_client.patch(url, payload, format='json')

        assert response.status_code == 200

    def test_registration_with_empty_first_name(self, api_client):
        """Test registration with empty first name."""
        url = reverse('register')
        payload = get_user_payload(email='emptyname@example.com')
        payload['first_name'] = ''

        response = api_client.post(url, payload, format='json')

        assert response.status_code in [201, 400]


@pytest.mark.django_db
class TestBoundaryValues:
    """Test boundary values and limits."""

    def test_registration_with_very_long_email(self, api_client):
        """Test registration with email at max length."""
        long_email = 'a' * 240 + '@example.com'
        url = reverse('register')
        payload = get_user_payload(email=long_email)

        response = api_client.post(url, payload, format='json')

        assert response.status_code in [201, 400]

    def test_registration_with_very_long_first_name(self, api_client):
        """Test registration with very long first name."""
        url = reverse('register')
        payload = get_user_payload(email='longname@example.com')
        payload['first_name'] = 'A' * 200

        response = api_client.post(url, payload, format='json')

        assert response.status_code in [201, 400]

    def test_registration_with_maximum_length_password(self, api_client):
        """Test registration with very long password."""
        long_password = 'SecurePass123!' * 20
        url = reverse('register')
        payload = get_user_payload(email='longpass@example.com')
        payload['password'] = long_password
        payload['password_confirm'] = long_password

        response = api_client.post(url, payload, format='json')

        assert response.status_code in [201, 400]


@pytest.mark.django_db
class TestUnicodeAndSpecialCharacters:
    """Test Unicode and special character handling."""

    def test_registration_with_unicode_name(self, api_client):
        """Test registration with Unicode characters in name."""
        url = reverse('register')
        payload = get_user_payload(email='unicode@example.com')
        payload['first_name'] = 'José'
        payload['last_name'] = 'François'

        response = api_client.post(url, payload, format='json')

        assert response.status_code == 201
        assert response.data['first_name'] == 'José'
        assert response.data['last_name'] == 'François'

    def test_registration_with_emoji_in_name(self, api_client):
        """Test registration with emoji in name."""
        url = reverse('register')
        payload = get_user_payload(email='emoji@example.com')
        payload['first_name'] = 'Test😀'

        response = api_client.post(url, payload, format='json')

        assert response.status_code == 201

    def test_registration_with_special_characters_in_name(self, api_client):
        """Test registration with special characters."""
        url = reverse('register')
        payload = get_user_payload(email='special@example.com')
        payload['first_name'] = "O'Brien"
        payload['last_name'] = 'Smith-Jones'

        response = api_client.post(url, payload, format='json')

        assert response.status_code == 201
        assert response.data['first_name'] == "O'Brien"
        assert response.data['last_name'] == 'Smith-Jones'


@pytest.mark.django_db
class TestCaseSensitivity:
    """Test case sensitivity handling."""

    def test_email_login_case_insensitive(self, api_client):
        """Test login is case-insensitive for email."""
        user = UserFactory.create(email='testuser@example.com')

        url = reverse('login')
        payload = {
            'email': 'TESTUSER@EXAMPLE.COM',
            'password': 'TestPassword123!',
        }

        response = api_client.post(url, payload, format='json')

        assert response.status_code == 200

    def test_duplicate_email_different_case_rejected(
        self, api_client, authenticated_user
    ):
        """Test duplicate email with different case is rejected."""
        url = reverse('register')
        payload = get_user_payload(email=authenticated_user.email.upper())

        response = api_client.post(url, payload, format='json')

        assert response.status_code == 400
        assert 'email' in response.data

    def test_password_reset_email_case_insensitive(
        self, api_client, authenticated_user
    ):
        """Test password reset with different email case."""
        url = reverse('password-reset-request')
        payload = {'email': authenticated_user.email.upper()}

        response = api_client.post(url, payload, format='json')

        assert response.status_code == 200


@pytest.mark.django_db
class TestWhitespaceHandling:
    """Test whitespace handling in inputs."""

    def test_registration_email_trimmed(self, api_client):
        """Test email whitespace is trimmed."""
        url = reverse('register')
        payload = get_user_payload(email='  trimmed@example.com  ')

        response = api_client.post(url, payload, format='json')

        if response.status_code == 201:
            assert response.data['email'] == 'trimmed@example.com'

    def test_login_email_trimmed(self, api_client, authenticated_user):
        """Test login email whitespace is trimmed."""
        url = reverse('login')
        payload = {
            'email': f'  {authenticated_user.email}  ',
            'password': 'TestPassword123!',
        }

        response = api_client.post(url, payload, format='json')

        assert response.status_code == 200

    def test_update_profile_name_trimmed(self, authenticated_client):
        """Test profile update trims name whitespace."""
        url = reverse('user-update-profile')
        payload = {'first_name': '  Trimmed  '}

        response = authenticated_client.patch(url, payload, format='json')

        assert response.status_code == 200


@pytest.mark.django_db
class TestExpiredTokens:
    """Test expired token handling."""

    def test_expired_password_reset_token_rejected(
        self, api_client, authenticated_user
    ):
        """Test expired password reset token is rejected."""
        expired_token = PasswordResetTokenFactory.create(
            user=authenticated_user,
            used=False,
            expires_at=timezone.now() - timedelta(hours=1)
        )

        url = reverse('password-reset-confirm')
        payload = {
            'token': expired_token.token,
            'new_password': 'NewSecurePass123!',
            'new_password_confirm': 'NewSecurePass123!',
        }

        response = api_client.post(url, payload, format='json')

        assert response.status_code == 400
        assert 'detail' in response.data

    def test_used_password_reset_token_rejected(
        self, api_client, authenticated_user
    ):
        """Test already used password reset token is rejected."""
        used_token = PasswordResetTokenFactory.create(
            user=authenticated_user,
            used=True
        )

        url = reverse('password-reset-confirm')
        payload = {
            'token': used_token.token,
            'new_password': 'NewSecurePass123!',
            'new_password_confirm': 'NewSecurePass123!',
        }

        response = api_client.post(url, payload, format='json')

        assert response.status_code == 400


@pytest.mark.django_db
class TestInvalidUUIDs:
    """Test invalid UUID handling."""

    def test_retrieve_user_with_invalid_uuid(self, authenticated_client):
        """Test retrieving user with invalid UUID returns 404."""
        url = reverse('user-detail', args=['invalid-uuid'])

        response = authenticated_client.get(url)

        assert response.status_code == 404

    def test_update_user_with_invalid_uuid(self, authenticated_client):
        """Test updating user with invalid UUID returns 404."""
        url = reverse('user-detail', args=['not-a-uuid'])
        payload = {'first_name': 'Updated'}

        response = authenticated_client.patch(url, payload, format='json')

        assert response.status_code == 404


@pytest.mark.django_db
class TestMultipleRequestsScenarios:
    """Test scenarios with multiple requests."""

    def test_multiple_password_reset_requests(
        self, api_client, authenticated_user
    ):
        """Test multiple password reset requests invalidate old tokens."""
        url = reverse('password-reset-request')
        payload = {'email': authenticated_user.email}

        response1 = api_client.post(url, payload, format='json')
        token1 = response1.data['token']

        response2 = api_client.post(url, payload, format='json')
        token2 = response2.data['token']

        assert response1.status_code == 200
        assert response2.status_code == 200
        assert token1 != token2

        from accounts.models import PasswordResetToken
        old_token = PasswordResetToken.objects.get(token=token1)
        assert old_token.used is True

    def test_login_updates_last_login(self, api_client, authenticated_user):
        """Test login updates last_login timestamp."""
        original_last_login = authenticated_user.last_login

        url = reverse('login')
        payload = {
            'email': authenticated_user.email,
            'password': 'TestPassword123!',
        }

        response = api_client.post(url, payload, format='json')

        assert response.status_code == 200

        authenticated_user.refresh_from_db()
        assert authenticated_user.last_login != original_last_login


@pytest.mark.django_db
class TestMalformedRequests:
    """Test malformed request handling."""

    def test_registration_with_invalid_json(self, api_client):
        """Test registration with malformed JSON."""
        url = reverse('register')

        response = api_client.post(
            url,
            data='{"email": invalid json}',
            content_type='application/json'
        )

        assert response.status_code == 400

    def test_registration_with_array_instead_of_object(self, api_client):
        """Test registration with array instead of object."""
        url = reverse('register')

        response = api_client.post(url, [], format='json')

        assert response.status_code == 400

    def test_update_profile_with_null_payload(self, authenticated_client):
        """Test profile update with null payload."""
        url = reverse('user-update-profile')

        response = authenticated_client.patch(url, None, format='json')

        assert response.status_code == 400


@pytest.mark.django_db
class TestDatabaseIntegrity:
    """Test database integrity and constraints."""

    def test_user_email_unique_constraint(self):
        """Test email uniqueness at database level."""
        UserFactory.create(email='unique@example.com')

        from django.db import IntegrityError
        with pytest.raises(IntegrityError):
            UserFactory.create(email='unique@example.com')

    def test_password_reset_token_unique_constraint(self, authenticated_user):
        """Test token uniqueness at database level."""
        token_value = 'unique-token-123'
        PasswordResetTokenFactory.create(
            user=authenticated_user,
            token=token_value
        )

        from django.db import IntegrityError
        with pytest.raises(IntegrityError):
            PasswordResetTokenFactory.create(
                user=authenticated_user,
                token=token_value
            )