# payments/views.py

"""
API views for the payments app.

Provides REST API endpoints for fees, payments, and receipts.
"""

from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter

from .models import Fee, FeeAssignment, Payment, Receipt
from .serializers import (
    FeeSerializer,
    FeeCreateSerializer,
    FeeDetailSerializer,
    FeeAssignmentSerializer,
    PaymentSerializer,
    PaymentCreateSerializer,
    ReceiptSerializer,
)
from .permissions import (
    EstateAccessPermission,
    CanRecordPayment,
    CanViewReceipt,
    IsEstateManager,
)
from .filters import FeeFilter, FeeAssignmentFilter, PaymentFilter
from . import services


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
        """Return appropriate serializer based on action."""
        if self.action in ['create', 'update', 'partial_update']:
            return FeeCreateSerializer
        elif self.action == 'retrieve':
            return FeeDetailSerializer
        return FeeSerializer
    
    def get_queryset(self):
        """Filter fees to only those in the user's estate."""
        queryset = super().get_queryset()
        user = self.request.user
        user_estate = self._get_user_estate(user)
        
        if not user_estate:
            return queryset.none()
        
        return queryset.filter(estate_id=user_estate.id)
    
    def perform_create(self, serializer):
        """Create fee with assignments using service layer."""
        validated_data = serializer.validated_data
        
        fee = services.create_fee(
            name=validated_data['name'],
            description=validated_data.get('description', ''),
            amount=validated_data['amount'],
            due_date=validated_data['due_date'],
            estate_id=validated_data['estate'].id,
            created_by=self.request.user,
            assign_to_all_units=validated_data.get('assign_to_all_units', False),
            unit_ids=validated_data.get('unit_ids', [])
        )
        
        serializer.instance = fee
    
    @action(detail=True, methods=['get'])
    def payment_summary(self, request, pk=None):
        """
        Get payment summary statistics for a fee.
        
        Returns counts and revenue figures for the fee.
        """
        fee = self.get_object()
        summary = services.get_fee_payment_summary(fee=fee)
        return Response(summary)
    
    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated, IsEstateManager])
    def assign_to_units(self, request, pk=None):
        """
        Assign this fee to additional units.
        
        Expects JSON body with 'unit_ids' array.
        """
        fee = self.get_object()
        unit_ids = request.data.get('unit_ids', [])
        
        if not unit_ids:
            return Response(
                {'error': 'unit_ids is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            assignments = services.assign_fee_to_units(
                fee=fee,
                unit_ids=unit_ids
            )
            serializer = FeeAssignmentSerializer(assignments, many=True)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
    
    def _get_user_estate(self, user):
        """Get the estate a user belongs to."""
        if hasattr(user, 'estate'):
            return user.estate
        
        if hasattr(user, 'profile') and hasattr(user.profile, 'estate'):
            return user.profile.estate
        
        return None


class FeeAssignmentViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for viewing fee assignments.
    
    Fee assignments are automatically created when fees are assigned to units.
    This viewset provides read-only access to track payment status per unit.
    """
    
    queryset = FeeAssignment.objects.select_related(
        'fee',
        'fee__estate',
        'unit'
    )
    serializer_class = FeeAssignmentSerializer
    permission_classes = [IsAuthenticated, EstateAccessPermission]
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_class = FeeAssignmentFilter
    ordering_fields = ['created_at', 'status']
    ordering = ['-created_at']
    
    def get_queryset(self):
        """Filter assignments to only those in the user's estate."""
        queryset = super().get_queryset()
        user = self.request.user
        user_estate = self._get_user_estate(user)
        
        if not user_estate:
            return queryset.none()
        
        return queryset.filter(fee__estate_id=user_estate.id)
    
    def _get_user_estate(self, user):
        """Get the estate a user belongs to."""
        if hasattr(user, 'estate'):
            return user.estate
        
        if hasattr(user, 'profile') and hasattr(user.profile, 'estate'):
            return user.profile.estate
        
        return None


class PaymentViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing payments.
    
    Provides endpoints to record payments and view payment history.
    """
    
    queryset = Payment.objects.select_related(
        'fee_assignment',
        'fee_assignment__fee',
        'fee_assignment__unit',
        'recorded_by'
    )
    permission_classes = [IsAuthenticated, CanRecordPayment, EstateAccessPermission]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_class = PaymentFilter
    search_fields = ['reference_number', 'fee_assignment__fee__name']
    ordering_fields = ['payment_date', 'created_at', 'amount']
    ordering = ['-payment_date']
    http_method_names = ['get', 'post', 'head', 'options']
    
    def get_serializer_class(self):
        """Return appropriate serializer based on action."""
        if self.action == 'create':
            return PaymentCreateSerializer
        return PaymentSerializer
    
    def get_queryset(self):
        """Filter payments to only those in the user's estate."""
        queryset = super().get_queryset()
        user = self.request.user
        user_estate = self._get_user_estate(user)
        
        if not user_estate:
            return queryset.none()
        
        return queryset.filter(fee_assignment__fee__estate_id=user_estate.id)
    
    def create(self, request, *args, **kwargs):
        # Validate input
        serializer = PaymentCreateSerializer(
            data=request.data,
            context=self.get_serializer_context()
        )
        serializer.is_valid(raise_exception=True)

        # Create payment via service layer
        payment = services.mark_fee_as_paid(
            fee_assignment=serializer.validated_data['fee_assignment'],
            amount=serializer.validated_data['amount'],
            payment_method=serializer.validated_data['payment_method'],
            payment_date=serializer.validated_data.get('payment_date'),
            reference_number=serializer.validated_data.get('reference_number', ''),
            notes=serializer.validated_data.get('notes', ''),
            recorded_by=request.user,
        )

        # 🔥 SERIALIZE RESPONSE WITH FULL SERIALIZER
        response_serializer = PaymentSerializer(
            payment,
            context=self.get_serializer_context()
        )

        return Response(
            response_serializer.data,
            status=status.HTTP_201_CREATED
        )


    def _get_user_estate(self, user):
        """Get the estate a user belongs to."""
        if hasattr(user, 'estate'):
            return user.estate
        
        if hasattr(user, 'profile') and hasattr(user.profile, 'estate'):
            return user.profile.estate
        
        return None


class ReceiptViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for viewing receipts.
    
    Receipts are automatically generated when payments are recorded.
    This viewset provides read-only access to view and download receipts.
    """
    
    queryset = Receipt.objects.select_related('payment', 'payment__fee_assignment')
    serializer_class = ReceiptSerializer
    permission_classes = [IsAuthenticated, CanViewReceipt, EstateAccessPermission]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    search_fields = ['receipt_number', 'fee_name', 'unit_identifier']
    ordering_fields = ['issued_at', 'payment_date']
    ordering = ['-issued_at']
    
    def get_queryset(self):
        """Filter receipts to only those in the user's estate."""
        queryset = super().get_queryset()
        user = self.request.user
        user_estate = self._get_user_estate(user)
        
        if not user_estate:
            return queryset.none()
        
        return queryset.filter(
            payment__fee_assignment__fee__estate_id=user_estate.id
        )
    
    @action(detail=True, methods=['get'])
    def download(self, request, pk=None):
        """
        Download receipt as PDF.
        
        This is a placeholder - implement PDF generation as needed.
        """
        receipt = self.get_object()
        
        return Response({
            'message': 'PDF generation not yet implemented',
            'receipt_number': receipt.receipt_number,
            'receipt_id': str(receipt.id)
        })
    
    def _get_user_estate(self, user):
        """Get the estate a user belongs to."""
        if hasattr(user, 'estate'):
            return user.estate
        
        if hasattr(user, 'profile') and hasattr(user.profile, 'estate'):
            return user.profile.estate
        
        return None