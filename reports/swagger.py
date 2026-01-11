# reports/swagger.py
"""
Swagger/OpenAPI schema customizations for reports app.
"""

from drf_yasg.views import get_schema_view
from drf_yasg import openapi
from rest_framework import permissions


schema_view = get_schema_view(
    openapi.Info(
        title="Estatly Reports API",
        default_version='v1',
        description="""
        API for generating payment reports in Estatly property management system.
        
        Features:
        - Fee payment status (who paid, who didn't)
        - Total collected amounts per fee
        - Overall payment summaries
        - Property-specific reports
        
        All reports are computed dynamically - no data is stored.
        """,
        contact=openapi.Contact(email="support@estatly.com"),
        license=openapi.License(name="Proprietary"),
    ),
    public=False,
    permission_classes=(permissions.IsAuthenticated,),
)