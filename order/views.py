# order/views.py
from rest_framework import viewsets, permissions
from .models import Order, MenuItem, OrderItem, Reservations
from .serializers import (
    OrderSerializer,
    MenuItemSerializer,
    OrderItemSerializer,
    ReservationsSerializer
)
# Optional: Import PermissionDenied for custom checks
# from rest_framework.exceptions import PermissionDenied

class OrderViewSet(viewsets.ModelViewSet):
    """ API endpoint for Orders """
    serializer_class = OrderSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        """ Filter orders for the current user unless they are staff. """
        user = self.request.user
        if user.is_staff:
            queryset = Order.objects.all()
        else:
            queryset = Order.objects.filter(user=user)
        # Allow filtering by status via query param e.g., /api/v1/orders/?status=pending
        status = self.request.query_params.get('status')
        if status is not None:
            queryset = queryset.filter(order_status=status)
        return queryset.order_by('-c_at')

    def perform_create(self, serializer):
        """ Associate the order with the logged-in user. """
        serializer.save(user=self.request.user)

class MenuItemViewSet(viewsets.ModelViewSet):
    """ API endpoint for Menu Items """
    queryset = MenuItem.objects.all().order_by('category', 'name')
    serializer_class = MenuItemSerializer
    # Permissions: Example - Only admins can modify menu items
    permission_classes = [permissions.IsAdminUser]

class OrderItemViewSet(viewsets.ModelViewSet):
    """ API endpoint for Order Items """
    queryset = OrderItem.objects.all()
    serializer_class = OrderItemSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        """ Filter order items based on the user who owns the parent order. """
        user = self.request.user
        if user.is_staff:
            return OrderItem.objects.all()
        return OrderItem.objects.filter(order__user=user)

    # Optional: Add validation in perform_create/perform_update
    # def perform_create(self, serializer):
    #     order = serializer.validated_data['order']
    #     if not self.request.user.is_staff and order.user != self.request.user:
    #         raise PermissionDenied("Cannot add items to another user's order.")
    #     super().perform_create(serializer)

class ReservationsViewSet(viewsets.ModelViewSet):
    """ API endpoint for Reservations """
    queryset = Reservations.objects.all().order_by('-reservation_time')
    serializer_class = ReservationsSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        """ Filter reservations for the current user unless they are staff. """
        user = self.request.user
        if user.is_staff:
            return Reservations.objects.all().order_by('-reservation_time')
        return Reservations.objects.filter(user=user).order_by('-reservation_time')

    def perform_create(self, serializer):
        """ Associate the reservation with the logged-in user. """
        serializer.save(user=self.request.user)
