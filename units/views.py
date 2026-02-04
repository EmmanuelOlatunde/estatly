"""
Views for the units app.

Provides REST API endpoints for unit management.
"""

from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.filters import SearchFilter, OrderingFilter
from django_filters.rest_framework import DjangoFilterBackend
from drf_yasg.utils import swagger_auto_schema
from estates.models import Estate

from .models import Unit
from .serializers import (
    UnitSerializer,
    UnitListSerializer,
    UnitCreateSerializer,
    UnitUpdateSerializer,
    UnitOccupancySerializer,
)
from .permissions import IsOwner
from .filters import UnitFilter
from . import services


class UnitViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing property units.
    
    Provides CRUD operations and custom actions for unit management.
    Only owners can access and manage their own units.
    
    list: Get all units owned by the authenticated user
    create: Create a new unit
    retrieve: Get details of a specific unit
    update: Update a unit (full update)
    partial_update: Partially update a unit
    destroy: Delete a unit
    
    Custom actions:
    - occupied: Get all occupied units
    - vacant: Get all vacant units
    - deactivate: Deactivate a unit
    - activate: Activate a unit
    - update_occupancy: Update occupancy status and information
    """
    
    permission_classes = [IsAuthenticated, IsOwner]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_class = UnitFilter
    search_fields = ['identifier', 'occupant_name', 'description']
    ordering_fields = ['identifier', 'created_at', 'updated_at', 'is_occupied']
    ordering = ['identifier']
    
    @swagger_auto_schema(
        operation_description="List units",
        responses={200: UnitListSerializer(many=True)},
    )
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)
    
    @swagger_auto_schema(
        operation_description="Retrieve a unit",
        responses={200: UnitSerializer},
    )
    def retrieve(self, request, *args, **kwargs):
        return super().retrieve(request, *args, **kwargs)
    
    
    def get_queryset(self):
        """
        Filter queryset to only include units owned by the current user.
        
        For most actions, only active units are returned.
        For the 'activate' action, inactive units are included so they can be activated.
        """
        if getattr(self, 'swagger_fake_view', False):
            return Unit.objects.none()
        
        # Actions that need to see inactive units
        actions_needing_inactive = ['activate']
        
        include_inactive = (
            self.action in actions_needing_inactive or
            self.request.query_params.get('include_inactive', 'false').lower() == 'true'
        )
        
        return services.get_user_units(
            user=self.request.user,
            include_inactive=include_inactive
        )
        
    def get_serializer_class(self):
        """
        Return appropriate serializer class based on action.
        
        Returns:
            Serializer class for the current action
        """
        if self.action == 'list':
            return UnitListSerializer
        elif self.action == 'create':
            return UnitCreateSerializer
        elif self.action in ['update', 'partial_update']:
            return UnitUpdateSerializer
        elif self.action == 'update_occupancy':
            return UnitOccupancySerializer
        return UnitSerializer
    
    @swagger_auto_schema(
        operation_description="Create a new unit",
        request_body=UnitCreateSerializer,
        responses={201: UnitSerializer},
    )

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            estate = Estate.objects.get(
                id=serializer.validated_data["estate"]
            )

            unit = services.create_unit(
                owner=request.user,
                estate=estate,
                identifier=serializer.validated_data["identifier"],
                unit_type=serializer.validated_data["unit_type"],
                occupant_name=serializer.validated_data.get("occupant_name"),
                occupant_phone=serializer.validated_data.get("occupant_phone"),
                description=serializer.validated_data.get("description"),
                is_occupied=serializer.validated_data.get("is_occupied", False),
                is_active=serializer.validated_data.get("is_active", True),
            )

            return Response(
                UnitSerializer(unit).data,
                status=status.HTTP_201_CREATED
            )

        except Estate.DoesNotExist:
            return Response(
                {"estate": "Invalid estate ID."},
                status=status.HTTP_400_BAD_REQUEST
            )

        
    @swagger_auto_schema(
        operation_description="Update a unit",
        request_body=UnitUpdateSerializer,
        responses={200: UnitSerializer},
    )
    def update(self, request, *args, **kwargs):
        """Update a unit (full update)."""
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        
        try:
            unit = services.update_unit(
                unit=instance,
                user=request.user,
                **serializer.validated_data
            )
            output_serializer = UnitSerializer(unit)
            return Response(output_serializer.data)
        except ValueError as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
    
    @swagger_auto_schema(
        operation_description="Partially update a unit",
        request_body=UnitUpdateSerializer,
        responses={200: UnitSerializer},
    )
    def partial_update(self, request, *args, **kwargs):
        """Update a unit (partial update)."""
        kwargs['partial'] = True
        return self.update(request, *args, **kwargs)
    
    @swagger_auto_schema(
        operation_description="Delete a unit",
        responses={204: 'Unit deleted successfully'},
    )
    def destroy(self, request, *args, **kwargs):
        """Delete a unit."""
        instance = self.get_object()
        
        try:
            services.delete_unit(unit=instance, user=request.user)
            return Response(status=status.HTTP_204_NO_CONTENT)
        except ValueError as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
    
    @swagger_auto_schema(
        method='get',
        operation_description="Get all occupied units",
        responses={200: UnitListSerializer(many=True)},
    )
    @action(detail=False, methods=['get'])
    def occupied(self, request):
        """
        Get all occupied units owned by the authenticated user.
        
        Returns only units where is_occupied=True and is_active=True.
        """
        queryset = services.get_occupied_units(user=request.user)
        serializer = UnitListSerializer(queryset, many=True)
        return Response(serializer.data)
    
    @swagger_auto_schema(
        method='get',
        operation_description="Get all vacant units",
        responses={200: UnitListSerializer(many=True)},
    )
    @action(detail=False, methods=['get'])
    def vacant(self, request):
        """
        Get all vacant (unoccupied) units owned by the authenticated user.
        
        Returns only units where is_occupied=False and is_active=True.
        """
        queryset = services.get_vacant_units(user=request.user)
        serializer = UnitListSerializer(queryset, many=True)
        return Response(serializer.data)
    
    @swagger_auto_schema(
        method='post',
        operation_description="Deactivate a unit",
        responses={200: UnitSerializer},
    )
    @action(detail=True, methods=['post'])
    def deactivate(self, request, pk=None):
        """
        Deactivate a unit (soft delete).
        
        Sets is_active=False without deleting the unit from the database.
        """
        instance = self.get_object()
        
        try:
            unit = services.deactivate_unit(unit=instance, user=request.user)
            serializer = UnitSerializer(unit)
            return Response(serializer.data)
        except ValueError as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
        
    @swagger_auto_schema(
        method='post',
        operation_description="Activate a unit",
        responses={200: UnitSerializer},
    )
    @action(detail=True, methods=['post'])
    def activate(self, request, pk=None):
        """
        Activate a previously deactivated unit.
        
        Sets is_active=True.
        """
        instance = self.get_object()
        
        try:
            unit = services.activate_unit(unit=instance, user=request.user)
            serializer = UnitSerializer(unit)
            return Response(serializer.data)
        except PermissionError as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_403_FORBIDDEN
            )
        except ValueError as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )

    @swagger_auto_schema(
        method='patch',
        operation_description="Update occupancy status",
        request_body=UnitOccupancySerializer,
        responses={200: UnitSerializer},
    )

    @action(detail=True, methods=['patch'])
    def update_occupancy(self, request, pk=None):
        """
        Update occupancy status and occupant information.
        
        Specialized endpoint for quickly updating occupancy-related fields.
        If marking as unoccupied, occupant information will be cleared automatically.
        """
        instance = self.get_object()
        serializer = UnitOccupancySerializer(instance, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        
        try:
            unit = services.update_occupancy(
                unit=instance,
                user=request.user,
                **serializer.validated_data
            )
            output_serializer = UnitSerializer(unit)
            return Response(output_serializer.data)
        except PermissionError as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_403_FORBIDDEN
            )
        except ValueError as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )