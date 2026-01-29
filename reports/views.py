# reports/views.py
import logging
import uuid
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from . import services
from .permissions import CanAccessReports

logger = logging.getLogger(__name__)


class ReportsViewSet(viewsets.ViewSet):
    """
    ViewSet for report endpoints.
    
    Provides custom actions for different report types.
    """
    permission_classes = [IsAuthenticated, CanAccessReports]
    
    @action(detail=False, methods=['get'], url_path='fee/(?P<fee_id>[^/.]+)')
    def fee_payment_status(self, request, fee_id=None):
        """
        Get payment status report for a specific fee.
        
        Returns:
            - 200: Report data
            - 400: Invalid request or permission denied
            - 404: Invalid UUID format
            - 500: Server error
        """
        # Validate UUID format first
        try:
            uuid.UUID(fee_id)
        except (ValueError, AttributeError):
            logger.warning(f"Invalid UUID format for fee_id: {fee_id}")
            return Response(
                {'error': 'Invalid fee ID format'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        try:
            report_data = services.get_fee_payment_status(
                user=request.user,
                fee_id=fee_id
            )
            
            logger.info(
                f"Fee payment status report generated successfully for fee {fee_id}"
            )
            
            return Response(report_data, status=status.HTTP_200_OK)
            
        except ValueError as e:
            logger.warning(f"ValueError in fee payment status: {str(e)}")
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            logger.error(f"Unexpected error in fee payment status: {str(e)}")
            return Response(
                {'error': 'An error occurred while generating the report'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=False, methods=['get'], url_path='overall-summary')
    def overall_summary(self, request):
        """
        Get overall payment summary across all fees.
        
        Query params:
            - estate_id (optional): Filter by specific estate
        
        Returns:
            - 200: Summary data
            - 400: Invalid request
            - 500: Server error
        """
        estate_id = request.query_params.get('estate_id', None)
        
        # Validate estate_id UUID format if provided
        if estate_id:
            try:
                uuid.UUID(estate_id)
            except (ValueError, AttributeError):
                logger.warning(f"Invalid UUID format for estate_id: {estate_id}")
                return Response(
                    {'error': 'Invalid estate ID format'},
                    status=status.HTTP_400_BAD_REQUEST
                )
        
        try:
            report_data = services.get_overall_payment_summary(
                user=request.user,
                estate_id=estate_id
            )
            
            logger.info(
                f"Overall summary report generated successfully "
                f"(estate_id={estate_id or 'all'})"
            )
            
            return Response(report_data, status=status.HTTP_200_OK)
            
        except ValueError as e:
            logger.warning(f"ValueError in overall summary: {str(e)}")
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            logger.error(f"Unexpected error in overall summary: {str(e)}")
            return Response(
                {'error': 'An error occurred while generating the report'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=False, methods=['get'], url_path='estate/(?P<estate_id>[^/.]+)')
    def estate_summary(self, request, estate_id=None):
        """
        Get payment summary for a specific estate.
        
        Returns:
            - 200: Estate summary data
            - 400: Invalid request or permission denied
            - 404: Invalid UUID format
            - 500: Server error
        """
        # Validate UUID format first
        try:
            uuid.UUID(estate_id)
        except (ValueError, AttributeError):
            logger.warning(f"Invalid UUID format for estate_id: {estate_id}")
            return Response(
                {'error': 'Invalid estate ID format'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        try:
            report_data = services.get_estate_payment_summary(
                user=request.user,
                estate_id=estate_id
            )
            
            logger.info(
                f"Estate summary report generated successfully for estate {estate_id}"
            )
            
            return Response(report_data, status=status.HTTP_200_OK)
            
        except ValueError as e:
            logger.warning(f"ValueError in estate summary: {str(e)}")
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            logger.error(f"Unexpected error in estate summary: {str(e)}")
            return Response(
                {'error': 'An error occurred while generating the report'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )