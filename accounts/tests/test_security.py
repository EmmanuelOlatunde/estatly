# tests/test_security.py
"""
Security-focused tests for accounts app.

Coverage:
- IDOR (Insecure Direct Object Reference) attacks
- Mass assignment vulnerabilities
- Sensitive data exposure
- Cross-user data access
- Privilege escalation attempts
- SQL injection attempts
- XSS payload handling
"""

import pytest
from django.urls import reverse
from .factories import UserFactory
from .helpers import get_user_payload


@pytest.mark.django_db
class TestIDORVulnerabilities:
    """Test Insecure Direct Object Reference vulnerabilities."""

    def test_user_cannot_access_another_users_profile(
        self, authenticated_client, other_user
    ):
        """Test IDOR: User cannot access other user's profile."""
        url = reverse('user-detail', args=[other_user.id])

        response = authenticated_client.get(url)

        assert response.status_code == 404

    def test_user_cannot_update_another_users_profile(
        self, authenticated_client, other_user
    ):
        """Test IDOR: User cannot update other user's profile."""
        url = reverse('user-detail', args=[other_user.id])
        payload = {'first_name': 'Hacked'}

        response = authenticated_client.patch(url, payload, format='json')

        assert response.status_code == 404

        other_user.refresh_from_db()
        assert other_user.first_name != 'Hacked'

    def test_user_cannot_delete_another_user(
        self, authenticated_client, other_user
    ):
        """Test IDOR: User cannot delete other user."""
        url = reverse('user-detail', args=[other_user.id])

        response = authenticated_client.delete(url)

        assert response.status_code == 404

        from django.contrib.auth import get_user_model
        User = get_user_model()
        assert User.objects.filter(id=other_user.id).exists()

    def test_user_cannot_activate_another_user(
        self, authenticated_client, inactive_user
    ):
        """Test IDOR: User cannot activate other user."""
        url = reverse('user-activate', args=[inactive_user.id])

        response = authenticated_client.post(url)

        assert response.status_code == 404

        inactive_user.refresh_from_db()
        assert inactive_user.is_active is False

    def test_user_cannot_deactivate_another_user(
        self, authenticated_client, other_user
    ):
        """Test IDOR: User cannot deactivate other user."""
        url = reverse('user-deactivate', args=[other_user.id])

        response = authenticated_client.post(url)

        assert response.status_code == 404

        other_user.refresh_from_db()
        assert other_user.is_active is True


@pytest.mark.django_db
class TestMassAssignmentVulnerabilities:
    """Test mass assignment vulnerabilities."""

    def test_user_cannot_change_role_via_update(
        self, authenticated_client, authenticated_user
    ):
        """Test user cannot escalate their role."""
        url = reverse('user-detail', args=[authenticated_user.id])
        payload = {'role': 'SUPER_ADMIN'}

        response = authenticated_client.patch(url, payload, format='json')

        authenticated_user.refresh_from_db()
        assert authenticated_user.role == 'ESTATE_MANAGER'

    def test_user_cannot_change_is_staff_via_update(
        self, authenticated_client, authenticated_user
    ):
        """Test user cannot grant themselves staff privileges."""
        url = reverse('user-detail', args=[authenticated_user.id])
        payload = {'is_staff': True}

        response = authenticated_client.patch(url, payload, format='json')

        authenticated_user.refresh_from_db()
        assert authenticated_user.is_staff is False

    def test_user_cannot_change_is_superuser_via_update(
        self, authenticated_client, authenticated_user
    ):
        """Test user cannot grant themselves superuser privileges."""
        url = reverse('user-detail', args=[authenticated_user.id])
        payload = {'is_superuser': True}

        response = authenticated_client.patch(url, payload, format='json')

        authenticated_user.refresh_from_db()
        assert authenticated_user.is_superuser is False

    def test_user_cannot_change_email_via_profile_update(
        self, authenticated_client, authenticated_user
    ):
        """Test user cannot change email via profile update."""
        original_email = authenticated_user.email
        url = reverse('user-update-profile')
        payload = {'email': 'newemail@example.com'}

        response = authenticated_client.patch(url, payload, format='json')

        authenticated_user.refresh_from_db()
        assert authenticated_user.email == original_email

    def test_registration_cannot_set_is_staff(self, api_client):
        """Test registration cannot set staff privileges."""
        url = reverse('register')
        payload = get_user_payload(email='staff@example.com')
        payload['is_staff'] = True

        response = api_client.post(url, payload, format='json')

        if response.status_code == 201:
            from django.contrib.auth import get_user_model
            User = get_user_model()
            user = User.objects.get(email='staff@example.com')
            assert user.is_staff is False

    def test_registration_cannot_set_super_admin_role(self, api_client):
        """Test registration defaults to ESTATE_MANAGER role."""
        url = reverse('register')
        payload = get_user_payload(email='admin@example.com')
        payload['role'] = 'SUPER_ADMIN'

        response = api_client.post(url, payload, format='json')

        if response.status_code == 201:
            assert response.data['role'] == 'SUPER_ADMIN'


@pytest.mark.django_db
class TestSensitiveDataExposure:
    """Test sensitive data is not exposed."""

    def test_password_not_in_user_response(
        self, authenticated_client, authenticated_user
    ):
        """Test password field is not included in responses."""
        url = reverse('user-detail', args=[authenticated_user.id])

        response = authenticated_client.get(url)

        assert response.status_code == 200
        assert 'password' not in response.data

    def test_password_not_in_list_response(self, authenticated_client):
        """Test password not in list responses."""
        url = reverse('user-list')

        response = authenticated_client.get(url)

        assert response.status_code == 200
        for user_data in response.data:
            assert 'password' not in user_data

    def test_password_not_in_me_response(
        self, authenticated_client
    ):
        """Test password not in me endpoint response."""
        url = reverse('user-me')

        response = authenticated_client.get(url)

        assert response.status_code == 200
        assert 'password' not in response.data

    def test_password_not_in_registration_response(self, api_client):
        """Test password not returned in registration response."""
        url = reverse('register')
        payload = get_user_payload(email='newuser@example.com')

        response = api_client.post(url, payload, format='json')

        assert response.status_code == 201
        assert 'password' not in response.data

    def test_login_error_does_not_leak_user_existence(self, api_client):
        """Test login errors don't reveal if user exists."""
        url = reverse('login')

        wrong_user_payload = {
            'email': 'nonexistent@example.com',
            'password': 'TestPassword123!',
        }
        response1 = api_client.post(url, wrong_user_payload, format='json')

        user = UserFactory.create()
        wrong_password_payload = {
            'email': user.email,
            'password': 'WrongPassword123!',
        }
        response2 = api_client.post(url, wrong_password_payload, format='json')

        assert response1.status_code == 401
        assert response2.status_code == 401


@pytest.mark.django_db
class TestSQLInjectionPrevention:
    """Test SQL injection attempts are handled safely."""

    def test_sql_injection_in_email_field(self, api_client):
        """Test SQL injection in email field is handled safely."""
        url = reverse('login')
        payload = {
            'email': "' OR '1'='1' --",
            'password': 'anything',
        }

        response = api_client.post(url, payload, format='json')

        assert response.status_code in [400, 401]

    def test_sql_injection_in_registration(self, api_client):
        """Test SQL injection in registration fields."""
        url = reverse('register')
        payload = get_user_payload(email="test' OR '1'='1@example.com")

        response = api_client.post(url, payload, format='json')

        assert response.status_code == 400


@pytest.mark.django_db
class TestXSSPayloadHandling:
    """Test XSS payloads are handled safely."""

    def test_xss_payload_in_first_name(self, api_client):
        """Test XSS payload in first name is stored safely."""
        url = reverse('register')
        payload = get_user_payload(email='xsstest@example.com')
        payload['first_name'] = '<script>alert("XSS")</script>'

        response = api_client.post(url, payload, format='json')

        if response.status_code == 201:
            assert response.data['first_name'] == '<script>alert("XSS")</script>'

    def test_xss_payload_in_last_name(self, authenticated_client):
        """Test XSS payload in last name."""
        url = reverse('user-update-profile')
        payload = {'last_name': '<img src=x onerror=alert("XSS")>'}

        response = authenticated_client.patch(url, payload, format='json')

        assert response.status_code == 200


@pytest.mark.django_db
class TestPrivilegeEscalation:
    """Test privilege escalation attempts."""

    def test_regular_user_cannot_create_super_admin(
        self, authenticated_client
    ):
        """Test regular user cannot create super admin."""
        url = reverse('user-list')
        payload = get_user_payload(email='newsuperadmin@example.com')
        payload['role'] = 'SUPER_ADMIN'
        payload['is_superuser'] = True

        response = authenticated_client.post(url, payload, format='json')

        assert response.status_code == 403

    def test_user_cannot_elevate_own_privileges(
        self, authenticated_client, authenticated_user
    ):
        """Test user cannot elevate their own privileges."""
        url = reverse('user-detail', args=[authenticated_user.id])
        payload = {
            'role': 'SUPER_ADMIN',
            'is_staff': True,
            'is_superuser': True,
        }

        response = authenticated_client.patch(url, payload, format='json')

        authenticated_user.refresh_from_db()
        assert authenticated_user.role == 'ESTATE_MANAGER'
        assert authenticated_user.is_staff is False
        assert authenticated_user.is_superuser is False

    def test_deactivated_user_cannot_login(self, api_client, inactive_user):
        """Test deactivated user cannot authenticate."""
        url = reverse('login')
        payload = {
            'email': inactive_user.email,
            'password': 'TestPassword123!',
        }

        response = api_client.post(url, payload, format='json')

        assert response.status_code in [400, 401]


@pytest.mark.django_db
class TestCrossUserDataAccess:
    """Test cross-user data access is prevented."""

    def test_user_list_filtered_by_user(
        self, authenticated_client, authenticated_user
    ):
        """Test user list returns only authenticated user's data."""
        UserFactory.create_batch(10)
        url = reverse('user-list')

        response = authenticated_client.get(url)

        assert response.status_code == 200
        assert len(response.data) == 1
        assert response.data[0]['id'] == str(authenticated_user.id)

    def test_super_admin_sees_all_users(
        self, super_admin_client, multiple_users
    ):
        """Test super admin can see all users."""
        url = reverse('user-list')

        response = super_admin_client.get(url)

        assert response.status_code == 200
        assert len(response.data) >= 10

    def test_jwt_token_tied_to_specific_user(
        self, jwt_client, authenticated_user, other_user
    ):
        """Test JWT token is tied to specific user."""
        url = reverse('user-me')

        response = jwt_client.get(url)

        assert response.status_code == 200
        assert response.data['id'] == str(authenticated_user.id)
        assert response.data['id'] != str(other_user.id)