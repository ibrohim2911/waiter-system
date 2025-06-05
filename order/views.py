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
    permission_classes = [permissions.IsAuthenticated]
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

    def create(self, request, *args, **kwargs):
        is_many = isinstance(request.data, list)
        serializer = self.get_serializer(data=request.data, many=is_many)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        # Get the order ID(s) from the created items
        order_ids = set()
        if is_many:
            for item in serializer.data:
                order_ids.add(item['order'])
        else:
            order_ids.add(serializer.data['order'])
        # Generate a kitchen ticket for each order involved
        for order_id in order_ids:
            generate_kitchen_ticket(order_id)
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)

    def perform_create(self, serializer):
        serializer.save()

# Place this helper function somewhere in the file (or import from utils)
def generate_kitchen_ticket(order_id):
    from .models import Order  # Import here to avoid circular import
    order = Order.objects.get(id=order_id)
    items = order.orderitem.all()
    ticket = f"\n--- KITCHEN TICKET ---\nTable: {getattr(order, 'table', 'N/A')}\nOrder: {order.id}\n"
    for item in items:
        ticket += f"{item.menu_item.name} x {item.quantity}\n"
    ticket += "----------------------\n"
    print(ticket)  # Replace with actual print/send logic
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
