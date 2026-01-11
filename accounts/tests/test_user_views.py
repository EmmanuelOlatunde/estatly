# tests/test_user_views.py
"""
Tests for user management views.

Coverage:
- User list endpoint
- User detail endpoint
- User create endpoint
- User update endpoint
- User delete endpoint
- Current user (me) endpoint
- Update profile endpoint
- Change password endpoint
- Activate/deactivate endpoints
- Authentication/authorization for all endpoints
"""

import pytest
from django.urls import reverse
from django.contrib.auth import get_user_model
from .factories import UserFactory
from .helpers import assert_user_response_structure, get_user_payload

User = get_user_model()


@pytest.mark.django_db
class TestUserListView:
    """Test user list endpoint."""

    def test_unauthenticated_user_cannot_list_users(self, api_client):
        """Test unauthenticated request returns 401."""
        url = reverse('user-list')
        response = api_client.get(url)
        assert response.status_code == 401

    def test_authenticated_user_can_list_only_self(
        self, authenticated_client, authenticated_user
    ):
        """Test regular user can only see themselves."""
        UserFactory.create_batch(5)
        url = reverse('user-list')

        response = authenticated_client.get(url)

        assert response.status_code == 200
        assert len(response.data) == 1
        assert response.data[0]['id'] == str(authenticated_user.id)

    def test_super_admin_can_list_all_users(
        self, super_admin_client, super_admin, multiple_users
    ):
        """Test super admin can see all users."""
        url = reverse('user-list')

        response = super_admin_client.get(url)

        assert response.status_code == 200
        assert len(response.data) >= 10

    def test_list_users_response_structure(self, authenticated_client):
        """Test list response has correct structure."""
        url = reverse('user-list')

        response = authenticated_client.get(url)

        assert response.status_code == 200
        assert isinstance(response.data, list)
        if len(response.data) > 0:
            assert_user_response_structure(response.data[0])

    def test_jwt_authentication_works_for_list(self, jwt_client):
        """Test JWT token authentication works."""
        url = reverse('user-list')
        response = jwt_client.get(url)
        assert response.status_code == 200


@pytest.mark.django_db
class TestUserRetrieveView:
    """Test user detail endpoint."""

    def test_unauthenticated_user_cannot_retrieve_user(self, api_client, user):
        """Test unauthenticated request returns 401."""
        url = reverse('user-detail', args=[user.id])
        response = api_client.get(url)
        assert response.status_code == 401

    def test_user_can_retrieve_own_profile(
        self, authenticated_client, authenticated_user
    ):
        """Test user can retrieve their own profile."""
        url = reverse('user-detail', args=[authenticated_user.id])

        response = authenticated_client.get(url)

        assert response.status_code == 200
        assert_user_response_structure(response.data)
        assert response.data['id'] == str(authenticated_user.id)

    def test_user_cannot_retrieve_other_user(
        self, authenticated_client, other_user
    ):
        """Test user cannot retrieve another user's profile."""
        url = reverse('user-detail', args=[other_user.id])

        response = authenticated_client.get(url)

        assert response.status_code == 404

    def test_super_admin_can_retrieve_any_user(
        self, super_admin_client, other_user
    ):
        """Test super admin can retrieve any user."""
        url = reverse('user-detail', args=[other_user.id])

        response = super_admin_client.get(url)

        assert response.status_code == 200
        assert response.data['id'] == str(other_user.id)

    def test_retrieve_nonexistent_user_returns_404(self, authenticated_client):
        """Test retrieving non-existent user returns 404."""
        from uuid import uuid4
        url = reverse('user-detail', args=[uuid4()])

        response = authenticated_client.get(url)

        assert response.status_code == 404


@pytest.mark.django_db
class TestUserCreateView:
    """Test user create endpoint."""

    def test_super_admin_can_create_user(self, super_admin_client):
        """Test super admin can create new user."""
        url = reverse('user-list')
        payload = get_user_payload(email='newadminuser@example.com')

        response = super_admin_client.post(url, payload, format='json')

        assert response.status_code == 201
        assert response.data['email'] == 'newadminuser@example.com'

        user = User.objects.get(email='newadminuser@example.com')
        assert user is not None

    def test_regular_user_cannot_create_user(self, authenticated_client):
        """Test regular user cannot create new user."""
        url = reverse('user-list')
        payload = get_user_payload(email='newuser@example.com')

        response = authenticated_client.post(url, payload, format='json')

        assert response.status_code == 403

    def test_unauthenticated_user_cannot_create_user(self, api_client):
        """Test unauthenticated user cannot create user."""
        url = reverse('user-list')
        payload = get_user_payload(email='newuser@example.com')

        response = api_client.post(url, payload, format='json')

        assert response.status_code == 401


@pytest.mark.django_db
class TestUserUpdateView:
    """Test user update endpoint."""

    def test_user_can_update_own_profile(
        self, authenticated_client, authenticated_user
    ):
        """Test user can update their own profile."""
        url = reverse('user-detail', args=[authenticated_user.id])
        payload = {'first_name': 'Updated', 'last_name': 'Name'}

        response = authenticated_client.patch(url, payload, format='json')

        assert response.status_code == 200
        assert response.data['first_name'] == 'Updated'
        assert response.data['last_name'] == 'Name'

        authenticated_user.refresh_from_db()
        assert authenticated_user.first_name == 'Updated'
        assert authenticated_user.last_name == 'Name'

    def test_user_cannot_update_other_user(
        self, authenticated_client, other_user
    ):
        """Test user cannot update another user's profile."""
        url = reverse('user-detail', args=[other_user.id])
        payload = {'first_name': 'Hacked'}

        response = authenticated_client.patch(url, payload, format='json')

        assert response.status_code == 404

    def test_super_admin_can_update_any_user(
        self, super_admin_client, other_user
    ):
        """Test super admin can update any user."""
        url = reverse('user-detail', args=[other_user.id])
        payload = {'first_name': 'AdminUpdated'}

        response = super_admin_client.patch(url, payload, format='json')

        assert response.status_code == 200
        assert response.data['first_name'] == 'AdminUpdated'

    def test_unauthenticated_user_cannot_update(self, api_client, user):
        """Test unauthenticated user cannot update."""
        url = reverse('user-detail', args=[user.id])
        payload = {'first_name': 'Updated'}

        response = api_client.patch(url, payload, format='json')

        assert response.status_code == 401


@pytest.mark.django_db
class TestUserDeleteView:
    """Test user delete endpoint."""

    def test_super_admin_can_delete_user(self, super_admin_client, other_user):
        """Test super admin can delete users."""
        url = reverse('user-detail', args=[other_user.id])

        response = super_admin_client.delete(url)

        assert response.status_code == 204
        assert not User.objects.filter(id=other_user.id).exists()

    def test_regular_user_cannot_delete_user(
        self, authenticated_client, other_user
    ):
        """Test regular user cannot delete users."""
        url = reverse('user-detail', args=[other_user.id])

        response = authenticated_client.delete(url)

        assert response.status_code == 404

    def test_user_cannot_delete_self(
        self, authenticated_client, authenticated_user
    ):
        """Test user cannot delete themselves via delete endpoint."""
        url = reverse('user-detail', args=[authenticated_user.id])

        response = authenticated_client.delete(url)

        assert response.status_code in [403, 404]


@pytest.mark.django_db
class TestUserMeView:
    """Test current user (me) endpoint."""

    def test_authenticated_user_can_get_own_profile(
        self, authenticated_client, authenticated_user
    ):
        """Test authenticated user can get their own profile."""
        url = reverse('user-me')

        response = authenticated_client.get(url)

        assert response.status_code == 200
        assert_user_response_structure(response.data)
        assert response.data['id'] == str(authenticated_user.id)
        assert response.data['email'] == authenticated_user.email

    def test_unauthenticated_user_cannot_access_me(self, api_client):
        """Test unauthenticated user cannot access me endpoint."""
        url = reverse('user-me')

        response = api_client.get(url)

        assert response.status_code == 401

    def test_jwt_authentication_works_for_me(self, jwt_client, authenticated_user):
        """Test JWT authentication works for me endpoint."""
        url = reverse('user-me')

        response = jwt_client.get(url)

        assert response.status_code == 200
        assert response.data['email'] == authenticated_user.email


@pytest.mark.django_db
class TestUpdateProfileView:
    """Test update profile endpoint."""

    def test_update_profile_success(
        self, authenticated_client, authenticated_user
    ):
        """Test successful profile update."""
        url = reverse('user-update-profile')
        payload = {'first_name': 'UpdatedFirst', 'last_name': 'UpdatedLast'}

        response = authenticated_client.patch(url, payload, format='json')

        assert response.status_code == 200
        assert response.data['first_name'] == 'UpdatedFirst'
        assert response.data['last_name'] == 'UpdatedLast'

        authenticated_user.refresh_from_db()
        assert authenticated_user.first_name == 'UpdatedFirst'
        assert authenticated_user.last_name == 'UpdatedLast'

    def test_update_profile_partial(self, authenticated_client):
        """Test partial profile update."""
        url = reverse('user-update-profile')
        payload = {'first_name': 'OnlyFirst'}

        response = authenticated_client.patch(url, payload, format='json')

        assert response.status_code == 200
        assert response.data['first_name'] == 'OnlyFirst'

    def test_unauthenticated_user_cannot_update_profile(self, api_client):
        """Test unauthenticated user cannot update profile."""
        url = reverse('user-update-profile')
        payload = {'first_name': 'Hacker'}

        response = api_client.patch(url, payload, format='json')

        assert response.status_code == 401


@pytest.mark.django_db
class TestChangePasswordView:
    """Test change password endpoint."""

    def test_change_password_success(
        self, authenticated_client, authenticated_user
    ):
        """Test successful password change."""
        url = reverse('user-change-password')
        payload = {
            'old_password': 'TestPassword123!',
            'new_password': 'NewSecurePass123!',
            'new_password_confirm': 'NewSecurePass123!',
        }

        response = authenticated_client.post(url, payload, format='json')

        assert response.status_code == 200
        assert 'detail' in response.data

        authenticated_user.refresh_from_db()
        assert authenticated_user.check_password('NewSecurePass123!')

    def test_change_password_wrong_old_password(self, authenticated_client):
        """Test password change fails with wrong old password."""
        url = reverse('user-change-password')
        payload = {
            'old_password': 'WrongPassword123!',
            'new_password': 'NewSecurePass123!',
            'new_password_confirm': 'NewSecurePass123!',
        }

        response = authenticated_client.post(url, payload, format='json')

        assert response.status_code == 400
        assert 'old_password' in response.data

    def test_change_password_mismatch(self, authenticated_client):
        """Test password change fails when new passwords don't match."""
        url = reverse('user-change-password')
        payload = {
            'old_password': 'TestPassword123!',
            'new_password': 'NewSecurePass123!',
            'new_password_confirm': 'DifferentPass123!',
        }

        response = authenticated_client.post(url, payload, format='json')

        assert response.status_code == 400
        assert 'new_password_confirm' in response.data

    def test_change_password_weak_password(self, authenticated_client):
        """Test password change fails with weak password."""
        url = reverse('user-change-password')
        payload = {
            'old_password': 'TestPassword123!',
            'new_password': '123',
            'new_password_confirm': '123',
        }

        response = authenticated_client.post(url, payload, format='json')

        assert response.status_code == 400
        assert 'new_password' in response.data

    def test_unauthenticated_user_cannot_change_password(self, api_client):
        """Test unauthenticated user cannot change password."""
        url = reverse('user-change-password')
        payload = {
            'old_password': 'TestPassword123!',
            'new_password': 'NewSecurePass123!',
            'new_password_confirm': 'NewSecurePass123!',
        }

        response = api_client.post(url, payload, format='json')

        assert response.status_code == 401


@pytest.mark.django_db
class TestActivateDeactivateViews:
    """Test user activate/deactivate endpoints."""

    def test_super_admin_can_deactivate_user(
        self, super_admin_client, other_user
    ):
        """Test super admin can deactivate users."""
        url = reverse('user-deactivate', args=[other_user.id])

        response = super_admin_client.post(url)

        assert response.status_code == 200
        assert 'detail' in response.data

        other_user.refresh_from_db()
        assert other_user.is_active is False

    def test_cannot_deactivate_super_admin(
        self, super_admin_client, super_admin
    ):
        """Test cannot deactivate super admin account."""
        other_admin = UserFactory.create(
            role='SUPER_ADMIN', is_staff=True, is_superuser=True
        )
        url = reverse('user-deactivate', args=[other_admin.id])

        response = super_admin_client.post(url)

        assert response.status_code == 400
        assert 'detail' in response.data

    def test_regular_user_cannot_deactivate_user(
        self, authenticated_client, other_user
    ):
        """Test regular user cannot deactivate users."""
        url = reverse('user-deactivate', args=[other_user.id])

        response = authenticated_client.post(url)

        assert response.status_code == 404

    def test_super_admin_can_activate_user(
        self, super_admin_client, inactive_user
    ):
        """Test super admin can activate users."""
        url = reverse('user-activate', args=[inactive_user.id])

        response = super_admin_client.post(url)

        assert response.status_code == 200
        assert 'detail' in response.data

        inactive_user.refresh_from_db()
        assert inactive_user.is_active is True

    def test_regular_user_cannot_activate_user(
        self, authenticated_client, inactive_user
    ):
        """Test regular user cannot activate users."""
        url = reverse('user-activate', args=[inactive_user.id])

        response = authenticated_client.post(url)

        assert response.status_code == 404

    def test_unauthenticated_user_cannot_deactivate(self, api_client, user):
        """Test unauthenticated user cannot deactivate."""
        url = reverse('user-deactivate', args=[user.id])

        response = api_client.post(url)

        assert response.status_code == 401

    def test_unauthenticated_user_cannot_activate(self, api_client, inactive_user):
        """Test unauthenticated user cannot activate."""
        url = reverse('user-activate', args=[inactive_user.id])

        response = api_client.post(url)

        assert response.status_code == 401