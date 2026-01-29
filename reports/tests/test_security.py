
# reports/tests/test_security.py
"""
Security-focused tests for reports app.

Coverage:
- IDOR (Insecure Direct Object Reference) attacks
- Authorization bypass attempts
- Data exposure vulnerabilities
- Cross-tenant data leakage
"""

import pytest
from django.urls import reverse
from rest_framework import status
import uuid


@pytest.mark.django_db
class TestIDORVulnerabilities:
    """Test protection against Insecure Direct Object Reference attacks."""
    
    def test_cannot_access_other_landlord_fee_by_uuid(
        self, landlord_client, other_estate
    ):
        """Test landlord cannot access another landlord's fee by knowing UUID."""
        from .factories import FeeFactory
        
        other_fee = FeeFactory.create(estate=other_estate)
        
        url = reverse('reports:reports-fee-payment-status', kwargs={'fee_id': other_fee.id})
        response = landlord_client.get(url)
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'error' in response.data
    
    def test_cannot_access_other_landlord_estate_summary(
        self, landlord_client, other_estate
    ):
        """Test landlord cannot access another landlord's estate summary."""
        url = reverse('reports:reports-estate-summary', kwargs={'estate_id': other_estate.id})
        response = landlord_client.get(url)
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
    
    def test_guessing_uuids_does_not_expose_data(self, landlord_client):
        """Test that guessing random UUIDs doesn't expose any data."""
        random_uuid = uuid.uuid4()
        
        url = reverse('reports:reports-fee-payment-status', kwargs={'fee_id': random_uuid})
        response = landlord_client.get(url)
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        # Ensure error message doesn't leak whether UUID exists
        assert 'error' in response.data


@pytest.mark.django_db
class TestAuthorizationBypass:
    """Test protection against authorization bypass attempts."""
    
    def test_tenant_cannot_bypass_permission_with_valid_token(
        self, tenant_client, fee
    ):
        """Test tenant with valid auth cannot bypass landlord-only permission."""
        url = reverse('reports:reports-fee-payment-status', kwargs={'fee_id': fee.id})
        response = tenant_client.get(url)
        
        assert response.status_code == status.HTTP_403_FORBIDDEN
    
    def test_cannot_access_reports_without_authentication(self, api_client, fee):
        """Test unauthenticated requests are rejected."""
        url = reverse('reports:reports-fee-payment-status', kwargs={'fee_id': fee.id})
        response = api_client.get(url)
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
    
    def test_invalid_jwt_token_rejected(self, api_client, fee):
        """Test invalid JWT token is rejected."""
        api_client.credentials(HTTP_AUTHORIZATION='Bearer invalid_token_here')
        
        url = reverse('reports:reports-fee-payment-status', kwargs={'fee_id': fee.id})
        response = api_client.get(url)
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
    
    def test_expired_jwt_token_rejected(self, api_client, fee):
        """Test expired JWT token is rejected."""
        # This would require actually creating an expired token
        # For now, test with malformed token
        api_client.credentials(HTTP_AUTHORIZATION='Bearer expired.token.here')
        
        url = reverse('reports:reports-fee-payment-status', kwargs={'fee_id': fee.id})
        response = api_client.get(url)
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED


@pytest.mark.django_db
class TestDataExposure:
    """Test protection against sensitive data exposure."""
    
    def test_error_messages_do_not_expose_sensitive_data(
        self, landlord_client, other_estate
    ):
        """Test error messages don't expose sensitive information."""
        from .factories import FeeFactory
        
        other_fee = FeeFactory.create(estate=other_estate)
        
        url = reverse('reports:reports-fee-payment-status', kwargs={'fee_id': other_fee.id})
        response = landlord_client.get(url)
        
        # Error should not reveal details about the fee or estate
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        error_message = str(response.data.get('error', ''))
        
        # Should not contain estate name or fee details
        assert other_estate.name not in error_message
        assert str(other_fee.amount) not in error_message
    
    def test_unpaid_units_do_not_expose_other_landlord_tenants(
        self, landlord_client, other_landlord_client, estate_with_complete_data
    ):
        """Test report doesn't expose tenants from other landlords."""
        from .factories import EstateFactory, UnitFactory, FeeFactory
        
        # Create other landlord's data
        other_landlord = other_landlord_client.handler._force_user
        other_estate = EstateFactory.create(owner=other_landlord)
        other_unit = UnitFactory.create(estate=other_estate, is_occupied=True)
        other_fee = FeeFactory.create(estate=other_estate)
        
        # First landlord's fee report should not include other landlord's tenants
        fee_id = estate_with_complete_data['fee1'].id
        url = reverse('reports:reports-fee-payment-status', kwargs={'fee_id': fee_id})
        response = landlord_client.get(url)
        
        assert response.status_code == status.HTTP_200_OK
        
        # Check that other landlord's tenant is not in unpaid units
        unpaid_tenant_ids = [
            u.get('tenant_id') for u in response.data['unpaid_units']
        ]
        assert other_unit.tenant.id not in unpaid_tenant_ids


@pytest.mark.django_db
class TestCrossTenantDataLeakage:
    """Test protection against cross-tenant data leakage."""
    
    def test_overall_summary_shows_only_own_estates(
        self, landlord_client, other_landlord_client, estate_with_complete_data
    ):
        """Test overall summary only shows landlord's own estates."""
        from .factories import EstateFactory, FeeFactory
        
        # Create other landlord's estate
        other_landlord = other_landlord_client.handler._force_user
        other_estate = EstateFactory.create(owner=other_landlord)
        other_fee = FeeFactory.create(estate=other_estate)
        
        # First landlord's summary should not include other landlord's fees
        url = reverse('reports:reports-overall-summary')
        response = landlord_client.get(url)
        
        assert response.status_code == status.HTTP_200_OK
        
        # Check that other landlord's fee is not in summary
        fee_ids = [f['fee_id'] for f in response.data['fees_summary']]
        assert str(other_fee.id) not in [str(fid) for fid in fee_ids]
    
    def test_filtering_by_estate_respects_ownership(
        self, landlord_client, other_estate
    ):
        """Test filtering by estate_id respects ownership."""
        url = reverse('reports:reports-overall-summary')
        response = landlord_client.get(url, {'estate_id': str(other_estate.id)})
        
        # Should return error, not show other landlord's data
        assert response.status_code == status.HTTP_400_BAD_REQUEST


@pytest.mark.django_db
class TestSQLInjectionPrevention:
    """Test protection against SQL injection attempts."""
    
    def test_sql_injection_in_estate_id_parameter(self, landlord_client):
        """Test SQL injection attempt in estate_id parameter."""
        url = reverse('reports:reports-overall-summary')
        malicious_input = "'; DROP TABLE estates; --"
        
        response = landlord_client.get(url, {'estate_id': malicious_input})
        
        # Should handle gracefully, not execute SQL
        assert response.status_code in [
            status.HTTP_400_BAD_REQUEST,
            status.HTTP_200_OK
        ]
        
        # Verify estates table still exists by making another request
        response2 = landlord_client.get(url)
        assert response2.status_code == status.HTTP_200_OK
    
    def test_sql_injection_in_url_path(self, landlord_client):
        """Test SQL injection attempt in URL path."""
        malicious_uuid = "' OR '1'='1"
        url = f'/api/reports/fee/{malicious_uuid}/'
        
        response = landlord_client.get(url)
        
        # Should return 404 or 400, not execute SQL
        assert response.status_code in [
            status.HTTP_404_NOT_FOUND,
            status.HTTP_400_BAD_REQUEST,
            ]
@pytest.mark.django_db
class TestMassAssignmentProtection:
    
    """Test protection against mass assignment vulnerabilities."""
    def test_cannot_modify_read_only_fields(self, landlord_client):
        """Test that read-only serializer fields cannot be modified."""
        # Reports are read-only, so this is inherently protected
        # But verify GET-only endpoints reject POST/PUT/PATCH
        
        url = reverse('reports:reports-overall-summary')
        
        post_response = landlord_client.post(url, {})
        assert post_response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED
        
        put_response = landlord_client.put(url, {})
        assert put_response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED
        
        patch_response = landlord_client.patch(url, {})
        assert patch_response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED

