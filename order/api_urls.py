# order/api_urls.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views # Assuming ViewSets are in views.py

router = DefaultRouter()
router.register(r'orders', views.OrderViewSet, basename='order')
# Register new ViewSets
router.register(r'menuitems', views.MenuItemViewSet, basename='menuitem')
router.register(r'orderitems', views.OrderItemViewSet, basename='orderitem')
router.register(r'reservations', views.ReservationsViewSet, basename='reservation')


urlpatterns = [
    path('', include(router.urls)),
]
