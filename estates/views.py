from rest_framework import viewsets, status, serializers
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.filters import SearchFilter, OrderingFilter
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.pagination import PageNumberPagination

from .models import Estate
from .serializers import (
    EstateSerializer,
    EstateCreateSerializer,
    EstateUpdateSerializer,
    EstateListSerializer,
)
from .permissions import CanManageEstate
from .filters import EstateFilter
from . import services


class EstatePagination(PageNumberPagination):
    page_size = 10
    page_size_query_param = "page_size"
    max_page_size = 50


class EstateViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing Estate instances.
    """

    permission_classes = [IsAuthenticated, CanManageEstate]
    pagination_class = EstatePagination

    filter_backends = [
        DjangoFilterBackend,
        SearchFilter,
        OrderingFilter,
    ]
    filterset_class = EstateFilter
    search_fields = ['name', 'description', 'address']
    ordering_fields = ['name', 'created_at', 'updated_at', 'approximate_units']
    ordering = ['-created_at']

    # Serializer mapping
    serializer_action_map = {
        'list': EstateListSerializer,
        'create': EstateCreateSerializer,
        'update': EstateUpdateSerializer,
        'partial_update': EstateUpdateSerializer,
    }

    # Optimized base queryset
    queryset = Estate.objects.all()

    # -------------------------
    # Core DRF Overrides
    # -------------------------
    def get_permissions(self):
        if self.action in ['list', 'retrieve', 'statistics', 'by_type']:
            return [AllowAny()]
        return [IsAuthenticated(), CanManageEstate()]

    def get_serializer_class(self):
        return self.serializer_action_map.get(self.action, EstateSerializer)

    def get_queryset(self):
        queryset = super().get_queryset()

        # For list view: only active estates by default
        if self.action == "list" and "is_active" not in self.request.query_params:
            queryset = queryset.filter(is_active=True)

        # For retrieve view: include all estates
        return queryset


    def perform_create(self, serializer):
        # Call your service
        estate = self._handle_service_call(
            services.create_estate,
            **serializer.validated_data
        )
        # Assign to serializer.instance so DRF serializes it
        serializer.instance = estate
        return estate  # optional, but clearer


    def perform_update(self, serializer):
        serializer.instance = self._handle_service_call(
            services.update_estate,
            estate=self.get_object(),
            **serializer.validated_data
        )

    # -------------------------
    # Private Helpers (DRY)
    # -------------------------
    def _handle_service_call(self, func, **kwargs):
        """Wrap service calls and normalize errors."""
        try:
            return func(**kwargs)
        except ValueError as exc:
            raise serializers.ValidationError(str(exc))

    def _toggle_estate(self, estate, activate: bool):
        """Activate or deactivate estate."""
        if estate.is_active == activate:
            state = "active" if activate else "inactive"
            return Response(
                {'detail': f'Estate is already {state}.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        estate = services.activate_estate(estate=estate) if activate else services.deactivate_estate(estate=estate)
        serializer = self.get_serializer(estate)
        action = "activated" if activate else "deactivated"

        return Response(
            {
                'detail': f'Estate {action} successfully.',
                'estate': serializer.data
            },
            status=status.HTTP_200_OK
        )

    # -------------------------
    # Custom Actions
    # -------------------------
    @action(detail=True, methods=['post'])
    def activate(self, request, pk=None):
        return self._toggle_estate(self.get_object(), activate=True)

    @action(detail=True, methods=['post'])
    def deactivate(self, request, pk=None):
        return self._toggle_estate(self.get_object(), activate=False)

    @action(detail=False, methods=['get'])
    def statistics(self, request):
        stats = services.get_estate_statistics()
        return Response(stats, status=status.HTTP_200_OK)

    @action(detail=False, methods=['get'], url_path='by-type/(?P<estate_type>[^/.]+)')
    def by_type(self, request, estate_type=None):
        try:
            estates = services.get_estates_by_type(estate_type=estate_type.upper())
            serializer = EstateListSerializer(estates, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except ValueError as exc:
            return Response({'detail': str(exc)}, status=status.HTTP_400_BAD_REQUEST)
