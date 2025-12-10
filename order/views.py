import logging
from rest_framework.response import Response
from rest_framework import status
from rest_framework import viewsets, permissions, pagination
from rest_framework.exceptions import PermissionDenied
from .models import Order, MenuItem, OrderItem, Reservations
from .filters import OrderFilter
from .serializers import (
    OrderSerializer,
    MenuItemSerializer,
    OrderItemSerializer,
    ReservationsSerializer,
)
from drf_yasg.utils import swagger_auto_schema

logger = logging.getLogger(__name__)

def generate_kitchen_ticket_for_items(items):
    ticket = "\n--- KITCHEN TICKET ---\n"
    for item in items:
        order = item.order
        table_number = getattr(order.table, 'number', order.table_id)
        order_time = order.u_at.strftime('%Y-%m-%d %H:%M:%S')
        user = getattr(order.user, 'username', str(order.user))
        ticket += f"Table: {table_number}\n"
        ticket += f"Order: {order.id}\n"
        ticket += f"Time: {order_time}\n"
        ticket += f"User: {user}\n"
        ticket += f"{item.menu_item.name} x {item.quantity}\n"
    ticket += "----------------------\n"
    logger.info(ticket)

class OrderPagination(pagination.PageNumberPagination):
    page_size = 100
    page_size_query_param = 'page_size'
    max_page_size = 100

@swagger_auto_schema(tags=['Orders'])
class OrderViewSet(viewsets.ModelViewSet):
    """ API endpoint for Orders """
    serializer_class = OrderSerializer
    permission_classes = [permissions.IsAuthenticated]

    pagination_class = OrderPagination
    filterset_fields = ['order_status']
    filterset_class = OrderFilter
    def get_queryset(self):
        """Filter orders for the current user (waiter) or allow filtering by table location and user for others."""
        user = self.request.user
        queryset = Order.objects.all()
        try:
            if hasattr(user, 'role') and user.role == "waiter":
                queryset = queryset.filter(user=user)
            else:
                table_locations = self.request.query_params.getlist('table__location')
                user_ids = self.request.query_params.getlist('user')
                statuses = self.request.query_params.getlist('order_status')
                # Support comma-separated values as fallback
                if len(statuses) == 1 and ',' in statuses[0]:
                    statuses = [s.strip() for s in statuses[0].split(',') if s.strip()]
                if len(table_locations) == 1 and ',' in table_locations[0]:
                    table_locations = [l.strip() for l in table_locations[0].split(',') if l.strip()]
                if len(user_ids) == 1 and ',' in user_ids[0]:
                    user_ids = [u.strip() for u in user_ids[0].split(',') if u.strip()]
                print("table__location from params:", table_locations)
                print("user from params:", user_ids)
                print("order_status from params:", statuses)
                if table_locations:
                    queryset = queryset.filter(table__location__in=table_locations)
                if user_ids:
                    queryset = queryset.filter(user_id__in=user_ids)
                if statuses:
                    queryset = queryset.filter(order_status__in=statuses)
            return queryset.order_by('-c_at')
        except PermissionDenied:
            logger.warning("Unauthenticated user tried to access order list.")
            return Order.objects.none()

    def perform_create(self, serializer):
        """ Associate the order with the logged-in user. """
        serializer.save(user=self.request.user)

    def update(self, request, *args, **kwargs):
        response = super().update(request, *args, **kwargs)
        order = self.get_object()
        if order.order_status == "completed":
            logger.info(f"Cheque receipt for order {order.id} generated.")
        return response

@swagger_auto_schema(tags=['MenuItems'])
class MenuItemViewSet(viewsets.ModelViewSet):
    queryset = MenuItem.objects.all().order_by('category', 'name')
    serializer_class = MenuItemSerializer
    permission_classes = [permissions.IsAuthenticated]

@swagger_auto_schema(tags=['OrderItems'])
class OrderItemViewSet(viewsets.ModelViewSet):
    queryset = OrderItem.objects.all()
    serializer_class = OrderItemSerializer
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = OrderPagination
    
    def get_queryset(self):
        """ Filter order items based on the user who owns the parent order. """
        user = self.request.user
        try:
            if user.is_staff:
                return OrderItem.objects.all()
            return OrderItem.objects.filter(order__user=user)
        except PermissionDenied:
            logger.warning("Unauthenticated user tried to access order item list.")
            return OrderItem.objects.none()

    def create(self, request, *args, **kwargs):
        is_many = isinstance(request.data, list)
        serializer = self.get_serializer(data=request.data, many=is_many)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        
        created_items = serializer.instance if is_many else [serializer.instance]
        generate_kitchen_ticket_for_items(created_items)
        
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)

    def perform_create(self, serializer):
        serializer.save()

@swagger_auto_schema(tags=['Reservations'])
class ReservationsViewSet(viewsets.ModelViewSet):
    """ API endpoint for Reservations """
    queryset = Reservations.objects.all().order_by('-reservation_time')
    serializer_class = ReservationsSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        """ Filter reservations for the current user unless they are staff. """
        user = self.request.user
        try:
            queryset = Reservations.objects.all()
            if not user.is_staff:
                queryset = queryset.filter(user=user)
            return queryset.order_by('-reservation_time')
        except PermissionDenied:
            logger.warning("Unauthenticated user tried to access reservation list.")
            return Reservations.objects.none()

    def perform_create(self, serializer):
        """ Associate the reservation with the logged-in user. """
        serializer.save(user=self.request.user)
