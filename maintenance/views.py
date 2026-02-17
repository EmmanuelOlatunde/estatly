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

from estates.models import Estate
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


def _get_user_estate(user):
    """
    Return the Estate for the given user via reverse OneToOne, or None.

    Centralised here so get_queryset and any other callers have one safe
    access point. Returns None (not an exception) so callers can degrade
    gracefully (e.g. return queryset.none()) rather than raising a 500.
    """
    try:
        return user.estate
    except Estate.DoesNotExist:
        return None


class MaintenanceTicketPagination(PageNumberPagination):
    page_size = 10
    page_size_query_param = 'page_size'
    max_page_size = 100


class MaintenanceTicketViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing maintenance tickets.

    Users can only access tickets from the estate they manage.

    Custom actions:
    - resolve:    Mark a ticket as resolved
    - reopen:     Reopen a resolved ticket
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
        if self.action == 'list':
            return MaintenanceTicketListSerializer
        elif self.action == 'create':
            return MaintenanceTicketCreateSerializer
        elif self.action in ['update', 'partial_update']:
            return MaintenanceTicketUpdateSerializer
        return MaintenanceTicketSerializer

    def get_permissions(self):
        if self.action == 'create':
            return [IsAuthenticated(), CanCreateTicket()]
        elif self.action == 'statistics':
            return [IsAuthenticated(), CanAccessEstate()]
        elif self.action == 'list':
            return [IsAuthenticated()]
        elif self.action == 'retrieve':
            return [IsAuthenticated(), IsTicketCreatorOrAdmin()]
        return [IsAuthenticated(), IsTicketCreatorOrAdmin()]

    def get_queryset(self):
        """
        Filter queryset to tickets from the user's estate only.

        Superusers see all tickets.
        Estate managers see only their estate's tickets.
        Users with no estate assigned get an empty queryset — never a 500.
        """
        if getattr(self, 'swagger_fake_view', False):
            return MaintenanceTicket.objects.none()

        user = self.request.user

        if not user.is_authenticated:
            return MaintenanceTicket.objects.none()

        queryset = (
            super()
            .get_queryset()
            .select_related('created_by', 'unit', 'estate')
        )

        if user.is_superuser:
            logger.info(f"Superuser {user.id} accessing all tickets")
            return queryset

        estate = _get_user_estate(user)
        if not estate:
            logger.warning(
                f"User {user.id} has no estate assigned, returning empty queryset"
            )
            return MaintenanceTicket.objects.none()

        queryset = queryset.filter(estate=estate)
        logger.info(
            f"Filtering tickets for user {user.id} to estate {estate.id}. "
            f"Found {queryset.count()} tickets."
        )
        return queryset

    @swagger_auto_schema(
        operation_description="Create a new maintenance ticket",
        request_body=MaintenanceTicketCreateSerializer,
        responses={201: MaintenanceTicketSerializer, 400: 'Bad Request'},
    )
    def create(self, request: Request, *args, **kwargs) -> Response:
        """Create a new maintenance ticket for the user's estate."""
        logger.info(f"Creating maintenance ticket by user {request.user.id}")

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        validated_data = serializer.validated_data
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
            return Response(output_serializer.data, status=status.HTTP_201_CREATED)

        except ValueError as e:
            logger.error(f"Error creating ticket: {e}")
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

    @swagger_auto_schema(
        operation_description="Update a maintenance ticket",
        request_body=MaintenanceTicketUpdateSerializer,
        responses={200: MaintenanceTicketSerializer, 400: 'Bad Request', 404: 'Not Found'},
    )
    def update(self, request: Request, *args, **kwargs) -> Response:
        """Update an existing maintenance ticket."""
        partial = kwargs.pop('partial', False)
        instance = self.get_object()

        logger.info(f"Updating ticket {instance.id} by user {request.user.id}")

        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)

        validated_data = serializer.validated_data
        unit = validated_data.pop("unit", None)

        try:
            ticket = services.update_maintenance_ticket(
                ticket=instance,
                user=request.user,
                title=validated_data.get("title", instance.title),
                description=validated_data.get("description", instance.description),
                category=validated_data.get("category", instance.category),
                unit_id=str(unit.id) if unit else None,
                status=validated_data.get("status", instance.status),
            )
            output_serializer = MaintenanceTicketSerializer(ticket)
            return Response(output_serializer.data)

        except ValueError as e:
            logger.error(f"Error updating ticket: {e}")
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

    @swagger_auto_schema(
        operation_description="Delete a maintenance ticket",
        responses={204: 'No Content', 404: 'Not Found'},
    )
    def destroy(self, request: Request, *args, **kwargs) -> Response:
        """Delete a maintenance ticket."""
        instance = self.get_object()
        logger.info(f"Deleting ticket {instance.id} by user {request.user.id}")
        services.delete_maintenance_ticket(ticket=instance, user=request.user)
        return Response(status=status.HTTP_204_NO_CONTENT)

    @swagger_auto_schema(
        method='post',
        operation_description="Mark a ticket as resolved",
        responses={200: MaintenanceTicketSerializer, 400: 'Already resolved', 404: 'Not Found'},
    )
    @action(detail=True, methods=['post'])
    def resolve(self, request: Request, pk=None) -> Response:
        """Mark a maintenance ticket as resolved."""
        ticket = self.get_object()
        logger.info(f"Resolving ticket {ticket.id} by user {request.user.id}")

        try:
            resolved_ticket = services.resolve_maintenance_ticket(
                ticket=ticket, user=request.user
            )
            return Response(MaintenanceTicketSerializer(resolved_ticket).data)
        except ValueError as e:
            logger.error(f"Error resolving ticket: {e}")
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

    @swagger_auto_schema(
        method='post',
        operation_description="Reopen a resolved ticket",
        responses={200: MaintenanceTicketSerializer, 400: 'Not resolved', 404: 'Not Found'},
    )
    @action(detail=True, methods=['post'])
    def reopen(self, request: Request, pk=None) -> Response:
        """Reopen a resolved maintenance ticket."""
        ticket = self.get_object()
        logger.info(f"Reopening ticket {ticket.id} by user {request.user.id}")

        try:
            reopened_ticket = services.reopen_maintenance_ticket(
                ticket=ticket, user=request.user
            )
            return Response(MaintenanceTicketSerializer(reopened_ticket).data)
        except ValueError as e:
            logger.error(f"Error reopening ticket: {e}")
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

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
                            "Water": 15, "Electricity": 10,
                            "Security": 8, "Waste": 12, "Other": 5,
                        },
                    }
                },
            ),
            400: 'Bad Request',
        },
    )
    @action(detail=False, methods=['get'], filter_backends=[])
    def statistics(self, request: Request) -> Response:
        """
        Get ticket statistics for an estate.

        Super admins can pass any estate_id.
        Managers must pass their own estate_id (enforced by CanAccessEstate).
        """
        estate_id = request.query_params.get('estate_id')
        if not estate_id:
            return Response(
                {'error': 'estate_id query parameter is required'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        logger.info(
            f"Fetching ticket statistics for estate {estate_id} "
            f"by user {request.user.id}"
        )
        stats = services.get_ticket_statistics(
            estate_id=estate_id, user=request.user
        )
        return Response(stats)