# reports/views.py
"""
API views for reports app.

Thin layer that handles HTTP concerns and delegates to service layer.
"""

import logging
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

from . import services
from . import serializers
from .permissions import IsLandlordOrOwner

logger = logging.getLogger(__name__)


class ReportsViewSet(viewsets.ViewSet):
    """
    ViewSet for generating payment reports.
    
    Provides endpoints for:
    - Fee-specific payment status (who paid, who didn't)
    - Overall payment summary across all fees
    - Estate-specific payment summary
    """
    
    permission_classes = [IsAuthenticated, IsLandlordOrOwner]
    
    @swagger_auto_schema(
        operation_description="Get payment status report for a specific fee",
        responses={
            200: serializers.FeePaymentStatusSerializer(),
            400: "Bad request - invalid fee ID",
            403: "Forbidden - not the fee owner",
            404: "Fee not found"
        },
        manual_parameters=[
            openapi.Parameter(
                'fee_id',
                openapi.IN_PATH,
                description="UUID of the fee",
                type=openapi.TYPE_STRING,
                required=True
            )
        ]
    )
    @action(detail=False, methods=['get'], url_path='fee/(?P<fee_id>[^/.]+)')
    def fee_payment_status(self, request, fee_id=None):
        """
        Get payment status for a specific fee.
        
        Returns total collected amount and list of units that haven't paid.
        """
        logger.info(f"Fee payment status requested by user {request.user.id} for fee {fee_id}")
        
        try:
            report_data = services.get_fee_payment_status(
                fee_id=fee_id,
                user=request.user
            )
            serializer = serializers.FeePaymentStatusSerializer(report_data)
            
            logger.info(f"Fee payment status report generated successfully for fee {fee_id}")
            return Response(serializer.data, status=status.HTTP_200_OK)
            
        except ValueError as e:
            logger.warning(f"ValueError in fee payment status: {str(e)}")
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            logger.error(f"Unexpected error in fee payment status: {str(e)}", exc_info=True)
            return Response(
                {'error': 'An error occurred while generating the report'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @swagger_auto_schema(
        operation_description="Get overall payment summary across all fees",
        responses={
            200: serializers.OverallPaymentSummarySerializer(),
            400: "Bad request",
            403: "Forbidden - not a landlord/owner"
        },
        manual_parameters=[
            openapi.Parameter(
                'estate_id',
                openapi.IN_QUERY,
                description="Optional: Filter by estate UUID",
                type=openapi.TYPE_STRING,
                required=False
            )
        ]
    )
    @action(detail=False, methods=['get'], url_path='overall-summary')
    def overall_summary(self, request):
        """
        Get overall payment summary across all fees.
        
        Optionally filter by estate_id query parameter.
        """
        estate_id = request.query_params.get('estate_id', None)
        
        logger.info(
            f"Overall payment summary requested by user {request.user.id}, "
            f"estate_id={estate_id}"
        )
        
        try:
            report_data = services.get_overall_payment_summary(
                user=request.user,
                estate_id=estate_id
            )
            serializer = serializers.OverallPaymentSummarySerializer(report_data)
            
            logger.info("Overall payment summary generated successfully")
            return Response(serializer.data, status=status.HTTP_200_OK)
            
        except ValueError as e:
            logger.warning(f"ValueError in overall summary: {str(e)}")
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            logger.error(f"Unexpected error in overall summary: {str(e)}", exc_info=True)
            return Response(
                {'error': 'An error occurred while generating the report'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @swagger_auto_schema(
        operation_description="Get payment summary for a specific estate",
        responses={
            200: serializers.OverallPaymentSummarySerializer(),
            400: "Bad request - invalid estate ID",
            403: "Forbidden - not the estate owner",
            404: "Estate not found"
        },
        manual_parameters=[
            openapi.Parameter(
                'estate_id',
                openapi.IN_PATH,
                description="UUID of the estate",
                type=openapi.TYPE_STRING,
                required=True
            )
        ]
    )
    @action(detail=False, methods=['get'], url_path='estate/(?P<estate_id>[^/.]+)')
    def estate_summary(self, request, estate_id=None):
        """
        Get payment summary for a specific estate.
        
        Returns aggregated payment data for all fees in the estate.
        """
        logger.info(
            f"Estate payment summary requested by user {request.user.id} "
            f"for estate {estate_id}"
        )
        
        try:
            report_data = services.get_estate_payment_summary(
                estate_id=estate_id,
                user=request.user
            )
            serializer = serializers.OverallPaymentSummarySerializer(report_data)
            
            logger.info(f"Estate payment summary generated successfully for estate {estate_id}")
            return Response(serializer.data, status=status.HTTP_200_OK)
            
        except ValueError as e:
            logger.warning(f"ValueError in estate summary: {str(e)}")
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            logger.error(f"Unexpected error in estate summary: {str(e)}", exc_info=True)
            return Response(
                {'error': 'An error occurred while generating the report'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )