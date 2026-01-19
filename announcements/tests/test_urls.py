# tests/test_urls.py

"""
Tests for announcements URL routing and reverse resolution.

Coverage:
- URL patterns are correctly configured
- reverse() resolves all expected URLs
- URL parameters work correctly
"""

import pytest
from django.urls import reverse, resolve
from announcements import views


@pytest.mark.django_db
class TestAnnouncementURLs:
    """Test URL routing for announcement endpoints."""
    
    def test_announcement_list_url_resolves(self):
        """Test announcement list URL resolves correctly."""
        url = reverse('announcements:announcement-list')
        assert url == '/api/announcements/'
        
        resolver = resolve(url)
        assert resolver.func.cls == views.AnnouncementViewSet
    
    def test_announcement_detail_url_resolves(self, announcement):
        """Test announcement detail URL resolves with UUID."""
        url = reverse('announcements:announcement-detail', args=[announcement.id])
        assert str(announcement.id) in url
        
        resolver = resolve(url)
        assert resolver.func.cls == views.AnnouncementViewSet
    
    def test_announcement_print_url_resolves(self, announcement):
        """Test announcement print action URL resolves."""
        url = reverse('announcements:announcement-print-announcement', args=[announcement.id])
        assert 'print' in url
        
        resolver = resolve(url)
        assert resolver.func.cls == views.AnnouncementViewSet
    
    def test_all_viewset_actions_have_urls(self):
        """Test all expected viewset actions have URL patterns."""
        expected_actions = [
            ('announcements:announcement-list', []),
            ('announcements:announcement-detail', ['00000000-0000-0000-0000-000000000000']),
        ]
        
        for url_name, args in expected_actions:
            try:
                url = reverse(url_name, args=args)
                assert url is not None
            except Exception as e:
                pytest.fail(f"Failed to reverse {url_name}: {str(e)}")