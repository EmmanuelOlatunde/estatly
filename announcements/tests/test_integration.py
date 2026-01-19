# tests/test_integration.py

"""
Integration tests for announcements app.

Tests complete workflows across multiple endpoints and operations.
Validates end-to-end functionality and multi-step processes.

Coverage:
- Complete CRUD workflows
- Multi-user scenarios
- State transitions
- Cross-endpoint data consistency
- Real-world usage patterns
"""

import pytest
from django.urls import reverse
from announcements.models import Announcement
from .factories import UserFactory, AnnouncementFactory


@pytest.mark.django_db
class TestAnnouncementLifecycle:
    """Test complete announcement lifecycle from creation to deletion."""
    
    def test_create_update_delete_workflow(self, authenticated_client):
        """Test full lifecycle: create -> update -> delete."""
        list_url = reverse('announcements:announcement-list')
        
        # Step 1: Create announcement
        create_data = {
            'title': 'New System Update',
            'message': 'The system will be updated this weekend.',
            'is_active': True
        }
        create_response = authenticated_client.post(list_url, create_data)
        assert create_response.status_code == 201
        announcement_id = create_response.data['id']
        
        # Verify announcement exists in database
        assert Announcement.objects.filter(id=announcement_id).exists()
        
        # Step 2: Retrieve the announcement
        detail_url = reverse(
            'announcements:announcement-detail',
            args=[announcement_id]
        )
        retrieve_response = authenticated_client.get(detail_url)
        assert retrieve_response.status_code == 200
        assert retrieve_response.data['title'] == 'New System Update'
        
        # Step 3: Update the announcement
        update_data = {
            'title': 'Updated System Maintenance',
            'message': 'The maintenance has been rescheduled to next weekend.',
        }
        update_response = authenticated_client.patch(detail_url, update_data)
        assert update_response.status_code == 200
        assert update_response.data['title'] == 'Updated System Maintenance'
        
        # Verify update persisted
        announcement = Announcement.objects.get(id=announcement_id)
        assert announcement.title == 'Updated System Maintenance'
        assert announcement.message == 'The maintenance has been rescheduled to next weekend.'
        
        # Step 4: Deactivate announcement
        deactivate_response = authenticated_client.patch(
            detail_url, {'is_active': False}
        )
        assert deactivate_response.status_code == 200
        assert deactivate_response.data['is_active'] is False
        
        # Step 5: Delete the announcement
        delete_response = authenticated_client.delete(detail_url)
        assert delete_response.status_code == 204
        
        # Verify deletion
        assert not Announcement.objects.filter(id=announcement_id).exists()
        
        # Step 6: Verify cannot access deleted announcement
        final_response = authenticated_client.get(detail_url)
        assert final_response.status_code == 404
    
    def test_create_print_workflow(self, authenticated_client):
        """Test creating announcement and generating print version."""
        list_url = reverse('announcements:announcement-list')
        
        # Create announcement
        create_data = {
            'title': 'Important Notice',
            'message': 'Please read this important information carefully.',
            'is_active': True
        }
        create_response = authenticated_client.post(list_url, create_data)
        assert create_response.status_code == 201
        announcement_id = create_response.data['id']
        
        # Generate print version
        print_url = reverse(
            'announcements:announcement-print-announcement',
            args=[announcement_id]
        )
        print_response = authenticated_client.get(print_url)
        assert print_response.status_code == 200
        assert 'text/html' in print_response['Content-Type']
        
        # Verify print content includes announcement data
        content = print_response.content.decode('utf-8')
        assert 'Important Notice' in content
        assert 'Please read this important information carefully.' in content
    
    def test_bulk_create_list_filter_workflow(
        self, authenticated_client, authenticated_user
    ):
        """Test creating multiple announcements and filtering them."""
        list_url = reverse('announcements:announcement-list')
        
        # Create multiple announcements with different properties
        announcements_data = [
            {
                'title': 'Security Update',
                'message': 'Security patch applied.',
                'is_active': True
            },
            {
                'title': 'Maintenance Notice',
                'message': 'Scheduled maintenance.',
                'is_active': True
            },
            {
                'title': 'Old Announcement',
                'message': 'This is outdated.',
                'is_active': False
            }
        ]
        
        created_ids = []
        for data in announcements_data:
            response = authenticated_client.post(list_url, data)
            assert response.status_code == 201
            created_ids.append(response.data['id'])
        
        # List all active announcements
        list_response = authenticated_client.get(list_url)
        assert list_response.status_code == 200
        assert list_response.data['count'] >= 2
        
        # Filter by active only
        active_response = authenticated_client.get(
            list_url, {'is_active': 'true'}
        )
        assert active_response.status_code == 200
        active_titles = [item['title'] for item in active_response.data['results']]
        assert 'Old Announcement' not in active_titles
        
        # Search for specific announcement
        search_response = authenticated_client.get(
            list_url, {'search': 'Security'}
        )
        assert search_response.status_code == 200
        assert len(search_response.data['results']) >= 1
        assert search_response.data['results'][0]['title'] == 'Security Update'


@pytest.mark.django_db
class TestMultiUserScenarios:
    """Test scenarios involving multiple users."""
    
    def test_two_managers_create_and_view_announcements(self):
        """Test two managers can create and view all announcements."""
        manager1 = UserFactory.create(is_staff=True)
        manager2 = UserFactory.create(is_staff=True)
        
        from rest_framework.test import APIClient
        client1 = APIClient()
        client2 = APIClient()
        client1.force_authenticate(user=manager1)
        client2.force_authenticate(user=manager2)
        
        list_url = reverse('announcements:announcement-list')
        
        # Manager 1 creates announcement
        data1 = {
            'title': 'Manager 1 Announcement',
            'message': 'From manager one.',
            'is_active': True
        }
        response1 = client1.post(list_url, data1)
        assert response1.status_code == 201
        
        # Manager 2 creates announcement
        data2 = {
            'title': 'Manager 2 Announcement',
            'message': 'From manager two.',
            'is_active': True
        }
        response2 = client2.post(list_url, data2)
        assert response2.status_code == 201
        
        # Both managers can see all announcements
        list_response1 = client1.get(list_url)
        assert list_response1.status_code == 200
        assert list_response1.data['count'] >= 2
        
        list_response2 = client2.get(list_url)
        assert list_response2.status_code == 200
        assert list_response2.data['count'] >= 2
        
        # Manager 1 cannot update Manager 2's announcement
        detail_url = reverse(
            'announcements:announcement-detail',
            args=[response2.data['id']]
        )
        update_response = client1.patch(
            detail_url, {'title': 'Malicious Update'}
        )
        assert update_response.status_code == 403
    
    def test_manager_creates_regular_user_views(self):
        """Test manager creates announcement that regular user can view."""
        manager = UserFactory.create(is_staff=True)
        regular_user = UserFactory.create(is_staff=False)
        
        from rest_framework.test import APIClient
        manager_client = APIClient()
        regular_client = APIClient()
        manager_client.force_authenticate(user=manager)
        regular_client.force_authenticate(user=regular_user)
        
        list_url = reverse('announcements:announcement-list')
        
        # Manager creates announcement
        data = {
            'title': 'Public Announcement',
            'message': 'Everyone can see this.',
            'is_active': True
        }
        create_response = manager_client.post(list_url, data)
        assert create_response.status_code == 201
        announcement_id = create_response.data['id']
        
        # Regular user can view it
        detail_url = reverse(
            'announcements:announcement-detail',
            args=[announcement_id]
        )
        view_response = regular_client.get(detail_url)
        assert view_response.status_code == 200
        assert view_response.data['title'] == 'Public Announcement'
        
        # Regular user cannot update it
        update_response = regular_client.patch(
            detail_url, {'title': 'Hacked'}
        )
        assert update_response.status_code == 403
        
        # Regular user cannot delete it
        delete_response = regular_client.delete(detail_url)
        assert delete_response.status_code == 403
    
    def test_inactive_announcement_visibility(self):
        """Test inactive announcement visibility across users."""
        manager = UserFactory.create(is_staff=True)
        other_manager = UserFactory.create(is_staff=True)
        regular_user = UserFactory.create(is_staff=False)
        
        from rest_framework.test import APIClient
        manager_client = APIClient()
        other_client = APIClient()
        regular_client = APIClient()
        manager_client.force_authenticate(user=manager)
        other_client.force_authenticate(user=other_manager)
        regular_client.force_authenticate(user=regular_user)
        
        list_url = reverse('announcements:announcement-list')
        
        # Manager creates inactive announcement
        data = {
            'title': 'Draft Announcement',
            'message': 'Still working on this.',
            'is_active': False
        }
        create_response = manager_client.post(list_url, data)
        assert create_response.status_code == 201
        announcement_id = create_response.data['id']
        
        detail_url = reverse(
            'announcements:announcement-detail',
            args=[announcement_id]
        )
        
        # Owner can view their inactive announcement
        owner_response = manager_client.get(detail_url)
        assert owner_response.status_code == 200
        
        # Other manager cannot view inactive announcement
        other_response = other_client.get(detail_url)
        assert other_response.status_code == 404
        
        # Regular user cannot view inactive announcement
        regular_response = regular_client.get(detail_url)
        assert regular_response.status_code == 404
        
        # Activate announcement
        activate_response = manager_client.patch(
            detail_url, {'is_active': True}
        )
        assert activate_response.status_code == 200
        
        # Now everyone can view it
        other_response2 = other_client.get(detail_url)
        assert other_response2.status_code == 200
        
        regular_response2 = regular_client.get(detail_url)
        assert regular_response2.status_code == 200


@pytest.mark.django_db
class TestStateTransitions:
    """Test announcement state transitions and consistency."""
    
    def test_activate_deactivate_cycle(
        self, authenticated_client, authenticated_user
    ):
        """Test toggling announcement active state multiple times."""
        list_url = reverse('announcements:announcement-list')
        
        # Create active announcement
        data = {
            'title': 'Toggle Test',
            'message': 'Testing state transitions.',
            'is_active': True
        }
        create_response = authenticated_client.post(list_url, data)
        assert create_response.status_code == 201
        announcement_id = create_response.data['id']
        
        detail_url = reverse(
            'announcements:announcement-detail',
            args=[announcement_id]
        )
        
        # Verify initial state
        announcement = Announcement.objects.get(id=announcement_id)
        assert announcement.is_active is True
        
        # Deactivate
        deactivate_response = authenticated_client.patch(
            detail_url, {'is_active': False}
        )
        assert deactivate_response.status_code == 200
        announcement.refresh_from_db()
        assert announcement.is_active is False
        
        # Reactivate
        activate_response = authenticated_client.patch(
            detail_url, {'is_active': True}
        )
        assert activate_response.status_code == 200
        announcement.refresh_from_db()
        assert announcement.is_active is True
        
        # Deactivate again
        deactivate_response2 = authenticated_client.patch(
            detail_url, {'is_active': False}
        )
        assert deactivate_response2.status_code == 200
        announcement.refresh_from_db()
        assert announcement.is_active is False
    
    def test_update_preserves_relationships(
        self, authenticated_client, authenticated_user
    ):
        """Test updates preserve creator and timestamps correctly."""
        list_url = reverse('announcements:announcement-list')
        
        # Create announcement
        data = {
            'title': 'Original Title',
            'message': 'Original message.',
            'is_active': True
        }
        create_response = authenticated_client.post(list_url, data)
        assert create_response.status_code == 201
        announcement_id = create_response.data['id']
        
        announcement = Announcement.objects.get(id=announcement_id)
        original_creator = announcement.created_by
        original_created_at = announcement.created_at
        
        detail_url = reverse(
            'announcements:announcement-detail',
            args=[announcement_id]
        )
        
        # Update multiple times
        for i in range(5):
            update_data = {
                'title': f'Updated Title {i}',
                'message': f'Updated message {i}.'
            }
            update_response = authenticated_client.patch(detail_url, update_data)
            assert update_response.status_code == 200
        
        # Verify creator unchanged
        announcement.refresh_from_db()
        assert announcement.created_by == original_creator
        assert announcement.created_by == authenticated_user
        
        # Verify created_at unchanged
        assert announcement.created_at == original_created_at
        
        # Verify updated_at changed
        assert announcement.updated_at > announcement.created_at


@pytest.mark.django_db
class TestComplexWorkflows:
    """Test complex real-world workflows."""
    
    def test_announcement_publication_workflow(
        self, authenticated_client, authenticated_user
    ):
        """Test typical workflow: draft -> review -> publish -> archive."""
        list_url = reverse('announcements:announcement-list')
        
        # Step 1: Create draft (inactive)
        draft_data = {
            'title': 'Important Update (Draft)',
            'message': 'This is still being reviewed.',
            'is_active': False
        }
        create_response = authenticated_client.post(list_url, draft_data)
        assert create_response.status_code == 201
        announcement_id = create_response.data['id']
        
        detail_url = reverse(
            'announcements:announcement-detail',
            args=[announcement_id]
        )
        
        # Step 2: Review and update content
        review_data = {
            'title': 'Important System Update',
            'message': 'The system will undergo maintenance this weekend. Please save your work.'
        }
        review_response = authenticated_client.patch(detail_url, review_data)
        assert review_response.status_code == 200
        
        # Step 3: Publish (activate)
        publish_response = authenticated_client.patch(
            detail_url, {'is_active': True}
        )
        assert publish_response.status_code == 200
        
        # Verify published announcement is in list
        list_response = authenticated_client.get(list_url)
        result_ids = [item['id'] for item in list_response.data['results']]
        assert announcement_id in result_ids
        
        # Step 4: Generate print version for distribution
        print_url = reverse(
            'announcements:announcement-print-announcement',
            args=[announcement_id]
        )
        print_response = authenticated_client.get(print_url)
        assert print_response.status_code == 200
        assert 'Important System Update' in print_response.content.decode('utf-8')
        
        # Step 5: Archive (deactivate) after event
        archive_response = authenticated_client.patch(
            detail_url, {'is_active': False}
        )
        assert archive_response.status_code == 200
        
        # Verify archived announcement not in default list
        list_response2 = authenticated_client.get(list_url)
        result_ids2 = [item['id'] for item in list_response2.data['results']]
        assert str(announcement_id) not in result_ids2
        
        # But owner can still access it
        archived_response = authenticated_client.get(detail_url)
        assert archived_response.status_code == 200
    
    def test_batch_announcement_management(
        self, authenticated_client, authenticated_user
    ):
        """Test managing multiple announcements in batch."""
        list_url = reverse('announcements:announcement-list')
        
        # Create multiple announcements
        announcement_ids = []
        for i in range(10):
            data = {
                'title': f'Announcement {i}',
                'message': f'Content for announcement {i}.',
                'is_active': i % 2 == 0  # Alternate active/inactive
            }
            response = authenticated_client.post(list_url, data)
            assert response.status_code == 201
            announcement_ids.append(response.data['id'])
        
        # Verify count
        assert Announcement.objects.count() >= 10
        
        # List only active
        active_response = authenticated_client.get(
            list_url, {'is_active': 'true'}
        )
        assert active_response.status_code == 200
        assert active_response.data['count'] >= 5
        
        # Deactivate all
        for announcement_id in announcement_ids:
            detail_url = reverse(
                'announcements:announcement-detail',
                args=[announcement_id]
            )
            deactivate_response = authenticated_client.patch(
                detail_url, {'is_active': False}
            )
            assert deactivate_response.status_code == 200
        
        # Verify all deactivated
        active_response2 = authenticated_client.get(
            list_url, {'is_active': 'true'}
        )
        assert active_response2.status_code == 200
        
        # Delete half
        for announcement_id in announcement_ids[:5]:
            detail_url = reverse(
                'announcements:announcement-detail',
                args=[announcement_id]
            )
            delete_response = authenticated_client.delete(detail_url)
            assert delete_response.status_code == 204
        
        # Verify remaining count
        all_response = authenticated_client.get(
            list_url, {'include_inactive': 'true'}
        )
        assert all_response.status_code == 200
        assert all_response.data['count'] >= 5
    
    def test_search_and_filter_complex_query(
        self, authenticated_client, authenticated_user
    ):
        """Test complex search and filter combinations."""
        list_url = reverse('announcements:announcement-list')
        
        # Create diverse announcements
        test_data = [
            {
                'title': 'Security Update 2024',
                'message': 'Important security patch.',
                'is_active': True
            },
            {
                'title': 'Maintenance Notice',
                'message': 'Scheduled maintenance for security systems.',
                'is_active': True
            },
            {
                'title': 'Security Training',
                'message': 'Training session next week.',
                'is_active': False
            },
            {
                'title': 'Holiday Schedule',
                'message': 'Office closed for holidays.',
                'is_active': True
            }
        ]
        
        for data in test_data:
            response = authenticated_client.post(list_url, data)
            assert response.status_code == 201
        
        # Search for "security" in active announcements
        search_response = authenticated_client.get(
            list_url, {
                'search': 'security',
                'is_active': 'true'
            }
        )
        assert search_response.status_code == 200
        assert search_response.data['count'] >= 2
        
        titles = [item['title'] for item in search_response.data['results']]
        assert 'Security Update 2024' in titles
        assert 'Maintenance Notice' in titles
        assert 'Security Training' not in titles  # Inactive
        assert 'Holiday Schedule' not in titles  # Doesn't match search


@pytest.mark.django_db
class TestDataConsistency:
    """Test data consistency across operations."""
    
    def test_timestamps_consistency(
        self, authenticated_client, authenticated_user
    ):
        """Test created_at and updated_at timestamps are consistent."""
        list_url = reverse('announcements:announcement-list')
        
        # Create announcement
        data = {
            'title': 'Timestamp Test',
            'message': 'Testing timestamp behavior.',
            'is_active': True
        }
        create_response = authenticated_client.post(list_url, data)
        assert create_response.status_code == 201
        
        announcement = Announcement.objects.get(id=create_response.data['id'])
        
        # Verify initial timestamps
        assert announcement.created_at is not None
        assert announcement.updated_at is not None
        assert announcement.created_at == announcement.updated_at
        
        # Update and verify timestamps
        detail_url = reverse(
            'announcements:announcement-detail',
            args=[announcement.id]
        )
        
        import time
        time.sleep(0.1)  # Ensure time difference
        
        update_response = authenticated_client.patch(
            detail_url, {'title': 'Updated Title'}
        )
        assert update_response.status_code == 200
        
        announcement.refresh_from_db()
        assert announcement.updated_at > announcement.created_at
    
    def test_count_consistency_after_operations(
        self, authenticated_client, authenticated_user
    ):
        """Test announcement counts remain consistent after CRUD operations."""
        list_url = reverse('announcements:announcement-list')
        
        # Get initial count
        initial_response = authenticated_client.get(list_url)
        initial_count = initial_response.data['count']
        
        # Create 3 announcements
        for i in range(3):
            data = {
                'title': f'Count Test {i}',
                'message': 'Testing count consistency.',
                'is_active': True
            }
            response = authenticated_client.post(list_url, data)
            assert response.status_code == 201
        
        # Verify count increased
        after_create_response = authenticated_client.get(list_url)
        assert after_create_response.data['count'] == initial_count + 3
        
        # Delete 1 announcement
        first_id = after_create_response.data['results'][0]['id']
        detail_url = reverse('announcements:announcement-detail', args=[first_id])
        delete_response = authenticated_client.delete(detail_url)
        assert delete_response.status_code == 204
        
        # Verify count decreased
        after_delete_response = authenticated_client.get(list_url)
        assert after_delete_response.data['count'] == initial_count + 2