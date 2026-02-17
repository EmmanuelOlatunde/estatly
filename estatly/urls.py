from django.contrib import admin
from django.urls import path, include, re_path
from rest_framework import permissions
from drf_yasg.views import get_schema_view
from drf_yasg import openapi
from .swagger import api_info  # import the openapi.Info object

schema_view = get_schema_view(
    api_info,
    public=True,
    permission_classes=(permissions.AllowAny,),
)

urlpatterns = [
    path('admin/', admin.site.urls),
    
    # API endpoints
    path('api/accounts/', include('accounts.urls')),
    path('api/estates/', include('estates.urls')),
    path('api/units/', include('units.urls')),
    path('api/payments/', include('payments.urls')),
    path('api/maintenance/', include('maintenance.urls')),
    path('api/announcements/', include('announcements.urls')),
    path('api/reports/', include('reports.urls')),
    path('api/', include('documents.urls')),

    # Swagger documentation URLs
    re_path(r'^swagger(?P<format>\.json|\.yaml)$', 
            schema_view.without_ui(cache_timeout=0), 
            name='schema-json'),
    path('swagger/', 
         schema_view.with_ui('swagger', cache_timeout=0), 
         name='schema-swagger-ui'),
    path('redoc/', 
         schema_view.with_ui('redoc', cache_timeout=0), 
         name='schema-redoc'),
]

