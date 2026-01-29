# tests/test_urls.py
"""
Tests for documents app URL routing and reverse() lookups.

Coverage:
- All endpoints are accessible via reverse()
- URL patterns resolve correctly
- Router registration is correct
"""

import pytest
from django.urls import reverse, resolve
from documents import views


@pytest.mark.django_db
class TestDocumentURLs:
    """Test URL routing for Document endpoints."""
    
    def test_document_list_url(self):
        """Verify document list URL resolves correctly."""
        url = reverse('documents:document-list')
        assert url == '/api/documents/'
        
        resolved = resolve(url)
        assert resolved.func.cls == views.DocumentViewSet
    
    def test_document_detail_url(self):
        """Verify document detail URL resolves correctly."""
        doc_id = 'a1b2c3d4-e5f6-7890-abcd-ef1234567890'
        url = reverse('documents:document-detail', args=[doc_id])
        assert url == f'/api/documents/{doc_id}/'
        
        resolved = resolve(url)
        assert resolved.func.cls == views.DocumentViewSet
    
    def test_document_download_url(self):
        """Verify document download action URL resolves correctly."""
        doc_id = 'a1b2c3d4-e5f6-7890-abcd-ef1234567890'
        url = reverse('documents:document-download', args=[doc_id])
        assert url == f'/api/documents/{doc_id}/download/'
        
        resolved = resolve(url)
        assert resolved.func.cls == views.DocumentViewSet
    
    def test_document_regenerate_url(self):
        """Verify document regenerate action URL resolves correctly."""
        doc_id = 'a1b2c3d4-e5f6-7890-abcd-ef1234567890'
        url = reverse('documents:document-regenerate', args=[doc_id])
        assert url == f'/api/documents/{doc_id}/regenerate/'
        
        resolved = resolve(url)
        assert resolved.func.cls == views.DocumentViewSet
    
    def test_document_my_documents_url(self):
        """Verify my_documents action URL resolves correctly."""
        url = reverse('documents:document-my-documents')
        assert url == '/api/documents/my_documents/'
        
        resolved = resolve(url)
        assert resolved.func.cls == views.DocumentViewSet
    
    def test_document_stats_url(self):
        """Verify document stats action URL resolves correctly."""
        doc_id = 'a1b2c3d4-e5f6-7890-abcd-ef1234567890'
        url = reverse('documents:document-stats', args=[doc_id])
        assert url == f'/api/documents/{doc_id}/stats/'
        
        resolved = resolve(url)
        assert resolved.func.cls == views.DocumentViewSet


@pytest.mark.django_db
class TestDocumentDownloadURLs:
    """Test URL routing for DocumentDownload endpoints."""
    
    def test_download_list_url(self):
        """Verify download list URL resolves correctly."""
        url = reverse('documents:document-download-list')
        assert url == '/api/downloads/'
        
        resolved = resolve(url)
        assert resolved.func.cls == views.DocumentDownloadViewSet
    
    def test_download_detail_url(self):
        """Verify download detail URL resolves correctly."""
        download_id = 'a1b2c3d4-e5f6-7890-abcd-ef1234567890'
        url = reverse('documents:document-download-detail', args=[download_id])
        assert url == f'/api/downloads/{download_id}/'
        
        resolved = resolve(url)
        assert resolved.func.cls == views.DocumentDownloadViewSet