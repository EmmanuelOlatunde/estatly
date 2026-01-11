# tests/test_security.py
"""
Tests for security vulnerabilities and attack vectors.

Coverage:
- IDOR (Insecure Direct Object References)
- SQL injection attempts
- XSS payload handling
- Mass assignment vulnerabilities
- Authorization bypass attempts
- Sensitive data exposure
"""

import pytest
from django.urls import reverse
from units.models import Unit
from .factories import UnitFactory
from .factories import EstateFactory as estate_factory


@pytest.mark.django_db
class TestIDOR:
    """Test Insecure Direct Object Reference vulnerabilities."""
    
    def test_cannot_view_other_users_unit_by_id(
        self, authenticated_client, other_users_unit
    ):
        """Test that user cannot access another user's unit by knowing the ID."""
        url = reverse("units:unit-detail", args=[other_users_unit.id])
        response = authenticated_client.get(url)
        
        assert response.status_code == 404
    
    def test_cannot_update_other_users_unit_by_id(
        self, authenticated_client, other_users_unit
    ):
        """Test that user cannot update another user's unit."""
        url = reverse("units:unit-detail", args=[other_users_unit.id])
        data = {"identifier": "Hacked"}
        
        response = authenticated_client.patch(url, data, format="json")
        
        assert response.status_code in [403, 404]
        
        other_users_unit.refresh_from_db()
        assert other_users_unit.identifier != "Hacked"
    
    def test_cannot_delete_other_users_unit_by_id(
        self, authenticated_client, other_users_unit
    ):
        """Test that user cannot delete another user's unit."""
        url = reverse("units:unit-detail", args=[other_users_unit.id])
        response = authenticated_client.delete(url)
        
        assert response.status_code in [403, 404]
        assert Unit.objects.filter(id=other_users_unit.id).exists()
    
    def test_cannot_deactivate_other_users_unit(
        self, authenticated_client, other_users_unit
    ):
        """Test that user cannot deactivate another user's unit."""
        url = reverse("units:unit-deactivate", args=[other_users_unit.id])
        response = authenticated_client.post(url)
        
        assert response.status_code in [403, 404]
        
        other_users_unit.refresh_from_db()
        assert other_users_unit.is_active is True
    
    def test_cannot_update_occupancy_of_other_users_unit(
        self, authenticated_client, other_users_unit
    ):
        """Test that user cannot update occupancy of another user's unit."""
        url = reverse("units:unit-update-occupancy", args=[other_users_unit.id])
        data = {"is_occupied": True, "occupant_name": "Hacker"}
        
        response = authenticated_client.patch(url, data, format="json")
        
        assert response.status_code in [403, 404]
    
    def test_list_does_not_leak_other_users_units(
        self, authenticated_client, user, other_user
    ):
        """Test that list endpoint doesn't leak other users' units."""
        user_units = UnitFactory.create_batch(2, owner=user)
        other_units = UnitFactory.create_batch(3, owner=other_user)
        
        url = reverse("units:unit-list")
        response = authenticated_client.get(url)
        
        assert response.status_code == 200
        assert response.data["count"] == 2
        
        returned_ids = {unit["id"] for unit in response.data["results"]}
        other_ids = {str(unit.id) for unit in other_units}
        
        assert returned_ids.isdisjoint(other_ids)


@pytest.mark.django_db
class TestMassAssignment:
    """Test mass assignment vulnerabilities."""
    
    def test_cannot_change_owner_on_create(
        self, authenticated_client, user, other_user
    ):
        """Test that owner cannot be set during creation."""
        url = reverse("units:unit-list")
        estate = estate_factory()

        data = {
            "identifier": "House 1",
            "unit_type": Unit.UnitType.HOUSE, 
            "owner": str(other_user.id),
            "estate": str(estate.id), 
        }
        
        response = authenticated_client.post(url, data, format="json")
        
        assert response.status_code == 201
        
        unit = Unit.objects.get(id=response.data["id"])
        assert unit.owner == user
        assert unit.owner != other_user
    
    def test_cannot_change_owner_on_update(
        self, authenticated_client, unit, other_user
    ):
        """Test that owner cannot be changed via update."""
        original_owner = unit.owner
        
        url = reverse("units:unit-detail", args=[unit.id])
        data = {"owner": str(other_user.id)}
        
        authenticated_client.patch(url, data, format="json")
        
        unit.refresh_from_db()
        assert unit.owner == original_owner
    
    def test_cannot_set_id_on_create(self, authenticated_client, user):
        """Test that ID cannot be set during creation."""
        import uuid
        custom_id = uuid.uuid4()
        
        url = reverse("units:unit-list")
        estate = estate_factory()
        data = {
            "id": str(custom_id),
            "identifier": "House 1",
            "unit_type": Unit.UnitType.HOUSE,
            "estate": str(estate.id),
        }
        
        response = authenticated_client.post(url, data, format="json")
        
        assert response.status_code == 201
        assert response.data["id"] != str(custom_id)
    
    def test_cannot_modify_timestamps(self, authenticated_client, unit):
        """Test that timestamps cannot be manually set."""
        from django.utils import timezone
        
        past_date = timezone.now() - timezone.timedelta(days=365)
        
        url = reverse("units:unit-detail", args=[unit.id])
        data = {
            "created_at": past_date.isoformat(),
            "updated_at": past_date.isoformat(),
        }
        
        authenticated_client.patch(url, data, format="json")
        
        unit.refresh_from_db()
        assert unit.created_at > past_date


@pytest.mark.django_db
class TestSQLInjection:
    """Test SQL injection attack vectors."""
    
    def test_sql_injection_in_identifier_filter(
        self, authenticated_client, user
    ):
        """Test SQL injection attempt in identifier filter."""
        UnitFactory.create(owner=user, identifier="Safe Unit")
        
        url = reverse("units:unit-list")
        response = authenticated_client.get(
            url,
            {"identifier": "' OR '1'='1"}
        )
        
        assert response.status_code == 200
        assert Unit.objects.count() == 1
    
    def test_sql_injection_in_search(self, authenticated_client, user):
        """Test SQL injection attempt in search parameter."""
        UnitFactory.create(owner=user, identifier="Safe Unit")
        
        url = reverse("units:unit-list")
        response = authenticated_client.get(
            url,
            {"search": "'; DROP TABLE units; --"}
        )
        
        assert response.status_code == 200
        assert Unit.objects.count() == 1
    
    def test_sql_injection_in_create(self, authenticated_client, user):
        """Test SQL injection attempt in create data."""
        url = reverse("units:unit-list")
        estate = estate_factory()

        data = {
            "identifier": "'; DROP TABLE units; --",
            "unit_type": Unit.UnitType.HOUSE,
            "estate": str(estate.id),
        }
        
        response = authenticated_client.post(url, data, format="json")
        
        assert response.status_code == 201
        assert Unit.objects.count() == 1


@pytest.mark.django_db
class TestXSS:
    """Test XSS (Cross-Site Scripting) attack vectors."""
    
    def test_xss_in_identifier(self, authenticated_client, user):
        """Test that XSS payload in identifier is stored but not executed."""
        url = reverse("units:unit-list")
        estate = estate_factory()

        data = {
            "identifier": "<script>alert('XSS')</script>",
            "unit_type": Unit.UnitType.HOUSE,
            "estate": str(estate.id), 
        }
        
        response = authenticated_client.post(url, data, format="json")
        
        assert response.status_code == 201
        assert response.data["identifier"] == "<script>alert('XSS')</script>"
    
    def test_xss_in_occupant_name(self, authenticated_client, user):
        """Test XSS payload in occupant name."""
        url = reverse("units:unit-list")
        estate = estate_factory()
        data = {
            "identifier": "House 1",
            "unit_type": Unit.UnitType.HOUSE,
            "is_occupied": True,
            "occupant_name": "<img src=x onerror=alert('XSS')>",
            "estate": str(estate.id), 

        }
        
        response = authenticated_client.post(url, data, format="json")
        
        assert response.status_code == 201
        assert "<img src=x" in response.data["occupant_name"]
    
    def test_xss_in_description(self, authenticated_client, user):
        """Test XSS payload in description."""
        url = reverse("units:unit-list")
        estate = estate_factory()
        data = {
            "identifier": "House 1",
            "unit_type": Unit.UnitType.HOUSE,
            "description": "<script>document.cookie</script>",
            "estate": str(estate.id), 

        }
        
        response = authenticated_client.post(url, data, format="json")
        
        assert response.status_code == 201


@pytest.mark.django_db
class TestSensitiveDataExposure:
    """Test that sensitive data is not exposed."""
    
    def test_list_does_not_expose_sensitive_user_data(
        self, authenticated_client, user
    ):
        """Test that user passwords/tokens are not exposed."""
        UnitFactory.create(owner=user)
        
        url = reverse("units:unit-list")
        response = authenticated_client.get(url)
        
        assert response.status_code == 200
        
        for unit_data in response.data["results"]:
            assert "password" not in str(unit_data).lower()
            assert "token" not in str(unit_data).lower()
    
    def test_detail_does_not_expose_sensitive_user_data(
        self, authenticated_client, unit
    ):
        """Test that detail view doesn't expose sensitive data."""
        url = reverse("units:unit-detail", args=[unit.id])
        response = authenticated_client.get(url)
        
        assert response.status_code == 200
        response_str = str(response.data).lower()
        assert "password" not in response_str
        assert "token" not in response_str
    
    def test_error_responses_do_not_leak_info(
        self, authenticated_client, other_users_unit
    ):
        """Test that error responses don't leak existence of other users' data."""
        url = reverse("units:unit-detail", args=[other_users_unit.id])
        response = authenticated_client.get(url)
        
        assert response.status_code == 404
        
        response_str = str(response.data).lower()
        assert other_users_unit.identifier.lower() not in response_str


@pytest.mark.django_db
class TestAuthorizationBypass:
    """Test authorization bypass attempts."""
    
    def test_cannot_bypass_auth_with_fake_jwt(self, api_client, unit):
        """Test that fake JWT tokens are rejected."""
        url = reverse("units:unit-detail", args=[unit.id])
        
        client = api_client
        client.credentials(HTTP_AUTHORIZATION="Bearer fake_token_12345")
        response = client.get(url)
        
        assert response.status_code == 401
    
    def test_cannot_access_with_expired_session(self, api_client, unit):
        """Test that expired/invalid sessions are rejected."""
        url = reverse("units:unit-detail", args=[unit.id])
        response = api_client.get(url)
        
        assert response.status_code == 401
    
    def test_admin_status_does_not_grant_cross_user_access(
        self, admin_client, other_users_unit
    ):
        """Test that admin status alone doesn't grant access to other users' units."""
        url = reverse("units:unit-detail", args=[other_users_unit.id])
        response = admin_client.get(url)
        
        assert response.status_code == 404


@pytest.mark.django_db
class TestInputValidation:
    """Test input validation for security."""
    
    def test_very_long_identifier_rejected(self, authenticated_client):
        """Test that excessively long identifiers are rejected."""
        url = reverse("units:unit-list")
        data = {
            "identifier": "x" * 10000,
            "unit_type": Unit.UnitType.HOUSE,
        }
        
        response = authenticated_client.post(url, data, format="json")
        
        assert response.status_code == 400
    
    def test_negative_values_handled(self, authenticated_client, user):
        """Test that negative values are handled appropriately."""
        url = reverse("units:unit-list")
        data = {
            "identifier": "House 1",
            "unit_type": Unit.UnitType.HOUSE,
            "is_active": -1,
        }
        
        response = authenticated_client.post(url, data, format="json")
        
        assert response.status_code == 400
    
    def test_null_byte_injection(self, authenticated_client, user):
        """Test null byte injection attempt."""
        url = reverse("units:unit-list")
        data = {
            "identifier": "House\x001",
            "unit_type": Unit.UnitType.HOUSE,
        }
        
        response = authenticated_client.post(url, data, format="json")
        
        assert response.status_code in [201, 400]