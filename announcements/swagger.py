# announcements/swagger.py

"""
Swagger/OpenAPI documentation configuration for announcements app.

Provides detailed API documentation schemas.
"""

from drf_yasg import openapi

# Common response schemas
announcement_response_schema = openapi.Schema(
    type=openapi.TYPE_OBJECT,
    properties={
        'id': openapi.Schema(
            type=openapi.TYPE_STRING,
            format='uuid',
            description='Unique identifier for the announcement'
        ),
        'title': openapi.Schema(
            type=openapi.TYPE_STRING,
            description='Announcement title',
            max_length=200
        ),
        'message': openapi.Schema(
            type=openapi.TYPE_STRING,
            description='Full announcement content'
        ),
        'preview': openapi.Schema(
            type=openapi.TYPE_STRING,
            description='Preview of the message (first 100 characters)'
        ),
        'created_by': openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'id': openapi.Schema(type=openapi.TYPE_STRING, format='uuid'),
                'email': openapi.Schema(type=openapi.TYPE_STRING, format='email'),
                'full_name': openapi.Schema(type=openapi.TYPE_STRING),
            },
            description='User who created the announcement'
        ),
        'is_active': openapi.Schema(
            type=openapi.TYPE_BOOLEAN,
            description='Whether the announcement is currently active'
        ),
        'created_at': openapi.Schema(
            type=openapi.TYPE_STRING,
            format='date-time',
            description='Timestamp when announcement was created'
        ),
        'updated_at': openapi.Schema(
            type=openapi.TYPE_STRING,
            format='date-time',
            description='Timestamp when announcement was last updated'
        ),
    },
    required=['id', 'title', 'message', 'created_by', 'is_active', 'created_at', 'updated_at']
)

announcement_create_schema = openapi.Schema(
    type=openapi.TYPE_OBJECT,
    properties={
        'title': openapi.Schema(
            type=openapi.TYPE_STRING,
            description='Announcement title (min 3 characters)',
            max_length=200
        ),
        'message': openapi.Schema(
            type=openapi.TYPE_STRING,
            description='Full announcement content (min 10 characters)'
        ),
        'is_active': openapi.Schema(
            type=openapi.TYPE_BOOLEAN,
            description='Whether the announcement is active (default: true)',
            default=True
        ),
    },
    required=['title', 'message']
)

announcement_update_schema = openapi.Schema(
    type=openapi.TYPE_OBJECT,
    properties={
        'title': openapi.Schema(
            type=openapi.TYPE_STRING,
            description='Announcement title (min 3 characters)',
            max_length=200
        ),
        'message': openapi.Schema(
            type=openapi.TYPE_STRING,
            description='Full announcement content (min 10 characters)'
        ),
        'is_active': openapi.Schema(
            type=openapi.TYPE_BOOLEAN,
            description='Whether the announcement is active'
        ),
    }
)

# Common error response schemas
error_400_schema = openapi.Schema(
    type=openapi.TYPE_OBJECT,
    properties={
        'field_name': openapi.Schema(
            type=openapi.TYPE_ARRAY,
            items=openapi.Schema(type=openapi.TYPE_STRING),
            description='List of validation errors for this field'
        )
    },
    description='Validation errors'
)

error_403_schema = openapi.Schema(
    type=openapi.TYPE_OBJECT,
    properties={
        'detail': openapi.Schema(
            type=openapi.TYPE_STRING,
            description='Permission denied message'
        )
    }
)

error_404_schema = openapi.Schema(
    type=openapi.TYPE_OBJECT,
    properties={
        'detail': openapi.Schema(
            type=openapi.TYPE_STRING,
            description='Not found message'
        )
    }
)

# Query parameters
list_query_parameters = [
    openapi.Parameter(
        'is_active',
        openapi.IN_QUERY,
        description='Filter by active status',
        type=openapi.TYPE_BOOLEAN
    ),
    openapi.Parameter(
        'created_by',
        openapi.IN_QUERY,
        description='Filter by creator user ID (UUID)',
        type=openapi.TYPE_STRING,
        format='uuid'
    ),
    openapi.Parameter(
        'search',
        openapi.IN_QUERY,
        description='Search in title and message',
        type=openapi.TYPE_STRING
    ),
    openapi.Parameter(
        'ordering',
        openapi.IN_QUERY,
        description='Order results by field (prefix with - for descending). '
                    'Options: created_at, updated_at, title',
        type=openapi.TYPE_STRING
    ),
    openapi.Parameter(
        'include_inactive',
        openapi.IN_QUERY,
        description='Include inactive announcements (default: false)',
        type=openapi.TYPE_BOOLEAN
    ),
    openapi.Parameter(
        'page',
        openapi.IN_QUERY,
        description='Page number for pagination',
        type=openapi.TYPE_INTEGER
    ),
    openapi.Parameter(
        'page_size',
        openapi.IN_QUERY,
        description='Number of results per page',
        type=openapi.TYPE_INTEGER
    ),
]

# API tags
announcement_tag = 'announcements'