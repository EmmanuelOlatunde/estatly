

# # tests/test_integration.py
# """
# Integration tests for multi-step workflows.

# Coverage:
# - Full CRUD lifecycle
# - Multiple estate operations
# - Filter + pagination combinations
# """

# import pytest
# from .helpers import (
#     get_estate_list_url,
#     get_estate_detail_url,
#     get_estate_activate_url,
#     get_estate_deactivate_url
# )
# # from estates.models import Estate


# @pytest.mark.django_db
# class TestEstateIntegration:
#     """Test complete estate workflows."""
    
#     def test_full_crud_lifecycle(self, staff_client):
#         """Test complete create-read-update-delete lifecycle."""
#         list_url = get_estate_list_url()
        
#         create_data = {
#             'name': 'Lifecycle Estate',
#             'estate_type': 'PRIVATE',
#             'fee_frequency': 'MONTHLY',
#             'approximate_units': 100
#         }
#         create_response = staff_client.post(list_url, create_data, format='json')
#         assert create_response.status_code == 201
#         estate_id = create_response.data['id']
        
#         detail_url = get_estate_detail_url(estate_id)
#         read_response = staff_client.get(detail_url)
#         assert read_response.status_code == 200
#         assert read_response.data['name'] == 'Lifecycle Estate'
        
#         update_data = {'name': 'Updated Lifecycle Estate'}
#         update_response = staff_client.patch(detail_url, update_data, format='json')
#         assert update_response.status_code == 200
#         assert update_response.data['name'] == 'Updated Lifecycle Estate'
        
#         delete_response = staff_client.delete(detail_url)
#         assert delete_response.status_code == 204
        
#         final_check = staff_client.get(detail_url)
#         assert final_check.status_code == 404
    
#     def test_create_then_deactivate_then_activate(self, staff_client):
#         """Test creating estate and toggling active status."""
#         list_url = get_estate_list_url()
        
#         create_data = {
#             'name': 'Toggle Estate',
#             'estate_type': 'GOVERNMENT',
#             'fee_frequency': 'YEARLY'
#         }
#         create_response = staff_client.post(list_url, create_data, format='json')
#         assert create_response.status_code == 201
#         estate_id = create_response.data['id']
#         assert create_response.data['is_active'] is True
        
#         deactivate_url = get_estate_deactivate_url(estate_id)
#         deactivate_response = staff_client.post(deactivate_url)
#         assert deactivate_response.status_code == 200
#         assert deactivate_response.data['estate']['is_active'] is False
        
#         activate_url = get_estate_activate_url(estate_id)
#         activate_response = staff_client.post(activate_url)
#         assert activate_response.status_code == 200
#         assert activate_response.data['estate']['is_active'] is True
    
#     def test_create_multiple_then_filter_and_paginate(self, staff_client):
#         """Test creating multiple estates then filtering with pagination."""
#         list_url = get_estate_list_url()
        
#         for i in range(15):
#             data = {
#                 'name': f'Private Estate {i}',
#                 'estate_type': 'PRIVATE',
#                 'fee_frequency': 'MONTHLY',
#                 'approximate_units': 100 + (i * 10)
#             }
#             response = staff_client.post(list_url, data, format='json')
#             assert response.status_code == 201
        
#         for i in range(10):
#             data = {
#                 'name': f'Government Estate {i}',
#                 'estate_type': 'GOVERNMENT',
#                 'fee_frequency': 'YEARLY',
#                 'approximate_units': 50 + (i * 5)
#             }
#             response = staff_client.post(list_url, data, format='json')
#             assert response.status_code == 201
        
#         filter_response = staff_client.get(list_url, {
#             'estate_type': 'PRIVATE',
#             'min_units': '150'
#         })
#         assert filter_response.status_code == 200
#         assert filter_response.data['count'] > 0
    
#     def test_search_across_multiple_fields(self, staff_client):
#         """Test search functionality across name, description, and address."""
#         list_url = get_estate_list_url()
        
#         estates_data = [
#             {
#                 'name': 'Sunshine Gardens',
#                 'estate_type': 'PRIVATE',
#                 'fee_frequency': 'MONTHLY',
#                 'description': 'Beautiful gardens',
#                 'address': '123 Main St'
#             },
#             {
#                 'name': 'Mountain View',
#                 'estate_type': 'PRIVATE',
#                 'fee_frequency': 'MONTHLY',
#                 'description': 'Mountain side living',
#                 'address': '456 Garden Road'
#             },
#             {
#                 'name': 'Beach Estate',
#                 'estate_type': 'GOVERNMENT',
#                 'fee_frequency': 'YEARLY',
#                 'description': 'Seaside property',
#                 'address': '789 Beach Ave'
#             }
#         ]
        
#         for data in estates_data:
#             response = staff_client.post(list_url, data, format='json')
#             assert response.status_code == 201
        
#         search_response = staff_client.get(list_url, {'search': 'garden'})
#         assert search_response.status_code == 200
#         assert search_response.data['count'] == 2
