# announcements/views_with_pdf.py

"""
Enhanced API views for announcements app with PDF support.

This extends the original views with PDF generation and download capabilities.
SECURITY: Managers can only access announcements from their assigned estate.
"""

import logging
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import OrderingFilter
from django.http import HttpResponse, FileResponse
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from django.db.models import Q

from .models import Announcement
from .serializers import (
    AnnouncementSerializer,
    AnnouncementCreateSerializer,
    AnnouncementUpdateSerializer,
)
from .permissions import IsManagerOrReadOnly, IsOwnerOrReadOnly, IsActiveUser
from .filters import AnnouncementFilter
from . import services
from .utils import (
    get_announcement_pdf,
    regenerate_announcement_pdf,
)

logger = logging.getLogger(__name__)


class AnnouncementViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing announcements with PDF support.
    
    Provides CRUD operations for announcements:
    - list: Get all announcements visible to the user (filtered by estate for managers)
    - retrieve: Get a specific announcement
    - create: Create a new announcement (managers only, auto-generates PDF)
    - update: Update an announcement (owner only)
    - partial_update: Partially update an announcement (owner only)
    - destroy: Delete an announcement (owner only)
    
    Additional actions:
    - print: Get a printable HTML version of an announcement
    - download_pdf: Download the generated PDF for an announcement
    - regenerate_pdf: Regenerate the PDF for an announcement
    - pdf_status: Check PDF generation status
    
    SECURITY:
    - Superusers can see all announcements
    - Managers (is_staff) can only see announcements from their assigned estate
    - Regular users can only see active announcements from their estate
    """
    
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_class = AnnouncementFilter
    ordering_fields = ['created_at', 'updated_at', 'title']
    ordering = ['-created_at']

    def get_permissions(self):
        """Apply different permissions based on action."""
        if self.action == 'create':
            permission_classes = [IsAuthenticated, IsManagerOrReadOnly, IsActiveUser]
        elif self.action in ['update', 'partial_update', 'destroy', 'regenerate_pdf']:
            permission_classes = [IsAuthenticated, IsOwnerOrReadOnly, IsActiveUser]
        else:
            permission_classes = [IsAuthenticated, IsActiveUser]
        
        return [permission() for permission in permission_classes]
    
    def get_queryset(self):
        """
        Filter queryset to only show announcements from user's estate.
        
        Only superusers can see all announcements.
        Managers (is_staff) and regular users can only see announcements from their assigned estate.
        
        Returns:
            Filtered QuerySet of Announcement instances
        """
        if getattr(self, 'swagger_fake_view', False):
            return Announcement.objects.none()

        user = self.request.user
        
        if not user.is_authenticated:
            return Announcement.objects.none()
        
        queryset = Announcement.objects.all()

        # Actions that MUST see the object (for permission checks)
        if self.action in [
            'update',
            'partial_update',
            'destroy',
            'print_announcement',
            'download_pdf',
            'regenerate_pdf',
            'pdf_status',
        ]:
            # Still need to filter by estate for non-superusers
            if not user.is_superuser:
                if not user.estate:
                    logger.warning(
                        f"User {user.id} (is_staff={user.is_staff}) has no estate assigned"
                    )
                    return Announcement.objects.none()
                queryset = queryset.filter(estate=user.estate)
            return queryset

        # Only superusers can see all announcements (not is_staff)
        if user.is_superuser:
            logger.info(f"Superuser {user.id} accessing all announcements")
            # Continue with active/inactive filtering below
        else:
            # Managers (is_staff) and regular users can only see announcements from their estate
            if not user.estate:
                logger.warning(
                    f"User {user.id} (is_staff={user.is_staff}) has no estate assigned, returning empty queryset"
                )
                return Announcement.objects.none()
            
            queryset = queryset.filter(estate=user.estate)
            logger.info(
                f"Filtering announcements for user {user.id} (is_staff={user.is_staff}) "
                f"to estate {user.estate.id}"
            )

        # Retrieve logic
        if self.action == 'retrieve':
            return queryset.filter(
                Q(is_active=True) | Q(created_by=user)
            )

        # LIST behavior (query-aware)
        include_inactive = self.request.query_params.get('include_inactive')
        is_active_param = self.request.query_params.get('is_active')

        if include_inactive == 'true':
            qs = queryset
        else:
            qs = queryset.filter(is_active=True)

        if is_active_param == 'true':
            qs = qs.filter(is_active=True)
        elif is_active_param == 'false':
            qs = qs.filter(is_active=False)

        return qs

    def get_serializer_class(self):
        """Return appropriate serializer class based on action."""
        if self.action == 'create':
            return AnnouncementCreateSerializer
        elif self.action in ['update', 'partial_update']:
            return AnnouncementUpdateSerializer
        return AnnouncementSerializer
    
    @swagger_auto_schema(
        operation_description="List all announcements visible to the user",
        responses={200: AnnouncementSerializer(many=True)}
    )
    def list(self, request, *args, **kwargs):
        """List all announcements visible to the user."""
        logger.info(f"User {request.user.id} listing announcements")
        return super().list(request, *args, **kwargs)
    
    @swagger_auto_schema(
        operation_description="Retrieve a specific announcement",
        responses={
            200: AnnouncementSerializer(),
            404: "Announcement not found"
        }
    )
    def retrieve(self, request, *args, **kwargs):
        """Retrieve a specific announcement."""
        logger.info(
            f"User {request.user.id} retrieving announcement {kwargs.get('pk')}"
        )
        return super().retrieve(request, *args, **kwargs)
    
    @swagger_auto_schema(
        operation_description="Create a new announcement (managers only). PDF generation is triggered automatically.",
        request_body=AnnouncementCreateSerializer,
        responses={
            201: AnnouncementSerializer(),
            400: "Invalid input",
            403: "Permission denied"
        }
    )
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        # Validate estate assignment for non-superusers
        if not request.user.is_superuser:
            estate_id = serializer.validated_data.get('estate')
            if estate_id and hasattr(request.user, 'estate'):
                if request.user.estate and str(request.user.estate.id) != str(estate_id.id):
                    logger.warning(
                        f"User {request.user.id} (is_staff={request.user.is_staff}) "
                        f"attempted to create announcement for estate {estate_id.id} "
                        f"but they manage estate {request.user.estate.id}"
                    )
                    return Response(
                        {'error': 'You can only create announcements for your assigned estate'},
                        status=status.HTTP_403_FORBIDDEN
                    )

        announcement = services.create_announcement(
            created_by=request.user,
            **serializer.validated_data
        )

        output_serializer = AnnouncementSerializer(
            announcement,
            context=self.get_serializer_context()
        )

        headers = self.get_success_headers(output_serializer.data)
        return Response(
            output_serializer.data,
            status=status.HTTP_201_CREATED,
            headers=headers
        )
    
    @swagger_auto_schema(
        operation_description="Update an announcement (owner only)",
        request_body=AnnouncementUpdateSerializer,
        responses={
            200: AnnouncementSerializer(),
            400: "Invalid input",
            403: "Permission denied",
            404: "Announcement not found"
        }
    )
    def update(self, request, *args, **kwargs):
        """Update an announcement."""
        logger.info(
            f"User {request.user.id} updating announcement {kwargs.get('pk')}"
        )
        return super().update(request, *args, **kwargs)
    
    @swagger_auto_schema(
        operation_description="Partially update an announcement (owner only)",
        request_body=AnnouncementUpdateSerializer,
        responses={
            200: AnnouncementSerializer(),
            400: "Invalid input",
            403: "Permission denied",
            404: "Announcement not found"
        }
    )
    def partial_update(self, request, *args, **kwargs):
        """Partially update an announcement."""
        logger.info(
            f"User {request.user.id} partially updating announcement {kwargs.get('pk')}"
        )
        return super().partial_update(request, *args, **kwargs)
    
    @swagger_auto_schema(
        operation_description="Delete an announcement (owner only)",
        responses={
            204: "Announcement deleted successfully",
            403: "Permission denied",
            404: "Announcement not found"
        }
    )
    def destroy(self, request, *args, **kwargs):
        """Delete an announcement."""
        logger.info(
            f"User {request.user.id} deleting announcement {kwargs.get('pk')}"
        )
        return super().destroy(request, *args, **kwargs)
    
    def perform_create(self, serializer):
        """Create announcement using service layer."""
        try:
            announcement = services.create_announcement(
                created_by=self.request.user,
                **serializer.validated_data
            )
            serializer.instance = announcement
            
        except Exception as e:
            logger.error(
                f"Error creating announcement for user {self.request.user.id}: {str(e)}"
            )
            raise
    
    def perform_update(self, serializer):
        """Update announcement using service layer."""
        try:
            announcement = services.update_announcement(
                announcement=serializer.instance,
                user=self.request.user,
                **serializer.validated_data
            )
            serializer.instance = announcement
            
        except Exception as e:
            logger.error(
                f"Error updating announcement {serializer.instance.id}: {str(e)}"
            )
            raise
    
    def perform_destroy(self, instance):
        """Delete announcement using service layer."""
        try:
            services.delete_announcement(
                announcement=instance,
                user=self.request.user
            )
            
        except Exception as e:
            logger.error(
                f"Error deleting announcement {instance.id}: {str(e)}"
            )
            raise
    
    @swagger_auto_schema(
        method='get',
        operation_description="Get a printable HTML version of an announcement",
        responses={
            200: openapi.Response(
                description="HTML content for printing",
                schema=openapi.Schema(type=openapi.TYPE_STRING)
            ),
            404: "Announcement not found"
        }
    )
    @action(detail=True, methods=['get'], url_path='print')
    def print_announcement(self, request, pk=None):
        """
        Get a printable HTML version of an announcement.
        
        Returns an HTML page optimized for printing.
        """
        logger.info(
            f"User {request.user.id} requesting print version of announcement {pk}"
        )
        
        announcement = self.get_object()
        
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <title>{announcement.title}</title>
            <style>
                @media print {{
                    body {{ margin: 2cm; }}
                }}
                body {{
                    font-family: Arial, sans-serif;
                    max-width: 800px;
                    margin: 0 auto;
                    padding: 20px;
                }}
                .header {{
                    border-bottom: 2px solid #333;
                    padding-bottom: 10px;
                    margin-bottom: 20px;
                }}
                .title {{
                    font-size: 24px;
                    font-weight: bold;
                    margin-bottom: 10px;
                }}
                .meta {{
                    font-size: 14px;
                    color: #666;
                }}
                .message {{
                    line-height: 1.6;
                    white-space: pre-wrap;
                    margin-top: 20px;
                }}
                .footer {{
                    margin-top: 30px;
                    padding-top: 10px;
                    border-top: 1px solid #ccc;
                    font-size: 12px;
                    color: #666;
                }}
            </style>
        </head>
        <body>
            <div class="header">
                <div class="title">{announcement.title}</div>
                <div class="meta">
                    Posted by: {announcement.created_by.email}<br>
                    Date: {announcement.created_at.strftime('%B %d, %Y at %I:%M %p')}
                </div>
            </div>
            <div class="message">{announcement.message}</div>
            <div class="footer">
                <p>Estatly Estate Management System</p>
            </div>
        </body>
        </html>
        """
        
        return HttpResponse(html_content, content_type='text/html; charset=utf-8')
    
    @swagger_auto_schema(
        method='get',
        operation_description="Download the PDF version of an announcement",
        responses={
            200: openapi.Response(
                description="PDF file",
                schema=openapi.Schema(type=openapi.TYPE_FILE)
            ),
            404: "PDF not found or not ready",
            500: "PDF generation failed"
        }
    )
    @action(detail=True, methods=['get'], url_path='download-pdf')
    def download_pdf(self, request, pk=None):
        """
        Download the generated PDF for an announcement.
        
        Returns the PDF file if generation is complete.
        """
        logger.info(
            f"User {request.user.id} requesting PDF download for announcement {pk}"
        )
        
        announcement = self.get_object()
        document = get_announcement_pdf(announcement)
        
        if not document:
            logger.warning(
                f"PDF not ready for announcement {pk}"
            )
            return Response(
                {
                    'error': 'PDF is not ready yet. Check status endpoint.',
                    'status': 'not_ready'
                },
                status=status.HTTP_404_NOT_FOUND
            )
        
        try:
            response = FileResponse(
                document.file.open('rb'),
                content_type='application/pdf'
            )
            filename = f"announcement_{announcement.id}.pdf"
            response['Content-Disposition'] = f'attachment; filename="{filename}"'
            
            logger.info(
                f"PDF downloaded for announcement {pk} by user {request.user.id}"
            )
            return response
            
        except Exception as e:
            logger.error(f"Error downloading PDF for announcement {pk}: {e}")
            return Response(
                {'error': 'Failed to download PDF'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @swagger_auto_schema(
        method='post',
        operation_description="Regenerate the PDF for an announcement",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'force': openapi.Schema(
                    type=openapi.TYPE_BOOLEAN,
                    description='Force regeneration even if PDF exists'
                )
            }
        ),
        responses={
            200: openapi.Response(
                description="PDF regeneration initiated",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'message': openapi.Schema(type=openapi.TYPE_STRING),
                        'document_id': openapi.Schema(type=openapi.TYPE_STRING),
                        'status': openapi.Schema(type=openapi.TYPE_STRING)
                    }
                )
            ),
            400: "Bad request",
            403: "Permission denied"
        }
    )
    @action(detail=True, methods=['post'], url_path='regenerate-pdf')
    def regenerate_pdf(self, request, pk=None):
        """
        Regenerate the PDF for an announcement.
        
        Useful if PDF generation failed or content was updated.
        """
        logger.info(
            f"User {request.user.id} requesting PDF regeneration for announcement {pk}"
        )
        
        announcement = self.get_object()
        force = request.data.get('force', False)
        
        document = regenerate_announcement_pdf(announcement, force=force)
        
        if not document:
            return Response(
                {'error': 'Failed to regenerate PDF'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        return Response({
            'message': 'PDF regeneration initiated',
            'document_id': str(document.id),
            'status': document.status
        })
    
    @swagger_auto_schema(
        method='get',
        operation_description="Check PDF generation status for an announcement",
        responses={
            200: openapi.Response(
                description="PDF status information",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'status': openapi.Schema(type=openapi.TYPE_STRING),
                        'document_id': openapi.Schema(type=openapi.TYPE_STRING),
                        'file_size': openapi.Schema(type=openapi.TYPE_INTEGER),
                        'generated_at': openapi.Schema(type=openapi.TYPE_STRING),
                        'error_message': openapi.Schema(type=openapi.TYPE_STRING),
                    }
                )
            ),
            404: "Document not found"
        }
    )
    @action(detail=True, methods=['get'], url_path='pdf-status')
    def pdf_status(self, request, pk=None):
        """
        Check the status of PDF generation for an announcement.
        
        Returns information about the PDF document including generation status.
        """
        logger.info(
            f"User {request.user.id} checking PDF status for announcement {pk}"
        )
        
        announcement = self.get_object()
        
        from documents import services as doc_services
        document = doc_services.get_announcement_document(
            announcement_id=announcement.id
        )
        
        if not document:
            return Response(
                {
                    'status': 'not_found',
                    'message': 'No PDF document found for this announcement'
                },
                status=status.HTTP_404_NOT_FOUND
            )
        
        return Response({
            'status': document.status,
            'document_id': str(document.id),
            'file_size': document.file_size,
            'generated_at': document.generated_at,
            'error_message': document.error_message if document.error_message else None,
            'is_ready': document.status == 'completed' and bool(document.file),
        })