# order/api_urls.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views # Assuming ViewSets are in views.py
from .api_stats import OrdersPerUserAndTableView
from .api_reports import AdminReportView

router = DefaultRouter()
router.register(r'orders', views.OrderViewSet, basename='order')
# Register new ViewSets
router.register(r'menuitems', views.MenuItemViewSet, basename='menuitem')
router.register(r'orderitems', views.OrderItemViewSet, basename='orderitem')
router.register(r'reservations', views.ReservationsViewSet, basename='reservation')


urlpatterns = [
    path('', include(router.urls)),
    path('stats/orders-per-user-and-table/', OrdersPerUserAndTableView.as_view(), name='orders_per_user_and_table'),
    path('reports/admin/', AdminReportView.as_view(), name='admin_report'),
]
