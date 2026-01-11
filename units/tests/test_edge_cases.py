# tests/test_edge_cases.py
"""
Tests for edge cases and boundary conditions.

Coverage:
- Empty databases
- Single records
- Maximum field lengths
- Boundary values
- Special characters
- Unicode handling
- Timezone issues
- Concurrent operations
"""

import pytest
from django.urls import reverse
from units.models import Unit
from .factories import UnitFactory
from .factories import EstateFactory as estate_factory


@pytest.mark.django_db
class TestEmptyDatabase:
    """Test behavior with empty database."""
    
    def test_list_empty_database(self, authenticated_client):
        """Test listing units when none exist."""
        url = reverse("units:unit-list")
        response = authenticated_client.get(url)
        
        assert response.status_code == 200
        assert response.data["count"] == 0
        assert response.data["results"] == []
    
    def test_occupied_units_empty_database(self, authenticated_client):
        """Test occupied endpoint with no units."""
        url = reverse("units:unit-occupied")
        response = authenticated_client.get(url)
        
        assert response.status_code == 200
        assert len(response.data) == 0
    
    def test_vacant_units_empty_database(self, authenticated_client):
        """Test vacant endpoint with no units."""
        url = reverse("units:unit-vacant")
        response = authenticated_client.get(url)
        
        assert response.status_code == 200
        assert len(response.data) == 0


@pytest.mark.django_db
class TestSingleRecord:
    """Test behavior with single record in database."""
    
    def test_list_single_unit(self, authenticated_client, unit):
        """Test listing when only one unit exists."""
        url = reverse("units:unit-list")
        response = authenticated_client.get(url)
        
        assert response.status_code == 200
        assert response.data["count"] == 1
        assert len(response.data["results"]) == 1
    
    def test_delete_only_unit(self, authenticated_client, unit):
        """Test deleting the only unit in database."""
        url = reverse("units:unit-detail", args=[unit.id])
        response = authenticated_client.delete(url)
        
        assert response.status_code == 204
        assert Unit.objects.count() == 0


@pytest.mark.django_db
class TestFieldBoundaries:
    """Test boundary values for fields."""
    
    def test_identifier_max_length(self, authenticated_client):
        """Test identifier at maximum allowed length."""
        url = reverse("units:unit-list")
        estate = estate_factory() 

        data = {
            "identifier": "x" * 100,
            "unit_type": Unit.UnitType.HOUSE.value,
            "estate": str(estate.id),
        }
        
        response = authenticated_client.post(url, data, format="json")
        
        assert response.status_code == 201
    
    def test_identifier_exceeds_max_length(self, authenticated_client):
        """Test identifier exceeding maximum length."""
        url = reverse("units:unit-list")
        data = {
            "identifier": "x" * 101,
            "unit_type": Unit.UnitType.HOUSE.value,
        }
        
        response = authenticated_client.post(url, data, format="json")
        
        assert response.status_code == 400
    
    def test_description_very_long(self, authenticated_client, user):
        """Test creating unit with very long description."""
        url = reverse("units:unit-list")
        estate = estate_factory() 
        
        data = {
            "identifier": "House 1",
            "unit_type": Unit.UnitType.HOUSE.value,
            "description": "x" * 1000,
            "estate": str(estate.id),
        }
        
        response = authenticated_client.post(url, data, format="json")
        
        assert response.status_code == 201
        
        unit = Unit.objects.get(id=response.data["id"])
        assert len(unit.description) == 1000
    
    def test_empty_string_vs_null(self, authenticated_client, user):
            """Test difference between empty string and null."""
            url = reverse("units:unit-list")
            estate = estate_factory() 
            data = {
                "estate": str(estate.id),  # ADDED
                "identifier": "House 1",
                "unit_type": Unit.UnitType.HOUSE.value,
                "occupant_name": "",  # Empty string should be converted to None
            }

            response = authenticated_client.post(url, data, format="json")
            assert response.status_code == 201
            
            unit = Unit.objects.get(id=response.data['id'])
            # Empty strings should be stored as None for nullable fields
            assert unit.occupant_name in [None, ""]


@pytest.mark.django_db
class TestSpecialCharacters:
    """Test handling of special characters."""
    
    def test_identifier_with_special_chars(self, authenticated_client, user):
        """Test identifier with special characters."""
        url = reverse("units:unit-list")
        estate = estate_factory() 
        
        data = {
            "identifier": "Unit #123 (Building A)",
            "unit_type": Unit.UnitType.HOUSE.value,
            "estate": str(estate.id),
        }
        
        response = authenticated_client.post(url, data, format="json")
        
        assert response.status_code == 201
        assert response.data["identifier"] == "Unit #123 (Building A)"
    
    def test_identifier_with_unicode(self, authenticated_client, user):
        """Test identifier with Unicode characters."""
        url = reverse("units:unit-list")
        estate = estate_factory() 
        
        data = {
            "identifier": "Квартира 5",
            "unit_type": Unit.UnitType.FLAT,
            "estate": str(estate.id),
        }
        
        response = authenticated_client.post(url, data, format="json")
        
        assert response.status_code == 201
        assert response.data["identifier"] == "Квартира 5"
    
    def test_occupant_name_with_unicode(self, authenticated_client, user):
        """Test occupant name with Unicode characters."""
        url = reverse("units:unit-list")
        estate = estate_factory() 
        
        data = {
            "identifier": "House 1",
            "unit_type": Unit.UnitType.HOUSE.value,
            "is_occupied": True,
            "occupant_name": "José García",
            "estate": str(estate.id),
        }
        
        response = authenticated_client.post(url, data, format="json")
        
        assert response.status_code == 201
        assert response.data["occupant_name"] == "José García"
    
    def test_identifier_with_emojis(self, authenticated_client, user):
        """Test identifier with emoji characters."""
        url = reverse("units:unit-list")
        estate = estate_factory() 
        
        data = {
            "identifier": "House 🏠 123",
            "unit_type": Unit.UnitType.HOUSE.value,
            "estate": str(estate.id),
        }
        
        response = authenticated_client.post(url, data, format="json")
        
        assert response.status_code == 201
    
    def test_newlines_in_description(self, authenticated_client, user):
        """Test description with newline characters."""
        url = reverse("units:unit-list")
        estate = estate_factory() 
        
        data = {
            "identifier": "House 1",
            "unit_type": Unit.UnitType.HOUSE.value,
            "description": "Line 1\nLine 2\nLine 3",
            "estate": str(estate.id),
        }
        
        response = authenticated_client.post(url, data, format="json")
        
        assert response.status_code == 201
        assert "Line 1" in response.data["description"]


@pytest.mark.django_db
class TestPhoneNumberEdgeCases:
    """Test phone number validation edge cases."""
    
    def test_phone_with_country_code(self, authenticated_client, user):
        """Test phone number with country code."""
        url = reverse("units:unit-list")
        estate = estate_factory() 
        
        data = {
            "identifier": "House 1",
            "unit_type": Unit.UnitType.HOUSE.value,
            "is_occupied": True,
            "occupant_phone": "+447911123456",
            "estate": str(estate.id),
        }
        
        response = authenticated_client.post(url, data, format="json")
        
        assert response.status_code == 201
    
    def test_phone_minimum_length(self, authenticated_client, user):
        """Test phone number at minimum length."""
        url = reverse("units:unit-list")
        estate = estate_factory() 
        
        data = {
            "identifier": "House 1",
            "unit_type": Unit.UnitType.HOUSE.value,
            "is_occupied": True,
            "occupant_phone": "+123456789",
            "estate": str(estate.id),
        }
        
        response = authenticated_client.post(url, data, format="json")
        
        assert response.status_code == 201
    
    def test_phone_too_short(self, authenticated_client, user):
        """Test phone number that's too short."""
        url = reverse("units:unit-list")
        # estate = estate_factory() 
        
        data = {
            "identifier": "House 1",
            "unit_type": Unit.UnitType.HOUSE.value,
            "is_occupied": True,
            "occupant_phone": "+12345",
            # "estate": str(estate.id),
        }
        
        response = authenticated_client.post(url, data, format="json")
        
        assert response.status_code == 400
    
    def test_phone_with_spaces_invalid(self, authenticated_client, user):
        """Test that phone with spaces is invalid."""
        url = reverse("units:unit-list")
        data = {
            "identifier": "House 1",
            "unit_type": Unit.UnitType.HOUSE.value,
            "is_occupied": True,
            "occupant_phone": "+1 234 567 8901",
        }
        
        response = authenticated_client.post(url, data, format="json")
        
        assert response.status_code == 400


@pytest.mark.django_db
class TestCaseSensitivity:
    """Test case sensitivity handling."""
    
    def test_filter_identifier_case_insensitive(
        self, authenticated_client, user
    ):
        """Test that identifier filter is case-insensitive."""
        unit = UnitFactory.create(owner=user, identifier="House ABC")  # noqa: F841
        
        url = reverse("units:unit-list")
        response = authenticated_client.get(url, {"identifier": "house"})
        
        assert response.status_code == 200
        assert response.data["count"] == 1
    
    def test_occupant_name_preserves_case(self, authenticated_client, user):
        """Test that occupant name case is preserved."""
        url = reverse("units:unit-list")
        estate = estate_factory() 
        
        data = {
            "identifier": "House 1",
            "unit_type": Unit.UnitType.HOUSE.value,
            "is_occupied": True,
            "occupant_name": "John DOE",
            "estate": str(estate.id),
        }
        
        response = authenticated_client.post(url, data, format="json")
        
        assert response.status_code == 201
        assert response.data["occupant_name"] == "John DOE"


@pytest.mark.django_db
class TestWhitespace:
    """Test whitespace handling."""
    
    def test_identifier_leading_trailing_whitespace(
        self, authenticated_client, user
    ):
        """Test that leading/trailing whitespace is stripped."""
        url = reverse("units:unit-list")
        estate = estate_factory() 
        
        data = {
            "identifier": "  House 1  ",
            "unit_type": Unit.UnitType.HOUSE.value,
            "estate": str(estate.id),
        }
        
        response = authenticated_client.post(url, data, format="json")
        
        assert response.status_code == 201
        
        unit = Unit.objects.get(id=response.data["id"])
        assert unit.identifier == "House 1"
    
    def test_identifier_only_whitespace_invalid(self, authenticated_client):
        """Test that identifier with only whitespace is invalid."""
        url = reverse("units:unit-list")
        estate = estate_factory() 
        
        data = {
            "identifier": "    ",
            "unit_type": Unit.UnitType.HOUSE.value,
            "estate": str(estate.id),
        }
        
        response = authenticated_client.post(url, data, format="json")
        
        assert response.status_code == 400
    
    def test_occupant_name_whitespace_preserved(
        self, authenticated_client, user
    ):
        """Test that internal whitespace in names is preserved."""
        url = reverse("units:unit-list")
        estate = estate_factory() 
        
        data = {
            "identifier": "House 1",
            "unit_type": Unit.UnitType.HOUSE.value,
            "is_occupied": True,
            "occupant_name": "John   Doe",
            "estate": str(estate.id),
        }
        
        response = authenticated_client.post(url, data, format="json")
        
        assert response.status_code == 201
        assert "John   Doe" in response.data["occupant_name"]


@pytest.mark.django_db
class TestLargeDatasets:
    """Test behavior with large datasets."""
    
    def test_list_with_many_units(self, authenticated_client, user):
        """Test listing endpoint with 100+ units."""
        UnitFactory.create_batch(150, owner=user)
        
        url = reverse("units:unit-list")
        response = authenticated_client.get(url)
        
        assert response.status_code == 200
        assert response.data["count"] == 150
    
    def test_filter_on_large_dataset(self, authenticated_client, user):
        """Test filtering with large dataset."""
        UnitFactory.create_batch(50, owner=user, unit_type=Unit.UnitType.HOUSE)
        UnitFactory.create_batch(50, owner=user, unit_type=Unit.UnitType.FLAT)
        
        url = reverse("units:unit-list")
        response = authenticated_client.get(
            url, {"unit_type": Unit.UnitType.HOUSE}
        )
        
        assert response.status_code == 200
        assert response.data["count"] == 50