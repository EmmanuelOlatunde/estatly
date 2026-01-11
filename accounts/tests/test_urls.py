# tests/test_urls.py
"""
Tests for accounts app URL routing.

Coverage:
- URL patterns resolve correctly
- reverse() generates correct URLs
- URL namespaces work as expected
"""

import pytest
from django.urls import reverse, resolve


@pytest.mark.django_db
class TestAccountsURLs:
    """Test URL routing for accounts app."""

    def test_register_url_resolves(self):
        """Test register URL resolves correctly."""
        url = reverse('register')
        assert url == '/api/accounts/auth/register/'
        resolver = resolve(url)
        assert resolver.view_name == 'register'

    def test_login_url_resolves(self):
        """Test login URL resolves correctly."""
        url = reverse('login')
        assert url == '/api/accounts/auth/login/'
        resolver = resolve(url)
        assert resolver.view_name == 'login'

    def test_password_reset_request_url_resolves(self):
        """Test password reset request URL resolves correctly."""
        url = reverse('password-reset-request')
        assert url == '/api/accounts/auth/password-reset/'
        resolver = resolve(url)
        assert resolver.view_name == 'password-reset-request'

    def test_password_reset_confirm_url_resolves(self):
        """Test password reset confirm URL resolves correctly."""
        url = reverse('password-reset-confirm')
        assert url == '/api/accounts/auth/password-reset/confirm/'
        resolver = resolve(url)
        assert resolver.view_name == 'password-reset-confirm'

    def test_user_list_url_resolves(self):
        """Test user list URL resolves correctly."""
        url = reverse('user-list')
        assert url == '/api/accounts/users/'

    def test_user_detail_url_resolves(self, user):
        """Test user detail URL resolves correctly."""
        url = reverse('user-detail', args=[user.id])
        assert url == f'/api/accounts/users/{user.id}/'

    def test_user_me_url_resolves(self):
        """Test user me URL resolves correctly."""
        url = reverse('user-me')
        assert url == '/api/accounts/users/me/'

    def test_user_update_profile_url_resolves(self):
        """Test update profile URL resolves correctly."""
        url = reverse('user-update-profile')
        assert url == '/api/accounts/users/update_profile/'

    def test_user_change_password_url_resolves(self):
        """Test change password URL resolves correctly."""
        url = reverse('user-change-password')
        assert url == '/api/accounts/users/change_password/'

    def test_user_activate_url_resolves(self, user):
        """Test user activate URL resolves correctly."""
        url = reverse('user-activate', args=[user.id])
        assert url == f'/api/accounts/users/{user.id}/activate/'

    def test_user_deactivate_url_resolves(self, user):
        """Test user deactivate URL resolves correctly."""
        url = reverse('user-deactivate', args=[user.id])
        assert url == f'/api/accounts/users/{user.id}/deactivate/'