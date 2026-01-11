# maintenance/urls.py

"""
URL configuration for the maintenance app.

Defines URL patterns and routing for maintenance ticket endpoints.
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views


app_name = "maintenance"  # ✅ REQUIRED

# Create router and register viewsets
router = DefaultRouter()
router.register(
    r'tickets',
    views.MaintenanceTicketViewSet,
    basename='maintenance-ticket'
)



# URL patterns
urlpatterns = [
    path('', include(router.urls)),
]

# Available endpoints:
# GET    /api/maintenance/tickets/                    - List all tickets
# POST   /api/maintenance/tickets/                    - Create a ticket
# GET    /api/maintenance/tickets/{id}/               - Retrieve a ticket
# PUT    /api/maintenance/tickets/{id}/               - Update a ticket
# PATCH  /api/maintenance/tickets/{id}/               - Partial update
# DELETE /api/maintenance/tickets/{id}/               - Delete a ticket
# POST   /api/maintenance/tickets/{id}/resolve/       - Resolve a ticket
# POST   /api/maintenance/tickets/{id}/reopen/        - Reopen a ticket
# GET    /api/maintenance/tickets/statistics/         - Get statistics