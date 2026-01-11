# maintenance/swagger.py

"""
Swagger/OpenAPI documentation configuration for the maintenance app.

Defines custom schema configurations for API documentation.
"""

from drf_yasg import openapi
from drf_yasg.views import get_schema_view
from rest_framework import permissions


# Custom response examples for documentation
MAINTENANCE_TICKET_EXAMPLE = {
    "id": "123e4567-e89b-12d3-a456-426614174000",
    "title": "Water leak in building A",
    "description": "There is a major water leak on the second floor affecting multiple units",
    "category": "WATER",
    "category_display": "Water",
    "status": "OPEN",
    "status_display": "Open",
    "created_by": "123e4567-e89b-12d3-a456-426614174001",
    "created_by_name": "John Doe",
    "unit": "123e4567-e89b-12d3-a456-426614174002",
    "identifier": "A-201",
    "estate": "123e4567-e89b-12d3-a456-426614174003",
    "estate_name": "Green Valley Estate",
    "created_at": "2024-01-15T10:30:00Z",
    "updated_at": "2024-01-15T10:30:00Z",
    "resolved_at": None,
    "is_resolved": False,
    "days_open": 5
}

TICKET_CREATE_EXAMPLE = {
    "title": "Broken elevator in Tower B",
    "description": "The main elevator in Tower B is not working. Residents are unable to access upper floors.",
    "category": "OTHER",
    "estate": "123e4567-e89b-12d3-a456-426614174003",
    "unit": None
}

TICKET_UPDATE_EXAMPLE = {
    "title": "Broken elevator in Tower B - URGENT",
    "description": "The main elevator in Tower B is still not working. Residents are unable to access upper floors. This is affecting elderly residents.",
    "category": "OTHER",
    "status": "OPEN",
    "unit": None
}

STATISTICS_EXAMPLE = {
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

ERROR_RESPONSE_EXAMPLE = {
    "error": "Detailed error message explaining what went wrong"
}

VALIDATION_ERROR_EXAMPLE = {
    "title": ["This field is required."],
    "category": ["Invalid category. Must be one of: WATER, ELECTRICITY, SECURITY, WASTE, OTHER"]
}


# Custom parameter definitions
ESTATE_ID_PARAM = openapi.Parameter(
    'estate_id',
    openapi.IN_QUERY,
    description="Filter tickets by estate UUID",
    type=openapi.TYPE_STRING,
    format=openapi.FORMAT_UUID
)

STATUS_PARAM = openapi.Parameter(
    'status',
    openapi.IN_QUERY,
    description="Filter tickets by status (OPEN or RESOLVED)",
    type=openapi.TYPE_STRING,
    enum=['OPEN', 'RESOLVED']
)

CATEGORY_PARAM = openapi.Parameter(
    'category',
    openapi.IN_QUERY,
    description="Filter tickets by category",
    type=openapi.TYPE_STRING,
    enum=['WATER', 'ELECTRICITY', 'SECURITY', 'WASTE', 'OTHER']
)

SEARCH_PARAM = openapi.Parameter(
    'search',
    openapi.IN_QUERY,
    description="Search tickets by title or description",
    type=openapi.TYPE_STRING
)

ORDERING_PARAM = openapi.Parameter(
    'ordering',
    openapi.IN_QUERY,
    description="Order results by field (prefix with - for descending)",
    type=openapi.TYPE_STRING,
    enum=['created_at', '-created_at', 'updated_at', '-updated_at', 'status', '-status']
)


# Response schemas
MAINTENANCE_TICKET_RESPONSE = openapi.Response(
    description="Maintenance ticket details",
    examples={
        "application/json": MAINTENANCE_TICKET_EXAMPLE
    }
)

MAINTENANCE_TICKET_LIST_RESPONSE = openapi.Response(
    description="List of maintenance tickets",
    examples={
        "application/json": {
            "count": 50,
            "next": "http://api.example.com/api/maintenance/tickets/?page=2",
            "previous": None,
            "results": [MAINTENANCE_TICKET_EXAMPLE]
        }
    }
)

STATISTICS_RESPONSE = openapi.Response(
    description="Ticket statistics",
    examples={
        "application/json": STATISTICS_EXAMPLE
    }
)

ERROR_RESPONSE = openapi.Response(
    description="Error response",
    examples={
        "application/json": ERROR_RESPONSE_EXAMPLE
    }
)

VALIDATION_ERROR_RESPONSE = openapi.Response(
    description="Validation error response",
    examples={
        "application/json": VALIDATION_ERROR_EXAMPLE
    }
)


# Schema view configuration (if needed at project level)
def get_maintenance_schema_view():
    """
    Get the schema view for maintenance app API documentation.
    
    This can be used at the project level to include maintenance app
    in the overall API documentation.
    
    Returns:
        Schema view instance
    """
    schema_view = get_schema_view(
        openapi.Info(
            title="Maintenance API",
            default_version='v1',
            description="""
            API for managing maintenance tickets in Estatly.
            
            ## Features
            - Create maintenance tickets for estate issues
            - Track ticket status (Open/Resolved)
            - Categorize issues (Water, Electricity, Security, Waste, Other)
            - Associate tickets with specific units or estates
            - Search and filter tickets
            - Get ticket statistics
            
            ## Authentication
            All endpoints require authentication. Use JWT or Token authentication
            as configured in your project settings.
            
            ## Permissions
            - Estate managers can create tickets
            - Ticket creators can update their own tickets
            - Staff users have full access to all tickets
            """,
            contact=openapi.Contact(email="api@estatly.com"),
            license=openapi.License(name="Proprietary"),
        ),
        public=True,
        permission_classes=[permissions.AllowAny],
    )
    
    return schema_view