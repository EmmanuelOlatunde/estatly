# estate/swagger.py
"""
Swagger/OpenAPI schema customizations for estate app.
"""

from drf_yasg import openapi
from drf_yasg.views import get_schema_view
from rest_framework import permissions


schema_view = get_schema_view(
    openapi.Info(
        title="Estate API",
        default_version='v1',
        description="""
        API for managing estate information in the Estatly platform.
        
        ## Features
        - Create, read, update, and delete estates
        - Filter estates by type, status, and other criteria
        - Search estates by name, description, or address
        - Get estate statistics
        - Activate/deactivate estates
        
        ## Estate Types
        - **Government**: Government-owned estates
        - **Private**: Privately-owned estates
        
        ## Fee Frequencies
        - **Monthly**: Fees collected monthly
        - **Yearly**: Fees collected yearly
        """,
        terms_of_service="https://www.estatly.com/terms/",
        contact=openapi.Contact(email="support@estatly.com"),
        license=openapi.License(name="Proprietary"),
    ),
    public=True,
    permission_classes=(permissions.AllowAny,),
)


# Custom schema responses for common operations
estate_list_response = openapi.Response(
    description="List of estates",
    schema=openapi.Schema(
        type=openapi.TYPE_ARRAY,
        items=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'id': openapi.Schema(type=openapi.TYPE_STRING, format='uuid'),
                'name': openapi.Schema(type=openapi.TYPE_STRING),
                'estate_type': openapi.Schema(type=openapi.TYPE_STRING),
                'is_active': openapi.Schema(type=openapi.TYPE_BOOLEAN),
            }
        )
    )
)

estate_detail_response = openapi.Response(
    description="Estate details",
    schema=openapi.Schema(
        type=openapi.TYPE_OBJECT,
        properties={
            'id': openapi.Schema(type=openapi.TYPE_STRING, format='uuid'),
            'name': openapi.Schema(type=openapi.TYPE_STRING),
            'estate_type': openapi.Schema(type=openapi.TYPE_STRING),
            'approximate_units': openapi.Schema(type=openapi.TYPE_INTEGER),
            'fee_frequency': openapi.Schema(type=openapi.TYPE_STRING),
            'is_active': openapi.Schema(type=openapi.TYPE_BOOLEAN),
            'description': openapi.Schema(type=openapi.TYPE_STRING),
            'address': openapi.Schema(type=openapi.TYPE_STRING),
            'created_at': openapi.Schema(type=openapi.TYPE_STRING, format='date-time'),
            'updated_at': openapi.Schema(type=openapi.TYPE_STRING, format='date-time'),
        }
    )
)
