# tests/test_serializers.py

"""
Tests for announcements serializers.

Coverage:
- Serializer validation
- Field requirements
- Field constraints
- Nested serializers
- Read-only fields
"""

import pytest
from announcements.serializers import (
    AnnouncementSerializer,
    AnnouncementCreateSerializer,
    AnnouncementUpdateSerializer,
    AnnouncementCreatorSerializer,
)
from .factories import UserFactory, AnnouncementFactory


@pytest.mark.django_db
class TestAnnouncementCreatorSerializer:
    """Test AnnouncementCreatorSerializer."""
    
    def test_serializes_user_correctly(self):
        """Test user is serialized with correct fields."""
        user = UserFactory.create(first_name="John", last_name="Doe")
        serializer = AnnouncementCreatorSerializer(user)
        
        assert 'id' in serializer.data
        assert 'email' in serializer.data
        assert 'full_name' in serializer.data
        assert serializer.data['full_name'] == "John Doe"
    
    def test_full_name_falls_back_to_email(self):
        """Test full_name returns email when name not set."""
        user = UserFactory.create(first_name="", last_name="")
        serializer = AnnouncementCreatorSerializer(user)
        
        assert serializer.data['full_name'] == user.email


@pytest.mark.django_db
class TestAnnouncementSerializer:
    """Test AnnouncementSerializer (read)."""
    
    def test_serializes_announcement_correctly(self):
        """Test announcement is serialized with all fields."""
        announcement = AnnouncementFactory.create()
        serializer = AnnouncementSerializer(announcement)
        
        required_fields = [
            'id', 'title', 'message', 'preview',
            'created_by', 'is_active', 'created_at', 'updated_at'
        ]
        
        for field in required_fields:
            assert field in serializer.data
    
    def test_preview_truncates_long_messages(self):
        """Test preview field truncates messages over 100 chars."""
        message = "A" * 150
        announcement = AnnouncementFactory.create(message=message)
        serializer = AnnouncementSerializer(announcement)
        
        assert len(serializer.data['preview']) == 100
        assert serializer.data['preview'].endswith('...')
    
    def test_preview_shows_full_short_messages(self):
        """Test preview shows full message for short content."""
        message = "Short message"
        announcement = AnnouncementFactory.create(message=message)
        serializer = AnnouncementSerializer(announcement)
        
        assert serializer.data['preview'] == message
    
    def test_created_by_is_nested(self):
        """Test created_by field is properly nested."""
        announcement = AnnouncementFactory.create()
        serializer = AnnouncementSerializer(announcement)
        
        assert isinstance(serializer.data['created_by'], dict)
        assert 'id' in serializer.data['created_by']
        assert 'email' in serializer.data['created_by']


@pytest.mark.django_db
class TestAnnouncementCreateSerializer:
    """Test AnnouncementCreateSerializer (write)."""
    
    def test_valid_data_passes_validation(self):
        """Test serializer accepts valid data."""
        data = {
            'title': 'Test Announcement',
            'message': 'This is a test message with sufficient length.',
            'is_active': True
        }
        serializer = AnnouncementCreateSerializer(data=data)
        
        assert serializer.is_valid()
    
    def test_missing_title_fails_validation(self):
        """Test validation fails when title is missing."""
        data = {
            'message': 'This is a test message.',
            'is_active': True
        }
        serializer = AnnouncementCreateSerializer(data=data)
        
        assert not serializer.is_valid()
        assert 'title' in serializer.errors
    
    def test_missing_message_fails_validation(self):
        """Test validation fails when message is missing."""
        data = {
            'title': 'Test Announcement',
            'is_active': True
        }
        serializer = AnnouncementCreateSerializer(data=data)
        
        assert not serializer.is_valid()
        assert 'message' in serializer.errors
    
    def test_empty_title_fails_validation(self):
        """Test validation fails for empty title."""
        data = {
            'title': '',
            'message': 'This is a test message.',
            'is_active': True
        }
        serializer = AnnouncementCreateSerializer(data=data)
        
        assert not serializer.is_valid()
        assert 'title' in serializer.errors
    
    def test_whitespace_only_title_fails_validation(self):
        """Test validation fails for whitespace-only title."""
        data = {
            'title': '   ',
            'message': 'This is a test message.',
            'is_active': True
        }
        serializer = AnnouncementCreateSerializer(data=data)
        
        assert not serializer.is_valid()
        assert 'title' in serializer.errors
    
    def test_short_title_fails_validation(self):
        """Test validation fails for title under 3 characters."""
        data = {
            'title': 'AB',
            'message': 'This is a test message.',
            'is_active': True
        }
        serializer = AnnouncementCreateSerializer(data=data)
        
        assert not serializer.is_valid()
        assert 'title' in serializer.errors
    
    def test_empty_message_fails_validation(self):
        """Test validation fails for empty message."""
        data = {
            'title': 'Test Announcement',
            'message': '',
            'is_active': True
        }
        serializer = AnnouncementCreateSerializer(data=data)
        
        assert not serializer.is_valid()
        assert 'message' in serializer.errors
    
    def test_whitespace_only_message_fails_validation(self):
        """Test validation fails for whitespace-only message."""
        data = {
            'title': 'Test Announcement',
            'message': '   ',
            'is_active': True
        }
        serializer = AnnouncementCreateSerializer(data=data)
        
        assert not serializer.is_valid()
        assert 'message' in serializer.errors
    
    def test_short_message_fails_validation(self):
        """Test validation fails for message under 10 characters."""
        data = {
            'title': 'Test Announcement',
            'message': 'Short',
            'is_active': True
        }
        serializer = AnnouncementCreateSerializer(data=data)
        
        assert not serializer.is_valid()
        assert 'message' in serializer.errors
    
    def test_title_is_stripped(self):
        """Test title whitespace is stripped."""
        data = {
            'title': '  Test Announcement  ',
            'message': 'This is a test message.',
            'is_active': True
        }
        serializer = AnnouncementCreateSerializer(data=data)
        
        assert serializer.is_valid()
        assert serializer.validated_data['title'] == 'Test Announcement'
    
    def test_message_is_stripped(self):
        """Test message whitespace is stripped."""
        data = {
            'title': 'Test Announcement',
            'message': '  This is a test message.  ',
            'is_active': True
        }
        serializer = AnnouncementCreateSerializer(data=data)
        
        assert serializer.is_valid()
        assert serializer.validated_data['message'] == 'This is a test message.'
    
    def test_is_active_defaults_to_true(self):
        """Test is_active field is optional."""
        data = {
            'title': 'Test Announcement',
            'message': 'This is a test message.',
        }
        serializer = AnnouncementCreateSerializer(data=data)
        
        assert serializer.is_valid()


@pytest.mark.django_db
class TestAnnouncementUpdateSerializer:
    """Test AnnouncementUpdateSerializer (partial update)."""
    
    def test_partial_update_title_only(self):
        """Test can update only title."""
        announcement = AnnouncementFactory.create()
        data = {'title': 'Updated Title'}
        serializer = AnnouncementUpdateSerializer(
            announcement, data=data, partial=True
        )
        
        assert serializer.is_valid()
        assert serializer.validated_data['title'] == 'Updated Title'
    
    def test_partial_update_message_only(self):
        """Test can update only message."""
        announcement = AnnouncementFactory.create()
        data = {'message': 'Updated message content here.'}
        serializer = AnnouncementUpdateSerializer(
            announcement, data=data, partial=True
        )
        
        assert serializer.is_valid()
        assert serializer.validated_data['message'] == 'Updated message content here.'
    
    def test_partial_update_is_active_only(self):
        """Test can update only is_active."""
        announcement = AnnouncementFactory.create()
        data = {'is_active': False}
        serializer = AnnouncementUpdateSerializer(
            announcement, data=data, partial=True
        )
        
        assert serializer.is_valid()
        assert serializer.validated_data['is_active'] is False
    
    def test_update_validates_title_length(self):
        """Test update validates title minimum length."""
        announcement = AnnouncementFactory.create()
        data = {'title': 'AB'}
        serializer = AnnouncementUpdateSerializer(
            announcement, data=data, partial=True
        )
        
        assert not serializer.is_valid()
        assert 'title' in serializer.errors
    
    def test_update_validates_message_length(self):
        """Test update validates message minimum length."""
        announcement = AnnouncementFactory.create()
        data = {'message': 'Short'}
        serializer = AnnouncementUpdateSerializer(
            announcement, data=data, partial=True
        )
        
        assert not serializer.is_valid()
        assert 'message' in serializer.errors