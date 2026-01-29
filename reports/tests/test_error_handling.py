
# reports/tests/test_error_handling.py
"""
Tests for error handling and exception scenarios.

Coverage:`
- Invalid data handling
- Database errors
- Service layer exceptions
- HTTP error responses
"""

import pytest
from django.urls import reverse
from rest_framework import status
from unittest.mock import patch, Mock
import uuid
from django.db import DatabaseError


@pytest.mark.django_db
class TestServiceLayerErrorHandling:
    """Test error handling in service layer."""
    
    def test_fee_not_found_returns_400(self, estate_manager_client):
        """Test nonexistent fee returns appropriate error."""
        fake_id = uuid.uuid4()
        url = reverse('reports:reports-fee-payment-status', kwargs={'fee_id': fake_id})
        response = estate_manager_client.get(url)
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'error' in response.data
    
    def test_estate_not_found_returns_400(self, estate_manager_client):
        """Test nonexistent estate returns appropriate error."""
        fake_id = uuid.uuid4()
        url = reverse('reports:reports-estate-summary', kwargs={'estate_id': fake_id})
        response = estate_manager_client.get(url)
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'error' in response.data
    
    @patch('reports.services.get_fee_payment_status')
    def test_service_exception_returns_500(self, mock_service, estate_manager_client, fee):
        """Test unexpected service exception returns 500."""
        mock_service.side_effect = Exception('Unexpected error')
        
        url = reverse('reports:reports-fee-payment-status', kwargs={'fee_id': fee.id})
        response = estate_manager_client.get(url)
        
        assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
        assert 'error' in response.data
    
    @patch('reports.services.get_overall_payment_summary')
    def test_overall_summary_exception_returns_500(
        self, mock_service, estate_manager_client
    ):
        """Test exception in overall summary returns 500."""
        mock_service.side_effect = Exception('Database error')
        
        url = reverse('reports:reports-overall-summary')
        response = estate_manager_client.get(url)
        
        assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR


@pytest.mark.django_db
class TestPermissionErrors:
    """Test permission-related error responses."""
    
    def test_tenant_accessing_reports_gets_proper_error(self, tenant_client):
        """Test tenant gets clear error message."""
        url = reverse('reports:reports-overall-summary')
        response = tenant_client.get(url)
        
        assert response.status_code == status.HTTP_403_FORBIDDEN
    
    def test_accessing_other_landlord_fee_gets_clear_error(
        self, estate_manager_client, other_estate
    ):
        """Test accessing another landlord's fee gives clear error."""
        from .factories import FeeFactory
        
        other_fee = FeeFactory.create(estate=other_estate)
        url = reverse('reports:reports-fee-payment-status', kwargs={'fee_id': other_fee.id})
        response = estate_manager_client.get(url)
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'error' in response.data
        assert 'permission' in response.data['error'].lower()


@pytest.mark.django_db
class TestMalformedRequests:
    """Test handling of malformed requests."""
    
    def test_invalid_http_method_on_fee_report(self, estate_manager_client, fee):
        """Test invalid HTTP method returns 405."""
        url = reverse('reports:reports-fee-payment-status', kwargs={'fee_id': fee.id})
        response = estate_manager_client.post(url)
        
        assert response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED
    
    def test_invalid_http_method_on_overall_summary(self, estate_manager_client):
        """Test invalid HTTP method on overall summary."""
        url = reverse('reports:reports-overall-summary')
        response = estate_manager_client.post(url)
        
        assert response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED
    
    def test_invalid_content_type_ignored_for_get(self, estate_manager_client):
        """Test invalid content type on GET request."""
        url = reverse('reports:reports-overall-summary')
        response = estate_manager_client.get(
            url,
            content_type='application/xml'
        )
        
        # GET requests should still work regardless of content type
        assert response.status_code in [
            status.HTTP_200_OK,
            status.HTTP_403_FORBIDDEN
        ]


@pytest.mark.django_db
class TestDatabaseErrors:
    """Test handling of database-related errors."""
    


    @patch("reports.services.Fee.objects.select_related")
    def test_database_error_in_fee_query_handled(
        self, mock_select_related, estate_manager_client, fee
    ):
        # Make select_related().get() raise DatabaseError
        mock_select_related.return_value.get.side_effect = DatabaseError("Connection lost")

        url = reverse("reports:reports-fee-payment-status", kwargs={"fee_id": fee.id})
        response = estate_manager_client.get(url)

        assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
        assert response.data == {"error": "An error occurred while generating the report"}



        
@pytest.mark.django_db
class TestValidationErrors:
    """Test validation error handling."""
    
    def test_empty_fee_id_parameter_rejected(self, estate_manager_client):
        """Test empty fee_id parameter is rejected."""
        url = '/api/reports/fee//'
        response = estate_manager_client.get(url)
        
        assert response.status_code == status.HTTP_404_NOT_FOUND
    
    def test_empty_estate_id_parameter_rejected(self, estate_manager_client):
        """Test empty estate_id parameter is rejected."""
        url = '/api/reports/estate//'
        response = estate_manager_client.get(url)
        
        assert response.status_code == status.HTTP_404_NOT_FOUND
