# tests/test_ordering.py
"""
Tests for ordering/sorting functionality.

Coverage:
- Default ordering
- Custom ordering fields
- Ascending/descending
- Multiple field ordering
"""

import pytest
from django.urls import reverse
from documents.models import DocumentStatus
from .factories import DocumentFactory, CompletedDocumentFactory


@pytest.mark.django_db
class TestDocumentOrdering:
    """Test ordering on document list endpoint."""
    
    def test_default_ordering_by_created_desc(
        self, authenticated_client, user
    ):
        """Default ordering is by created_at descending."""
        doc1 = DocumentFactory.create(related_user=user, title="First")
        doc2 = DocumentFactory.create(related_user=user, title="Second")
        doc3 = DocumentFactory.create(related_user=user, title="Third")
        
        url = reverse('documents:document-list')
        response = authenticated_client.get(url)
        
        assert response.status_code == 200
        results = response.data['results']
        
        assert str(results[0]['id']) == str(doc3.id)
        assert str(results[1]['id']) == str(doc2.id)
        assert str(results[2]['id']) == str(doc1.id)
    
    def test_order_by_created_asc(self, authenticated_client, user):
        """Order by created_at ascending."""
        doc1 = DocumentFactory.create(related_user=user, title="First")
        doc2 = DocumentFactory.create(related_user=user, title="Second")
        doc3 = DocumentFactory.create(related_user=user, title="Third")
        
        url = reverse('documents:document-list')
        response = authenticated_client.get(url, {'ordering': 'created_at'})
        
        assert response.status_code == 200
        results = response.data['results']
        
        assert str(results[0]['id']) == str(doc1.id)
        assert str(results[1]['id']) == str(doc2.id)
        assert str(results[2]['id']) == str(doc3.id)
    
    def test_order_by_created_desc_explicit(
        self, authenticated_client, user
    ):
        """Explicit descending order with minus prefix."""
        doc1 = DocumentFactory.create(related_user=user)
        doc2 = DocumentFactory.create(related_user=user)
        
        url = reverse('documents:document-list')
        response = authenticated_client.get(url, {'ordering': '-created_at'})
        
        assert response.status_code == 200
        results = response.data['results']
        
        assert str(results[0]['id']) == str(doc2.id)
        assert str(results[1]['id']) == str(doc1.id)
    
    def test_order_by_title_asc(self, authenticated_client, user):
        """Order by title ascending."""
        DocumentFactory.create(related_user=user, title="Zebra")
        DocumentFactory.create(related_user=user, title="Alpha")
        DocumentFactory.create(related_user=user, title="Beta")
        
        url = reverse('documents:document-list')
        response = authenticated_client.get(url, {'ordering': 'title'})
        
        assert response.status_code == 200
        results = response.data['results']
        
        assert results[0]['title'] == "Alpha"
        assert results[1]['title'] == "Beta"
        assert results[2]['title'] == "Zebra"
    
    def test_order_by_title_desc(self, authenticated_client, user):
        """Order by title descending."""
        DocumentFactory.create(related_user=user, title="Alpha")
        DocumentFactory.create(related_user=user, title="Beta")
        DocumentFactory.create(related_user=user, title="Zebra")
        
        url = reverse('documents:document-list')
        response = authenticated_client.get(url, {'ordering': '-title'})
        
        assert response.status_code == 200
        results = response.data['results']
        
        assert results[0]['title'] == "Zebra"
        assert results[1]['title'] == "Beta"
        assert results[2]['title'] == "Alpha"
    
    def test_order_by_updated_at(self, authenticated_client, user):
        """Order by updated_at field."""
        doc1 = DocumentFactory.create(related_user=user)
        doc2 = DocumentFactory.create(related_user=user)
        
        doc1.title = "Updated"
        doc1.save()
        
        url = reverse('documents:document-list')
        response = authenticated_client.get(url, {'ordering': '-updated_at'})
        
        assert response.status_code == 200
        results = response.data['results']
        
        assert str(results[0]['id']) == str(doc1.id)
    
    def test_order_by_generated_at(self, authenticated_client, user):
        """Order by generated_at field."""
        CompletedDocumentFactory.create(related_user=user, title="First")
        CompletedDocumentFactory.create(related_user=user, title="Second")
        
        url = reverse('documents:document-list')
        response = authenticated_client.get(url, {'ordering': '-generated_at'})
        
        assert response.status_code == 200
        assert len(response.data['results']) == 2
    
    def test_invalid_ordering_field_ignored(
        self, authenticated_client, user
    ):
        """Invalid ordering field is ignored."""
        DocumentFactory.create_batch(3, related_user=user)
        
        url = reverse('documents:document-list')
        response = authenticated_client.get(
            url,
            {'ordering': 'invalid_field'}
        )
        
        assert response.status_code == 200
        assert len(response.data['results']) == 3
    
    def test_ordering_with_pagination(self, authenticated_client, user):
        """Ordering works with pagination."""
        for i in range(25):
            DocumentFactory.create(
                related_user=user,
                title=f"Document {i:02d}"
            )
        
        url = reverse('documents:document-list')
        response = authenticated_client.get(
            url,
            {'ordering': 'title', 'page_size': 10}
        )
        
        assert response.status_code == 200
        assert len(response.data['results']) == 10
        assert response.data['results'][0]['title'] == "Document 00"
    
    def test_ordering_with_filters(self, authenticated_client, user):
        """Ordering works with filters."""
        CompletedDocumentFactory.create(related_user=user, title="Z Complete")
        CompletedDocumentFactory.create(related_user=user, title="A Complete")
        DocumentFactory.create(
            related_user=user,
            title="B Pending",
            status=DocumentStatus.PENDING
        )
        
        url = reverse('documents:document-list')
        response = authenticated_client.get(url, {
            'status': 'completed',
            'ordering': 'title'
        })
        
        assert response.status_code == 200
        assert response.data['count'] == 2
        assert response.data['results'][0]['title'] == "A Complete"


@pytest.mark.django_db
class TestDocumentDownloadOrdering:
    """Test ordering on download list endpoint."""
    
    def test_default_ordering_by_downloaded_desc(
        self, authenticated_client, user
    ):
        """Default ordering is by downloaded_at descending."""
        from .factories import DocumentDownloadFactory, CompletedDocumentFactory
        
        document = CompletedDocumentFactory.create(related_user=user)
        download1 = DocumentDownloadFactory.create(document=document)
        download2 = DocumentDownloadFactory.create(document=document)
        download3 = DocumentDownloadFactory.create(document=document)
        
        url = reverse('documents:document-download-list')
        response = authenticated_client.get(url)
        
        assert response.status_code == 200
        results = response.data['results']
        
        assert str(results[0]['id']) == str(download3.id)
        assert str(results[1]['id']) == str(download2.id)
        assert str(results[2]['id']) == str(download1.id)
    
    def test_order_downloads_by_date_asc(self, authenticated_client, user):
        """Order downloads by date ascending."""
        from .factories import DocumentDownloadFactory, CompletedDocumentFactory
        
        document = CompletedDocumentFactory.create(related_user=user)
        download1 = DocumentDownloadFactory.create(document=document)
        download2 = DocumentDownloadFactory.create(document=document)
        
        url = reverse('documents:document-download-list')
        response = authenticated_client.get(
            url,
            {'ordering': 'downloaded_at'}
        )
        
        assert response.status_code == 200
        results = response.data['results']
        
        assert str(results[0]['id']) == str(download1.id)
        assert str(results[1]['id']) == str(download2.id)