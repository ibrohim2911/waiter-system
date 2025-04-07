from django.urls import path
from . import views

app_name = 'order'
urlpatterns = [
    # Order URLs
    path('orders/', views.OrderListView.as_view(), name='order_list'),
    path('orders/<int:pk>/', views.OrderDetailView.as_view(), name='order_detail'),
    path('orders/create/', views.OrderCreateView.as_view(), name='order_create'),
    path('orders/<int:pk>/update/', views.OrderUpdateView.as_view(), name='order_update'),
    path('orders/<int:pk>/delete/', views.OrderDeleteView.as_view(), name='order_delete'),

    # MenuItem URLs
    path('menuitems/', views.MenuItemListView.as_view(), name='menuitem_list'),
    path('menuitems/<int:pk>/', views.MenuItemDetailView.as_view(), name='menuitem_detail'),
    path('menuitems/create/', views.MenuItemCreateView.as_view(), name='menuitem_create'),
    path('menuitems/<int:pk>/update/', views.MenuItemUpdateView.as_view(), name='menuitem_update'),
    path('menuitems/<int:pk>/delete/', views.MenuItemDeleteView.as_view(), name='menuitem_delete'),

    # OrderItem URLs
    path('orderitems/', views.OrderItemListView.as_view(), name='orderitem_list'),
    path('orderitems/<int:pk>/', views.OrderItemDetailView.as_view(), name='orderitem_detail'),
    path('orderitems/create/', views.OrderItemCreateView.as_view(), name='orderitem_create'),
    path('orderitems/<int:pk>/update/', views.OrderItemUpdateView.as_view(), name='orderitem_update'),
    path('orderitems/<int:pk>/delete/', views.OrderItemDeleteView.as_view(), name='orderitem_delete'),

    # Reservations URLs
    path('reservations/', views.ReservationsListView.as_view(), name='reservations_list'),
    path('reservations/<int:pk>/', views.ReservationsDetailView.as_view(), name='reservations_detail'),
    path('reservations/create/', views.ReservationsCreateView.as_view(), name='reservations_create'),
    path('reservations/<int:pk>/update/', views.ReservationsUpdateView.as_view(), name='reservations_update'),
    path('reservations/<int:pk>/delete/', views.ReservationsDeleteView.as_view(), name='reservations_delete'),
]
