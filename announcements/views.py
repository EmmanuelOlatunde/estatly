# announcements/views.py

"""
API views for announcements app.

Provides RESTful endpoints for announcement operations.
"""

import logging
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import  OrderingFilter
from django.http import HttpResponse
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from .filters import AnnouncementFilter 
from django.db.models import Q


from .models import Announcement
from .serializers import (
    AnnouncementSerializer,
    AnnouncementCreateSerializer,
    AnnouncementUpdateSerializer,
)
from .permissions import IsManagerOrReadOnly, IsOwnerOrReadOnly, IsActiveUser
from . import services

logger = logging.getLogger(__name__)


class AnnouncementViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing announcements.
    
    Provides CRUD operations for announcements:
    - list: Get all announcements visible to the user
    - retrieve: Get a specific announcement
    - create: Create a new announcement (managers only)
    - update: Update an announcement (owner only)
    - partial_update: Partially update an announcement (owner only)
    - destroy: Delete an announcement (owner only)
    
    Additional actions:
    - print: Get a printable version of an announcement
    """
    
    permission_classes = [IsAuthenticated, IsOwnerOrReadOnly, IsActiveUser]
    filter_backends = [DjangoFilterBackend,  OrderingFilter]
    filterset_class = AnnouncementFilter
    # search_fields = ['title', 'message']
    ordering_fields = ['created_at', 'updated_at', 'title']
    ordering = ['-created_at']


    def get_queryset(self):
        if getattr(self, 'swagger_fake_view', False):
            return Announcement.objects.none()

        user = self.request.user
        queryset = Announcement.objects.all()

        # 🔑 Actions that MUST see the object
        if self.action in [
            'update',
            'partial_update',
            'destroy',
            'print_announcement',
        ]:
            return queryset

        # 🔑 Retrieve logic
        if self.action == 'retrieve':
            return queryset.filter(
                Q(is_active=True) | Q(created_by=user)
            )

    #    # LIST behavior
    #     if user.is_estate_manager:
    #         # Managers see ALL announcements (active + inactive)
    #         return queryset

        # # Regular users see only active announcements
        # return queryset.filter(is_active=True)
        # 📃 LIST behavior (query-aware)
        include_inactive = self.request.query_params.get('include_inactive')
        is_active_param = self.request.query_params.get('is_active')

        # Explicit include inactive → start with all
        if include_inactive == 'true':
            qs = queryset
        else:
            qs = queryset.filter(is_active=True)

        # Explicit is_active filter overrides
        if is_active_param == 'true':
            qs = qs.filter(is_active=True)
        elif is_active_param == 'false':
            qs = qs.filter(is_active=False)

        return qs




    def get_serializer_class(self):
        """
        Return appropriate serializer class based on action.
        
        Returns:
            Serializer class for the current action
        """
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
        operation_description="Create a new announcement (managers only)",
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
        """
        Create announcement using service layer.
        
        Args:
            serializer: Validated serializer instance
        """
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
        """
        Update announcement using service layer.
        
        Args:
            serializer: Validated serializer instance
        """
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
        """
        Delete announcement using service layer.
        
        Args:
            instance: Announcement instance to delete
        """
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
        operation_description="Get a printable version of an announcement",
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
        Get a printable version of an announcement.
        
        Returns an HTML page optimized for printing.
        
        Args:
            request: HTTP request
            pk: Announcement primary key
        
        Returns:
            HttpResponse with HTML content
        """
        logger.info(
            f"User {request.user.id} requesting print version of announcement {pk}"
        )
        
        announcement = self.get_object()
        
        # Simple HTML template for printing
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


        