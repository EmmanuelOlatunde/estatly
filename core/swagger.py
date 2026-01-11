
# core/swagger.py
"""
Swagger/OpenAPI schema configuration for Estatly APIs.
"""

from drf_yasg.views import get_schema_view
from drf_yasg import openapi
from rest_framework import permissions


schema_view = get_schema_view(
    openapi.Info(
        title="Estatly MVP API",
        default_version='v1',
        description="""
        Estate Management SaaS API
        
        **MVP Features:**
        - Estate management (name, type, units)
        - Unit management (houses/flats with occupants)
        - Payment tracking (fees, payments, receipts)
        - Maintenance tickets (estate issues)
        - Announcements (one-way communication)
        - Reports (payment status, collections)
        
        **Authentication:**
        All endpoints require authentication.
        Two user types: Super Admin and Estate Manager.
        
        **Estate Context:**
        All data is scoped to estates. Estate managers can only access their own estate.
        Super admins can access all estates.
        """,
        terms_of_service="https://estatly.com/terms/",
        contact=openapi.Contact(email="support@estatly.com"),
        license=openapi.License(name="Proprietary"),
    ),
    public=True,
    permission_classes=[permissions.AllowAny],
)

