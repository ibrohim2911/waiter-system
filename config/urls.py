# c:\Users\User\Desktop\waiter-system\config\urls.py
from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),

    # --- REMOVE Web URL Includes ---
    # path('orders/', include(('order.urls', 'order'), namespace='order')),
    # path('inventory/', include(('inventory.urls', 'inventory'), namespace='inventory')),
    # path('users/', include(('user.urls', 'user'), namespace='user')),

    # --- API URLs ---
    # Include the api_urls from each app
    path('api/v1/', include('order.api_urls')),
    path('api/v1/', include('inventory.api_urls')),
    path('api/v1/', include('user.api_urls')),

    # --- DRF Browsable API Auth ---
    # Keep this for easy testing/login via the browser during development
    path('api-auth/', include('rest_framework.urls', namespace='rest_framework')),
]
