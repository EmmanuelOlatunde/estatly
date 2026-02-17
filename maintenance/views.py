# maintenance/views.py

"""
API views for the maintenance app.

Defines ViewSets for maintenance ticket CRUD operations and custom actions.
"""

import logging
from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.pagination import PageNumberPagination
from django_filters.rest_framework import DjangoFilterBackend
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

from .models import MaintenanceTicket
from .serializers import (
    MaintenanceTicketSerializer,
    MaintenanceTicketCreateSerializer,
    MaintenanceTicketUpdateSerializer,
    MaintenanceTicketListSerializer,
)
from .permissions import (
    IsTicketCreatorOrAdmin,
    CanCreateTicket,
    CanAccessEstate,
)
from .filters import MaintenanceTicketFilter
from . import services

logger = logging.getLogger(__name__)


class MaintenanceTicketPagination(PageNumberPagination):
    """
    Custom pagination class for maintenance tickets.
    """
    page_size = 10
    page_size_query_param = 'page_size'
    max_page_size = 100


class MaintenanceTicketViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing maintenance tickets.
    
    Provides CRUD operations and custom actions for maintenance ticket management.
    Users can only access tickets from estates they manage.
    
    list: Get a list of maintenance tickets with filtering and search
    retrieve: Get details of a specific maintenance ticket
    create: Create a new maintenance ticket
    update: Update an existing maintenance ticket
    partial_update: Partially update an existing maintenance ticket
    destroy: Delete a maintenance ticket
    
    Custom actions:
    - resolve: Mark a ticket as resolved
    - reopen: Reopen a resolved ticket
    - statistics: Get ticket statistics for an estate
    """
    
    queryset = MaintenanceTicket.objects.all()
    permission_classes = [IsAuthenticated, IsTicketCreatorOrAdmin]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_class = MaintenanceTicketFilter
    ordering_fields = ['created_at', 'updated_at', 'status', 'category']
    ordering = ['-created_at']
    pagination_class = MaintenanceTicketPagination
    
    def get_serializer_class(self):
        """
        Return appropriate serializer based on action.
        
        Returns:
            Serializer class for the current action
        """
        if self.action == 'list':
            return MaintenanceTicketListSerializer
        elif self.action == 'create':
            return MaintenanceTicketCreateSerializer
        elif self.action in ['update', 'partial_update']:
            return MaintenanceTicketUpdateSerializer
        return MaintenanceTicketSerializer
    
    def get_permissions(self):
        """
        Return appropriate permissions based on action.
        
        Returns:
            List of permission instances
        """
        if self.action == 'create':
            return [IsAuthenticated(), CanCreateTicket()]
        elif self.action == 'statistics':
            return [IsAuthenticated(), CanAccessEstate()]
        elif self.action == 'list':
            # List action relies on get_queryset filtering by estate
            return [IsAuthenticated()]
        elif self.action == 'retrieve':
            # Retrieve needs object permission to verify estate access
            return [IsAuthenticated(), IsTicketCreatorOrAdmin()]
        # For update, partial_update, destroy, resolve, reopen
        return [IsAuthenticated(), IsTicketCreatorOrAdmin()]
        
    def get_queryset(self):
        """
        Filter queryset to only show tickets from user's estate.
        
        Only superusers can see all tickets.
        Managers (is_staff) and regular users can only see tickets from their assigned estate.
        
        Returns:
            Filtered QuerySet of MaintenanceTicket instances
        """
        if getattr(self, 'swagger_fake_view', False):
            return MaintenanceTicket.objects.none()

        user = self.request.user

        if not user.is_authenticated:
            return MaintenanceTicket.objects.none()

        queryset = super().get_queryset().select_related(
            'created_by',
            'unit',
            'estate'
        )

        # Only superusers can see all tickets (not is_staff)
        if user.is_superuser:
            logger.info(f"Superuser {user.id} accessing all tickets")
            return queryset

        # Managers (is_staff) and regular users can only see tickets from their estate
        if not user.estate:
            logger.warning(
                f"User {user.id} (is_staff={user.is_staff}) has no estate assigned, returning empty queryset"
            )
            return MaintenanceTicket.objects.none()

        queryset = queryset.filter(estate=user.estate)
        logger.info(
            f"Filtering tickets for user {user.id} (is_staff={user.is_staff}) "
            f"to estate {user.estate.id}. Found {queryset.count()} tickets."
        )

        return queryset

    @swagger_auto_schema(
        operation_description="Create a new maintenance ticket",
        request_body=MaintenanceTicketCreateSerializer,
        responses={
            201: MaintenanceTicketSerializer,
            400: 'Bad Request - Validation Error'
        }
    )
    def create(self, request: Request, *args, **kwargs) -> Response:
        """
        Create a new maintenance ticket.
        
        Users can only create tickets for their own estate.
        
        Args:
            request: The incoming request with ticket data
            
        Returns:
            Response with created ticket data
        """
        logger.info(f"Creating maintenance ticket by user {request.user.id}")
        
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        validated_data = serializer.validated_data

        # Extract estate and unit IDs for the service
        estate = validated_data.pop("estate")
        unit = validated_data.pop("unit", None)

        try:
            ticket = services.create_maintenance_ticket(
                title=validated_data["title"],
                description=validated_data["description"],
                category=validated_data["category"],
                estate_id=str(estate.id),
                unit_id=str(unit.id) if unit else None,
                created_by=request.user,
            )
            
            output_serializer = MaintenanceTicketSerializer(ticket)
            return Response(
                output_serializer.data,
                status=status.HTTP_201_CREATED
            )
            
        except ValueError as e:
            logger.error(f"Error creating ticket: {e}")
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )

    @swagger_auto_schema(
        operation_description="Update a maintenance ticket",
        request_body=MaintenanceTicketUpdateSerializer,
        responses={
            200: MaintenanceTicketSerializer,
            400: 'Bad Request - Validation Error',
            404: 'Not Found'
        }
    )
    def update(self, request: Request, *args, **kwargs) -> Response:
        """
        Update an existing maintenance ticket.
        
        Args:
            request: The incoming request with updated data
            
        Returns:
            Response with updated ticket data
        """
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        
        logger.info(
            f"Updating maintenance ticket {instance.id} by user {request.user.id}"
        )
        
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        
        validated_data = serializer.validated_data

        # Extract unit_id if present
        unit = validated_data.pop("unit", None)

        try:
            ticket = services.update_maintenance_ticket(
                ticket=instance,
                user=request.user,
                title=validated_data.get("title", instance.title),
                description=validated_data.get("description", instance.description),
                category=validated_data.get("category", instance.category),
                unit_id=str(unit.id) if unit else None,
                status=validated_data.get("status", instance.status)
            )
            
            output_serializer = MaintenanceTicketSerializer(ticket)
            return Response(output_serializer.data)
            
        except ValueError as e:
            logger.error(f"Error updating ticket: {e}")
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )

    @swagger_auto_schema(
        operation_description="Delete a maintenance ticket",
        responses={
            204: 'No Content - Successfully deleted',
            404: 'Not Found'
        }
    )
    def destroy(self, request: Request, *args, **kwargs) -> Response:
        """
        Delete a maintenance ticket.
        
        Args:
            request: The incoming request
            
        Returns:
            Response with no content
        """
        instance = self.get_object()
        
        logger.info(
            f"Deleting maintenance ticket {instance.id} by user {request.user.id}"
        )
        
        services.delete_maintenance_ticket(
            ticket=instance,
            user=request.user
        )
        
        return Response(status=status.HTTP_204_NO_CONTENT)
    
    @swagger_auto_schema(
        method='post',
        operation_description="Mark a ticket as resolved",
        responses={
            200: MaintenanceTicketSerializer,
            400: 'Bad Request - Already resolved',
            404: 'Not Found'
        }
    )
    @action(detail=True, methods=['post'])
    def resolve(self, request: Request, pk=None) -> Response:
        """
        Mark a maintenance ticket as resolved.
        
        Args:
            request: The incoming request
            pk: Primary key of the ticket
            
        Returns:
            Response with updated ticket data
        """
        ticket = self.get_object()
        
        logger.info(
            f"Resolving maintenance ticket {ticket.id} by user {request.user.id}"
        )
        
        try:
            resolved_ticket = services.resolve_maintenance_ticket(
                ticket=ticket,
                user=request.user
            )
            
            serializer = MaintenanceTicketSerializer(resolved_ticket)
            return Response(serializer.data)
            
        except ValueError as e:
            logger.error(f"Error resolving ticket: {e}")
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
    
    @swagger_auto_schema(
        method='post',
        operation_description="Reopen a resolved ticket",
        responses={
            200: MaintenanceTicketSerializer,
            400: 'Bad Request - Not resolved',
            404: 'Not Found'
        }
    )
    @action(detail=True, methods=['post'])
    def reopen(self, request: Request, pk=None) -> Response:
        """
        Reopen a resolved maintenance ticket.
        
        Args:
            request: The incoming request
            pk: Primary key of the ticket
            
        Returns:
            Response with updated ticket data
        """
        ticket = self.get_object()
        
        logger.info(
            f"Reopening maintenance ticket {ticket.id} by user {request.user.id}"
        )
        
        try:
            reopened_ticket = services.reopen_maintenance_ticket(
                ticket=ticket,
                user=request.user
            )
            
            serializer = MaintenanceTicketSerializer(reopened_ticket)
            return Response(serializer.data)
            
        except ValueError as e:
            logger.error(f"Error reopening ticket: {e}")
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
    
    @swagger_auto_schema(
        method='get',
        operation_description="Get ticket statistics for an estate",
        responses={
            200: openapi.Response(
                description="Statistics data",
                examples={
                    "application/json": {
                        "total_tickets": 50,
                        "open_tickets": 30,
                        "resolved_tickets": 20,
                        "by_category": {
                            "Water": 15,
                            "Electricity": 10,
                            "Security": 8,
                            "Waste": 12,
                            "Other": 5
                        }
                    }
                }
            ),
            400: 'Bad Request - Missing estate_id or unauthorized'
        }
    )
    @action(detail=False, methods=['get'], filter_backends=[])
    def statistics(self, request: Request) -> Response:
        """
        Get statistics for maintenance tickets in an estate.
        
        Users can only get statistics for their own estate.
        Superusers can get statistics for any estate.
        
        Args:
            request: The incoming request with estate_id query parameter
            
        Returns:
            Response with statistics data
        """
        estate_id = request.query_params.get('estate_id')
        
        if not estate_id:
            return Response(
                {'error': 'estate_id query parameter is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        logger.info(
            f"Fetching ticket statistics for estate {estate_id} "
            f"by user {request.user.id}"
        )
        
        stats = services.get_ticket_statistics(
            estate_id=estate_id,
            user=request.user
        )
        
        return Response(stats)