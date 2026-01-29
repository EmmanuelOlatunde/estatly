# payments/swagger.py

"""
Swagger/OpenAPI schema customizations for the payments app.

Provides better API documentation for payment endpoints.
"""

from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema


fee_create_schema = swagger_auto_schema(
    operation_description="""
    Create a new fee and assign it to units.
    
    You must either:
    - Set `assign_to_all_units` to true to assign to all units in the estate, OR
    - Provide a list of `unit_ids` to assign to specific units
    
    The fee will be automatically assigned to the specified units with 'unpaid' status.
    """,
    request_body=openapi.Schema(
        type=openapi.TYPE_OBJECT,
        required=['name', 'amount', 'due_date', 'estate'],
        properties={
            'name': openapi.Schema(
                type=openapi.TYPE_STRING,
                description='Fee name (e.g., "Security Levy 2025")'
            ),
            'description': openapi.Schema(
                type=openapi.TYPE_STRING,
                description='Optional detailed description'
            ),
            'amount': openapi.Schema(
                type=openapi.TYPE_NUMBER,
                description='Fee amount (must be positive)'
            ),
            'due_date': openapi.Schema(
                type=openapi.TYPE_STRING,
                format=openapi.FORMAT_DATE,
                description='Payment due date (YYYY-MM-DD)'
            ),
            'estate': openapi.Schema(
                type=openapi.TYPE_STRING,
                format=openapi.FORMAT_UUID,
                description='Estate UUID'
            ),
            'assign_to_all_units': openapi.Schema(
                type=openapi.TYPE_BOOLEAN,
                description='If true, assign to all units in the estate'
            ),
            'unit_ids': openapi.Schema(
                type=openapi.TYPE_ARRAY,
                items=openapi.Schema(type=openapi.TYPE_STRING, format=openapi.FORMAT_UUID),
                description='List of unit UUIDs to assign this fee to'
            ),
        }
    ),
    responses={
        201: openapi.Response(
            description='Fee created successfully',
        ),
        400: openapi.Response(
            description='Validation error',
        ),
    }
)


payment_create_schema = swagger_auto_schema(
    operation_description="""
    Record a payment for a fee assignment (mark as paid).
    
    This will:
    1. Create a Payment record
    2. Update the FeeAssignment status to 'paid'
    3. Auto-generate a Receipt
    
    The payment amount must exactly match the fee amount.
    """,
    request_body=openapi.Schema(
        type=openapi.TYPE_OBJECT,
        required=['fee_assignment', 'amount', 'payment_method'],
        properties={
            'fee_assignment': openapi.Schema(
                type=openapi.TYPE_STRING,
                format=openapi.FORMAT_UUID,
                description='FeeAssignment UUID to mark as paid'
            ),
            'amount': openapi.Schema(
                type=openapi.TYPE_NUMBER,
                description='Payment amount (must match fee amount)'
            ),
            'payment_method': openapi.Schema(
                type=openapi.TYPE_STRING,
                enum=['bank_transfer', 'cash'],
                description='Method of payment'
            ),
            'payment_date': openapi.Schema(
                type=openapi.TYPE_STRING,
                format=openapi.FORMAT_DATETIME,
                description='When payment was made (defaults to now)'
            ),
            'reference_number': openapi.Schema(
                type=openapi.TYPE_STRING,
                description='Optional payment reference (e.g., transaction ID)'
            ),
            'notes': openapi.Schema(
                type=openapi.TYPE_STRING,
                description='Optional payment notes'
            ),
        }
    ),
    responses={
        201: openapi.Response(
            description='Payment recorded successfully',
        ),
        400: openapi.Response(
            description='Validation error (already paid, amount mismatch, etc.)',
        ),
    }
)


fee_payment_summary_schema = swagger_auto_schema(
    method='get',  # FIXED: Added method parameter to prevent duplicate parameters
    operation_description="""
    Get payment summary statistics for a fee.
    
    Returns:
    - Total units assigned
    - Paid/unpaid counts
    - Payment completion rate
    - Revenue figures (expected, collected, outstanding)
    """,
    responses={
        200: openapi.Response(
            description='Payment summary',
            schema=openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    'total_assigned_units': openapi.Schema(type=openapi.TYPE_INTEGER),
                    'total_paid': openapi.Schema(type=openapi.TYPE_INTEGER),
                    'total_unpaid': openapi.Schema(type=openapi.TYPE_INTEGER),
                    'payment_completion_rate': openapi.Schema(type=openapi.TYPE_NUMBER),
                    'total_expected_revenue': openapi.Schema(type=openapi.TYPE_NUMBER),
                    'total_collected_revenue': openapi.Schema(type=openapi.TYPE_NUMBER),
                    'total_outstanding_revenue': openapi.Schema(type=openapi.TYPE_NUMBER),
                }
            )
        ),
    }
)


assign_to_units_schema = swagger_auto_schema(
    method='post',  # FIXED: Added method parameter to prevent duplicate parameters
    operation_description="""
    Assign an existing fee to additional units.
    
    This allows you to add more units to a fee after it has been created.
    """,
    request_body=openapi.Schema(
        type=openapi.TYPE_OBJECT,
        required=['unit_ids'],
        properties={
            'unit_ids': openapi.Schema(
                type=openapi.TYPE_ARRAY,
                items=openapi.Schema(type=openapi.TYPE_STRING, format=openapi.FORMAT_UUID),
                description='List of unit UUIDs to assign this fee to'
            ),
        }
    ),
    responses={
        201: openapi.Response(
            description='Fee assigned to units successfully',
        ),
        400: openapi.Response(
            description='Validation error (units already assigned, invalid unit IDs, etc.)',
        ),
    }
)


receipt_download_schema = swagger_auto_schema(
    method='get',  # FIXED: Added method parameter to prevent duplicate parameters
    operation_description="""
    Download a receipt as PDF.
    
    Note: PDF generation is not yet implemented in MVP.
    This endpoint currently returns receipt metadata.
    """,
    responses={
        200: openapi.Response(
            description='Receipt data (PDF generation pending)',
        ),
    }
)