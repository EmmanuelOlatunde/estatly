# payments/views.py
"""
API views for the payments app.

Provides REST API endpoints for fees, payments, and receipts.
"""

import logging
from django.http import FileResponse
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.filters import SearchFilter, OrderingFilter
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .filters import FeeFilter, FeeAssignmentFilter, PaymentFilter, ReceiptFilter
from .models import Fee, FeeAssignment, Payment, Receipt
from .permissions import (
    EstateAccessPermission,
    CanRecordPayment,
    CanViewReceipt,
    IsEstateManager,
)
from .serializers import (
    FeeSerializer,
    FeeCreateSerializer,
    FeeDetailSerializer,
    FeeAssignmentSerializer,
    PaymentSerializer,
    PaymentCreateSerializer,
    ReceiptSerializer,
)
from . import services
from estates.models import Estate

logger = logging.getLogger(__name__)


def _get_user_estate(user):
    """
    Return the Estate for the given user via reverse OneToOne.

    Replaces the four duplicated _get_user_estate methods that were
    spread across each ViewSet, and removes the dead 'user.profile'
    fallback that belongs to a different architecture.

    Returns the Estate instance, or None if no estate is assigned.
    None is used (not an exception) so callers can return queryset.none()
    gracefully rather than raising a 500.
    """
    try:
        return user.estate
    except Estate.DoesNotExist:
        return None


class FeeViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing fees.

    Provides CRUD operations for fees and additional actions for
    payment summaries and bulk operations.
    """

    queryset = Fee.objects.select_related('estate', 'created_by')
    permission_classes = [IsAuthenticated, IsEstateManager, EstateAccessPermission]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_class = FeeFilter
    search_fields = ['name', 'description']
    ordering_fields = ['created_at', 'due_date', 'amount']
    ordering = ['-created_at']

    def get_serializer_class(self):
        if self.action in ['create', 'update', 'partial_update']:
            return FeeCreateSerializer
        elif self.action == 'retrieve':
            return FeeDetailSerializer
        return FeeSerializer

    def get_queryset(self):
        queryset = super().get_queryset()
        estate = _get_user_estate(self.request.user)
        if not estate:
            return queryset.none()
        return queryset.filter(estate_id=estate.id)

    def perform_create(self, serializer):
        validated_data = serializer.validated_data
        fee = services.create_fee(
            name=validated_data['name'],
            description=validated_data.get('description', ''),
            amount=validated_data['amount'],
            due_date=validated_data['due_date'],
            estate_id=validated_data['estate'].id,
            created_by=self.request.user,
            assign_to_all_units=validated_data.get('assign_to_all_units', False),
            unit_ids=validated_data.get('unit_ids', []),
        )
        serializer.instance = fee

    @action(detail=True, methods=['get'])
    def payment_summary(self, request, pk=None):
        """Get payment summary statistics for a fee."""
        fee = self.get_object()
        summary = services.get_fee_payment_summary(fee=fee)
        return Response(summary)

    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated, IsEstateManager])
    def assign_to_units(self, request, pk=None):
        """Assign this fee to additional units. Expects {'unit_ids': [...]}."""
        fee = self.get_object()
        unit_ids = request.data.get('unit_ids', [])

        if not unit_ids:
            return Response(
                {'error': 'unit_ids is required'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            assignments = services.assign_fee_to_units(fee=fee, unit_ids=unit_ids)
            serializer = FeeAssignmentSerializer(assignments, many=True)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)


class FeeAssignmentViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Read-only ViewSet for fee assignments.

    Fee assignments are created automatically when fees are assigned to units.
    """

    queryset = FeeAssignment.objects.select_related('fee', 'fee__estate', 'unit')
    serializer_class = FeeAssignmentSerializer
    permission_classes = [IsAuthenticated, EstateAccessPermission]
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_class = FeeAssignmentFilter
    ordering_fields = ['created_at', 'status']
    ordering = ['-created_at']

    def get_queryset(self):
        queryset = super().get_queryset()
        estate = _get_user_estate(self.request.user)
        if not estate:
            return queryset.none()
        return queryset.filter(fee__estate_id=estate.id)


class PaymentViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing payments.

    Provides endpoints to record payments and view payment history.
    Payments are immutable once created — no PUT/PATCH/DELETE.
    """

    queryset = Payment.objects.select_related(
        'fee_assignment',
        'fee_assignment__fee',
        'fee_assignment__unit',
        'recorded_by',
    )
    permission_classes = [IsAuthenticated, CanRecordPayment, EstateAccessPermission]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_class = PaymentFilter
    search_fields = ['reference_number', 'fee_assignment__fee__name']
    ordering_fields = ['payment_date', 'created_at', 'amount']
    ordering = ['-payment_date']
    http_method_names = ['get', 'post', 'head', 'options']

    def get_serializer_class(self):
        if self.action == 'create':
            return PaymentCreateSerializer
        return PaymentSerializer

    def get_queryset(self):
        queryset = super().get_queryset()
        estate = _get_user_estate(self.request.user)
        if not estate:
            return queryset.none()
        return queryset.filter(fee_assignment__fee__estate_id=estate.id)

    def create(self, request, *args, **kwargs):
        serializer = PaymentCreateSerializer(
            data=request.data,
            context=self.get_serializer_context(),
        )
        serializer.is_valid(raise_exception=True)

        payment = services.mark_fee_as_paid(
            fee_assignment=serializer.validated_data['fee_assignment'],
            amount=serializer.validated_data['amount'],
            payment_method=serializer.validated_data['payment_method'],
            payment_date=serializer.validated_data.get('payment_date'),
            reference_number=serializer.validated_data.get('reference_number', ''),
            notes=serializer.validated_data.get('notes', ''),
            recorded_by=request.user,
        )

        response_serializer = PaymentSerializer(
            payment,
            context=self.get_serializer_context(),
        )
        return Response(response_serializer.data, status=status.HTTP_201_CREATED)


class ReceiptViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Read-only ViewSet for receipts.

    Receipts are generated automatically when payments are recorded.
    """

    queryset = Receipt.objects.select_related('payment', 'payment__fee_assignment')
    serializer_class = ReceiptSerializer
    permission_classes = [IsAuthenticated, CanViewReceipt, EstateAccessPermission]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_class = ReceiptFilter
    search_fields = ['receipt_number', 'fee_name', 'unit_identifier']
    ordering_fields = ['issued_at', 'payment_date']
    ordering = ['-issued_at']

    def get_queryset(self):
        queryset = super().get_queryset()
        estate = _get_user_estate(self.request.user)
        if not estate:
            return queryset.none()
        return queryset.filter(payment__fee_assignment__fee__estate_id=estate.id)

    @action(detail=True, methods=['get'])
    def download(self, request, pk=None):
        """Download receipt as PDF."""
        receipt = self.get_object()

        try:
            from documents.models import Document, DocumentType, DocumentStatus

            document = Document.objects.filter(
                document_type=DocumentType.PAYMENT_RECEIPT,
                related_payment_id=receipt.payment.id,
                is_deleted=False,
            ).first()

            if not document:
                logger.warning(
                    f"No document found for receipt {receipt.id}, "
                    f"payment {receipt.payment.id}"
                )
                return Response(
                    {
                        'error': 'Receipt PDF not found',
                        'detail': (
                            'The PDF document has not been generated yet. '
                            'Please try again in a moment.'
                        ),
                    },
                    status=status.HTTP_404_NOT_FOUND,
                )

            if document.status != DocumentStatus.COMPLETED:
                logger.warning(
                    f"Document {document.id} not ready, status={document.status}"
                )
                return Response(
                    {
                        'error': 'Receipt PDF not ready',
                        'detail': (
                            f'The PDF is currently being generated. '
                            f'Status: {document.get_status_display()}'
                        ),
                        'status': document.status,
                    },
                    status=status.HTTP_202_ACCEPTED,
                )

            if not document.file:
                logger.error(
                    f"Document {document.id} marked completed but has no file"
                )
                return Response(
                    {
                        'error': 'Receipt PDF file missing',
                        'detail': 'The PDF file is not available. Please contact support.',
                    },
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR,
                )

            try:
                response = FileResponse(
                    document.file.open('rb'),
                    content_type='application/pdf',
                )
                response['Content-Disposition'] = (
                    f'attachment; filename="receipt_{receipt.receipt_number}.pdf"'
                )
                logger.info(
                    f"Receipt PDF downloaded: {receipt.id} by user {request.user.id}"
                )
                return response

            except Exception as file_error:
                logger.error(
                    f"Error opening document file {document.id}: {file_error}"
                )
                return Response(
                    {'error': 'Failed to open PDF file', 'detail': str(file_error)},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR,
                )

        except Exception as e:
            logger.error(f"Unexpected error downloading receipt {receipt.id}: {e}")
            return Response(
                {'error': 'Download failed', 'detail': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )