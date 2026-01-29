"""
API views for documents app.
"""

import logging
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.pagination import PageNumberPagination
from rest_framework.filters import  OrderingFilter
from django_filters.rest_framework import DjangoFilterBackend
from django.http import FileResponse
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

from .models import Document, DocumentDownload, DocumentStatus
from .serializers import (
    DocumentSerializer,
    DocumentCreateSerializer,
    DocumentUpdateSerializer,
    DocumentListSerializer,
    DocumentDownloadSerializer,
    DocumentRegenerateSerializer,
)
from .permissions import (
    IsDocumentOwnerOrAdmin,
    CanDownloadDocument,
    CanViewDocumentDownloads,
)
from .filters import DocumentFilter, DocumentDownloadFilter
from . import services

logger = logging.getLogger(__name__)


class StandardResultsSetPagination(PageNumberPagination):
    """Standard pagination for document lists."""
    
    page_size = 20
    page_size_query_param = 'page_size'
    max_page_size = 100


class DocumentViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing documents.
    
    Provides CRUD operations for system-generated PDF documents including
    payment receipts and announcements.
    
    list: Get paginated list of documents
    retrieve: Get specific document details
    create: Create new document (initiates generation)
    update: Update document metadata
    partial_update: Partially update document
    destroy: Soft delete document
    
    Custom actions:
    - download: Download document PDF file
    - regenerate: Trigger document regeneration
    - my_documents: Get current user's documents
    - stats: Get document download statistics
    """
    
    permission_classes = [IsAuthenticated, IsDocumentOwnerOrAdmin]
    pagination_class = StandardResultsSetPagination
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_class = DocumentFilter
    # search_fields = ['title', 'error_message']
    ordering_fields = ['created_at', 'updated_at', 'generated_at', 'title']
    ordering = ['-created_at']
    
    def get_queryset(self):
        """
        Get queryset filtered by user permissions.
        
        Admin users see all documents.
        Regular users only see their own documents.
        """
        if getattr(self, 'swagger_fake_view', False):
            return Document.objects.none()
        user = self.request.user
        
        if user.is_staff or user.is_superuser:
            queryset = Document.objects.all()
        else:
            queryset = Document.objects.filter(related_user=user)
        
        queryset = queryset.filter(is_deleted=False)
        
        return queryset.select_related('related_user').prefetch_related('downloads')
    
    def get_serializer_class(self):
        """Return appropriate serializer based on action."""
        if self.action == 'list':
            return DocumentListSerializer
        elif self.action == 'create':
            return DocumentCreateSerializer
        elif self.action in ['update', 'partial_update']:
            return DocumentUpdateSerializer
        elif self.action == 'regenerate':
            return DocumentRegenerateSerializer
        return DocumentSerializer
    
    @swagger_auto_schema(
        operation_description="Create a new document and initiate PDF generation",
        responses={201: DocumentSerializer()}
    )
    def create(self, request, *args, **kwargs):
        """Create new document via service layer."""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        try:
            document = services.create_document(**serializer.validated_data)
            
            output_serializer = DocumentSerializer(
                document,
                context={'request': request}
            )
            
            logger.info(f"Document created via API: {document.id}")
            return Response(
                output_serializer.data,
                status=status.HTTP_201_CREATED
            )
            
        except ValueError as e:
            logger.error(f"Document creation failed: {e}")
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
    
    @swagger_auto_schema(
        operation_description="Update document metadata",
        responses={200: DocumentSerializer()}
    )
    def update(self, request, *args, **kwargs):
        """Update document via service layer."""
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        
        try:
            document = services.update_document(
                document=instance,
                **serializer.validated_data
            )
            
            output_serializer = DocumentSerializer(
                document,
                context={'request': request}
            )
            
            logger.info(f"Document updated via API: {document.id}")
            return Response(output_serializer.data)
            
        except ValueError as e:
            logger.error(f"Document update failed: {e}")
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
    
    def perform_destroy(self, instance):
        """Soft delete document via service layer."""
        services.soft_delete_document(document=instance)
        logger.info(f"Document soft deleted via API: {instance.id}")
    
    @swagger_auto_schema(
        method='get',
        operation_description="Download document PDF file",
        responses={
            200: openapi.Response('PDF file', schema=openapi.Schema(type=openapi.TYPE_FILE)),
            404: 'Document not found or not ready'
        }
    )
    @action(
        detail=True,
        methods=['get'],
        permission_classes=[IsAuthenticated, CanDownloadDocument]
    )
    
    def download(self, request, pk=None):
        """
        Download document PDF file.
        
        Records download event for analytics.
        """
        document = self.get_object()
        if document.is_deleted:
            return Response(
                {'error': 'Document not found'},
                status=status.HTTP_404_NOT_FOUND
            )

        
        if document.status != DocumentStatus.COMPLETED or not document.file:
            logger.warning(f"Attempt to download incomplete document: {document.id}")
            return Response(
                {'error': 'Document is not ready for download'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        try:
            ip_address = self.get_client_ip(request)
            user_agent = request.META.get('HTTP_USER_AGENT', '')
            
            services.record_document_download(
                document=document,
                user=request.user,
                ip_address=ip_address,
                user_agent=user_agent,
            )
            
            response = FileResponse(
                document.file.open('rb'),
                content_type='application/pdf'
            )
            response['Content-Disposition'] = f'attachment; filename="{document.file.name.split("/")[-1]}"'
            
            logger.info(f"Document downloaded: {document.id} by user {request.user.id}")
            return response
            
        except ValueError as e:
            logger.error(f"Download failed for document {document.id}: {e}")
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            logger.error(f"Unexpected error during download: {e}")
            return Response(
                {'error': 'Download failed'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @swagger_auto_schema(
        method='post',
        operation_description="Regenerate document PDF",
        request_body=DocumentRegenerateSerializer,
        responses={200: DocumentSerializer()}
    )
    @action(
        detail=True,
        methods=['post'],
        permission_classes=[IsAuthenticated, IsDocumentOwnerOrAdmin]
    )
    def regenerate(self, request, pk=None):
        """
        Trigger document regeneration.
        
        Can force regeneration even if document already exists.
        """
        document = self.get_object()
        serializer = DocumentRegenerateSerializer(
            data=request.data,
            context={'document': document}
        )
        serializer.is_valid(raise_exception=True)
        
        try:
            document = services.regenerate_document(
                document=document,
                **serializer.validated_data
            )
            
            output_serializer = DocumentSerializer(
                document,
                context={'request': request}
            )
            
            logger.info(f"Document regeneration initiated: {document.id}")
            return Response(output_serializer.data)
            
        except ValueError as e:
            logger.error(f"Regeneration failed for document {document.id}: {e}")
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
    
    @swagger_auto_schema(
        method='get',
        operation_description="Get current user's documents",
        responses={200: DocumentListSerializer(many=True)}
    )
    @action(
        detail=False,
        methods=['get'],
        permission_classes=[IsAuthenticated]
    )
    def my_documents(self, request):
        """
        Get documents for the authenticated user.
        
        Supports filtering by document_type and status via query params.
        """
        document_type = request.query_params.get('document_type')
        doc_status = request.query_params.get('status')
        
        documents = services.get_user_documents(
            user=request.user,
            document_type=document_type,
            status=doc_status,
        )
        
        page = self.paginate_queryset(documents)
        if page is not None:
            serializer = DocumentListSerializer(
                page,
                many=True,
                context={'request': request}
            )
            return self.get_paginated_response(serializer.data)
        
        serializer = DocumentListSerializer(
            documents,
            many=True,
            context={'request': request}
        )
        return Response(serializer.data)
    
    @swagger_auto_schema(
        method='get',
        operation_description="Get download statistics for a document",
        responses={200: openapi.Response('Download statistics')}
    )
    @action(
        detail=True,
        methods=['get'],
        permission_classes=[IsAuthenticated, IsDocumentOwnerOrAdmin]
    )
    def stats(self, request, pk=None):
        """Get download statistics for a document."""
        document = self.get_object()
        
        stats = services.get_document_download_stats(document=document)
        
        logger.info(f"Stats retrieved for document: {document.id}")
        return Response(stats)
    
    def get_client_ip(self, request):
        """Extract client IP address from request."""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip


class DocumentDownloadViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for viewing document download records.
    
    Read-only access to download history for analytics and auditing.
    
    list: Get paginated list of downloads
    retrieve: Get specific download record
    """
    
    serializer_class = DocumentDownloadSerializer
    permission_classes = [IsAuthenticated, CanViewDocumentDownloads]
    pagination_class = StandardResultsSetPagination
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_class = DocumentDownloadFilter
    ordering_fields = ['downloaded_at']
    ordering = ['-downloaded_at']
    
    def get_queryset(self):
        """
        Get queryset filtered by user permissions.
        
        Admin users see all downloads.
        Regular users only see downloads of their own documents.
        """
            # Short-circuit during schema generation
        if getattr(self, 'swagger_fake_view', False):
            return DocumentDownload.objects.none()
        user = self.request.user
        
        if user.is_staff or user.is_superuser:
            queryset = DocumentDownload.objects.all()
        else:
            queryset = DocumentDownload.objects.filter(
                document__related_user=user
            )
        
        return queryset.select_related('document', 'user')