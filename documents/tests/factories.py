# tests/factories.py

"""
Factory Boy factories for payments app models.

Provides realistic test data generation for all models.
"""

import factory
from factory.django import DjangoModelFactory
from faker import Faker
from decimal import Decimal
from django.utils import timezone
from datetime import timedelta
from accounts.models import User  # Import your custom User model
from units.models import Unit
from estates.models import Estate 
import uuid
from django.contrib.auth import get_user_model
from django.core.files.base import ContentFile
from documents.models import Document, DocumentDownload, DocumentType, DocumentStatus



class UserFactory(DjangoModelFactory):
    """Factory for User model."""
    
    class Meta:
        model = User  # Use your custom User model
        skip_postgeneration_save = True
    
    email = factory.Sequence(lambda n: f"user{n}@example.com")
    first_name = factory.Faker("first_name")
    last_name = factory.Faker("last_name")
    is_active = True
    is_staff = False
    is_superuser = False
    
    @factory.post_generation
    def password(self, create, extracted, **kwargs):
        """Set password after user creation."""
        if not create:
            return
        self.set_password(extracted or 'testpass123')



class DocumentFactory(DjangoModelFactory):
    """Factory for Document model."""
    
    class Meta:
        model = Document
    
    id = factory.LazyFunction(uuid.uuid4)
    document_type = DocumentType.PAYMENT_RECEIPT
    title = factory.Faker("sentence", nb_words=4)
    status = DocumentStatus.PENDING
    related_user = factory.SubFactory(UserFactory)
    related_payment_id = factory.LazyFunction(uuid.uuid4)
    related_announcement_id = None
    metadata = factory.Dict({})
    error_message = ""
    file_size = None
    is_deleted = False
    
    @factory.post_generation
    def with_file(obj, create, extracted, **kwargs):
        """Optionally add a PDF file to the document."""
        if create and extracted:
            pdf_content = b"%PDF-1.4 fake pdf content"
            obj.file.save(
                f"test_document_{obj.id}.pdf",
                ContentFile(pdf_content),
                save=True
            )
            obj.file_size = len(pdf_content)
            obj.status = DocumentStatus.COMPLETED
            obj.save()


class PaymentReceiptFactory(DocumentFactory):
    """Factory for payment receipt documents."""
    
    document_type = DocumentType.PAYMENT_RECEIPT
    related_payment_id = factory.LazyFunction(uuid.uuid4)
    related_announcement_id = None


class AnnouncementDocumentFactory(DocumentFactory):
    """Factory for announcement documents."""
    
    document_type = DocumentType.ANNOUNCEMENT
    related_payment_id = None
    related_announcement_id = factory.LazyFunction(uuid.uuid4)


class CompletedDocumentFactory(DocumentFactory):
    """Factory for completed documents with files."""
    
    status = DocumentStatus.COMPLETED
    file_size = 1024
    
    @factory.lazy_attribute
    def file(self):
        """Generate a fake PDF file."""
        pdf_content = b"%PDF-1.4 fake pdf content"
        return ContentFile(pdf_content, name=f"document_{self.id}.pdf")


class FailedDocumentFactory(DocumentFactory):
    """Factory for failed document generation."""
    
    status = DocumentStatus.FAILED
    error_message = factory.Faker("sentence")


class DocumentDownloadFactory(DjangoModelFactory):
    """Factory for DocumentDownload model."""
    
    class Meta:
        model = DocumentDownload
    
    id = factory.LazyFunction(uuid.uuid4)
    document = factory.SubFactory(CompletedDocumentFactory)
    user = factory.SubFactory(UserFactory)
    ip_address = factory.Faker("ipv4")
    user_agent = factory.Faker("user_agent")