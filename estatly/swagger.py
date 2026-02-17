# estatly/swagger.py
from drf_yasg import openapi

api_info = openapi.Info(
    title="Estatly API",
    default_version='v1',
    description="API documentation for Estatly - Real Estate Management System",
    terms_of_service="https://www.yourapp.com/terms/",
    contact=openapi.Contact(email="contact@estatly.com"),
    license=openapi.License(name="BSD License"),
)