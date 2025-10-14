# c:\Users\User\Desktop\waiter-system\config\urls.py
from django.contrib import admin
from django.urls import path, include, re_path
from rest_framework_simplejwt.views import TokenRefreshView
from django.http import JsonResponse
from django.views.decorators.csrf import ensure_csrf_cookie
from user.views import getmeview

# Re-add csrf view for CSRF cookie endpoint
@ensure_csrf_cookie
def csrf(request):
    return JsonResponse({'detail': 'CSRF cookie set'})

# drf-yasg imports for Swagger
from rest_framework import permissions
from drf_yasg.views import get_schema_view
from drf_yasg import openapi

schema_view = get_schema_view(
    openapi.Info(
        title="Waiter System API",
        default_version='v1',
        description="API documentation for Waiter System",
    ),
    public=True,
    permission_classes=(permissions.AllowAny,),
)

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/v1/csrf/', csrf, name='csrf'),  # CSRF cookie endpoint
    # --- REMOVE Web URL Includes ---
    # path('orders/', include(('order.urls', 'order'), namespace='order')),
    # path('inventory/', include(('inventory.urls', 'inventory'), namespace='inventory')),
    # path('users/', include(('user.urls', 'user'), namespace='user')),

    # --- API URLs ---
    # Include the api_urls from each app
    path('api/v1/', include('order.api_urls')),
    path('api/v1/', include('inventory.api_urls')),
    path('api/v1/', include('user.api_urls')),
    path('api/v1/', include('log.api_urls')),
    # path('api/v1/reports/', include('reports.api_urls')),
    path('api/v1/getme/', getmeview, name='getme'),
    # --- DRF Browsable API Auth ---
    # Keep this for easy testing/login via the browser during development
    path('api-auth/', include('rest_framework.urls', namespace='rest_framework')),
    path('auth/refresh/', TokenRefreshView.as_view(), name='token_refresh'),

    # Swagger and Redoc endpoints
    re_path(r'^swagger(?P<format>\.json|\.yaml)$', schema_view.without_ui(cache_timeout=0), name='schema-json'),
    path('swagger/', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
    path('redoc/', schema_view.with_ui('redoc', cache_timeout=0), name='schema-redoc'),
]
