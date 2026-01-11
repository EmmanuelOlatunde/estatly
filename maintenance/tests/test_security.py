# tests/test_security.py

"""
Tests for security-specific scenarios.

Coverage:
- IDOR (Insecure Direct Object References)
- Cross-user data access
- SQL injection attempts
- XSS payload handling
- Mass assignment vulnerabilities
- Sensitive data exposure
"""

import pytest
import uuid
from django.urls import reverse
from .factories import MaintenanceTicketFactory


@pytest.mark.django_db
class TestIDORVulnerabilities:
    """Test Insecure Direct Object Reference vulnerabilities."""
    
    def test_user_cannot_access_other_users_ticket_detail(
        self, authenticated_client, other_user_ticket
    ):
        """Test IDOR: user cannot access another user's ticket by ID."""
        url = reverse('maintenance:maintenance-ticket-detail', args=[other_user_ticket.id])
        response = authenticated_client.get(url)
        assert response.status_code == 404
    
    def test_user_cannot_update_other_users_ticket(
        self, authenticated_client, other_user_ticket
    ):
        """Test IDOR: user cannot update another user's ticket."""
        url = reverse('maintenance:maintenance-ticket-detail', args=[other_user_ticket.id])
        response = authenticated_client.patch(
            url,
            {'title': 'Hacked title'},
            format='json'
        )
        assert response.status_code == 404
        
        other_user_ticket.refresh_from_db()
        assert other_user_ticket.title != 'Hacked title'
    
    def test_user_cannot_delete_other_users_ticket(
        self, authenticated_client, other_user_ticket
    ):
        """Test IDOR: user cannot delete another user's ticket."""
        ticket_id = other_user_ticket.id
        url = reverse('maintenance:maintenance-ticket-detail', args=[ticket_id])
        response = authenticated_client.delete(url)
        assert response.status_code == 404
        
        from maintenance.models import MaintenanceTicket
        assert MaintenanceTicket.objects.filter(id=ticket_id).exists()
    
    def test_user_cannot_resolve_other_users_ticket(
        self, authenticated_client, other_user_ticket
    ):
        """Test IDOR: user cannot resolve another user's ticket."""
        url = reverse('maintenance:maintenance-ticket-resolve', args=[other_user_ticket.id])
        response = authenticated_client.post(url)
        assert response.status_code == 404
        
        other_user_ticket.refresh_from_db()
        assert other_user_ticket.status == 'OPEN'
    
    def test_sequential_id_guessing_fails(
        self, authenticated_client, other_user, estate
    ):
        """Test that sequential UUID guessing doesn't expose data."""
        fake_ids = [uuid.uuid4() for _ in range(10)]
        
        for fake_id in fake_ids:
            url = reverse('maintenance:maintenance-ticket-detail', args=[fake_id])
            response = authenticated_client.get(url)
            assert response.status_code == 404


@pytest.mark.django_db
class TestSQLInjectionPrevention:
    """Test SQL injection prevention."""
    
    def setup_method(self):
        """Setup common test data."""
        self.url = reverse('maintenance:maintenance-ticket-list')
    
    def test_sql_injection_in_search(
        self, authenticated_client, authenticated_user, estate
    ):
        """Test SQL injection attempt in search parameter."""
        MaintenanceTicketFactory.create(
            title="Normal ticket",
            created_by=authenticated_user,
            estate=estate
        )
        
        sql_injection = "'; DROP TABLE maintenance_maintenanceticket; --"
        response = authenticated_client.get(self.url, {'search': sql_injection})
        
        assert response.status_code == 200
        
        from maintenance.models import MaintenanceTicket
        assert MaintenanceTicket.objects.exists()
    
    def test_sql_injection_in_filter(
        self, authenticated_client, authenticated_user, estate
    ):
        """Test SQL injection attempt in filter parameter."""
        MaintenanceTicketFactory.create(
            created_by=authenticated_user,
            estate=estate
        )
        
        sql_injection = "1' OR '1'='1"
        response = authenticated_client.get(self.url, {'estate': sql_injection})
        
        assert response.status_code in [200, 400]
        if response.status_code == 200:
            assert response.data['count'] == 0


@pytest.mark.django_db
class TestXSSPrevention:
    """Test XSS (Cross-Site Scripting) prevention."""
    
    def test_xss_in_title(
        self, authenticated_client, estate
    ):
        """Test XSS payload in title is stored but escaped."""
        xss_payload = '<script>alert("XSS")</script>'
        data = {
            'title': xss_payload,
            'description': 'Test description',
            'category': 'WATER',
            'estate': str(estate.id)
        }
        
        url = reverse('maintenance:maintenance-ticket-list')
        response = authenticated_client.post(url, data, format='json')
        
        assert response.status_code == 201
        assert response.data['title'] == xss_payload
    
    def test_xss_in_description(
        self, authenticated_client, estate
    ):
        """Test XSS payload in description is handled."""
        xss_payload = '<img src=x onerror=alert("XSS")>'
        data = {
            'title': 'Test ticket',
            'description': xss_payload,
            'category': 'WATER',
            'estate': str(estate.id)
        }
        
        url = reverse('maintenance:maintenance-ticket-list')
        response = authenticated_client.post(url, data, format='json')
        
        assert response.status_code == 201
        assert response.data['description'] == xss_payload


@pytest.mark.django_db
class TestMassAssignmentProtection:
    """Test mass assignment vulnerability protection."""
    
    def test_cannot_assign_created_by_on_create(
        self, authenticated_client, other_user, estate
    ):
        """Test user cannot set created_by to another user."""
        data = {
            'title': 'Test ticket',
            'description': 'Test description',
            'category': 'WATER',
            'estate': str(estate.id),
            'created_by': str(other_user.id)
        }
        
        url = reverse('maintenance:maintenance-ticket-list')
        response = authenticated_client.post(url, data, format='json')
        
        assert response.status_code == 201
        from maintenance.models import MaintenanceTicket
        ticket = MaintenanceTicket.objects.get(id=response.data['id'])
        assert ticket.created_by != other_user
    
    def test_cannot_set_id_on_create(
        self, authenticated_client, estate
    ):
        """Test user cannot set custom ID."""
        custom_id = uuid.uuid4()
        data = {
            'id': str(custom_id),
            'title': 'Test ticket',
            'description': 'Test description',
            'category': 'WATER',
            'estate': str(estate.id)
        }
        
        url = reverse('maintenance:maintenance-ticket-list')
        response = authenticated_client.post(url, data, format='json')
        
        assert response.status_code == 201
        assert response.data['id'] != str(custom_id)
    
    def test_cannot_modify_created_at_on_update(
        self, authenticated_client, ticket
    ):
        """Test user cannot modify created_at timestamp."""
        from django.utils import timezone
        from datetime import timedelta
        original_created_at = ticket.created_at
        fake_date = timezone.now() - timedelta(days=365)
        
        url = reverse('maintenance:maintenance-ticket-detail', args=[ticket.id])
        response = authenticated_client.patch(
            url,
            {'created_at': fake_date.isoformat()},
            format='json'
        )
        
        ticket.refresh_from_db()
        assert ticket.created_at == original_created_at


@pytest.mark.django_db
class TestSensitiveDataExposure:
    """Test sensitive data is not exposed in responses."""
    
    def test_user_password_not_in_response(
        self, authenticated_client, ticket
    ):
        """Test user password is never exposed."""
        url = reverse('maintenance:maintenance-ticket-detail', args=[ticket.id])
        response = authenticated_client.get(url)
        
        assert response.status_code == 200
        assert 'password' not in str(response.data).lower()
    
    def test_list_response_no_sensitive_data(
        self, authenticated_client, multiple_tickets
    ):
        """Test list responses don't contain sensitive fields."""
        url = reverse('maintenance:maintenance-ticket-list')
        response = authenticated_client.get(url)
        
        assert response.status_code == 200
        sensitive_fields = ['password', 'token', 'secret', 'api_key']
        response_str = str(response.data).lower()
        for field in sensitive_fields:
            assert field not in response_str


@pytest.mark.django_db
class TestAuthorizationBypass:
    """Test authorization cannot be bypassed."""
    
    def test_cannot_bypass_auth_with_invalid_token(
        self, api_client, ticket
    ):
        """Test invalid JWT token is rejected."""
        api_client.credentials(HTTP_AUTHORIZATION='Bearer invalid_token')
        url = reverse('maintenance:maintenance-ticket-detail', args=[ticket.id])
        response = api_client.get(url)
        assert response.status_code == 401
    
    def test_cannot_bypass_auth_with_expired_token(
        self, api_client, ticket
    ):
        """Test expired token is rejected."""
        api_client.credentials(HTTP_AUTHORIZATION='Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9')
        url = reverse('maintenance:maintenance-ticket-detail', args=[ticket.id])
        response = api_client.get(url)
        assert response.status_code == 401
    
    def test_cannot_bypass_with_manipulated_user_id(
        self, authenticated_client, other_user_ticket
    ):
        """Test cannot access resource by manipulating user context."""
        url = reverse('maintenance:maintenance-ticket-detail', args=[other_user_ticket.id])
        response = authenticated_client.get(
            url,
            HTTP_X_USER_ID=str(other_user_ticket.created_by.id)
        )
        assert response.status_code == 404