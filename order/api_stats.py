from rest_framework.views import APIView
from rest_framework.response import Response
from django.contrib.auth import get_user_model
from rest_framework.permissions import AllowAny
from django.db.models import Count, Q, Sum, F, DecimalField, Value
from drf_yasg import openapi
from datetime import datetime, timedelta
from django.utils.dateparse import parse_datetime
from drf_yasg.utils import swagger_auto_schema

from order.models import Order, OrderItem, MenuItem
from inventory.models import Inventory, Table

class OrdersPerUserAndTableView(APIView):
    """
    Returns various statistics related to orders, users, tables, and menu items.
    Supports filtering by a time period using 'period' (day, week, month)
    or a custom range with 'start_time' and 'end_time'.
    Example: /api/v1/order-stats/?period=week
    """

    permission_classes = [AllowAny]

    @swagger_auto_schema(
        tags=['Stats'],
        manual_parameters=[
            openapi.Parameter('period', openapi.IN_QUERY, description="Time period for stats (day, week, month, alltime, custom). Default is 'day'.", type=openapi.TYPE_STRING),
            openapi.Parameter("start_time", openapi.IN_QUERY, description="Start of the time window (ISO 8601 format)", type=openapi.TYPE_STRING, format=openapi.FORMAT_DATETIME),
            openapi.Parameter("end_time", openapi.IN_QUERY, description="End of the time window (ISO 8601 format)", type=openapi.TYPE_STRING, format=openapi.FORMAT_DATETIME),
        ]
    )
    def get(self, request, *args, **kwargs):
        User = get_user_model()

        # 1. Determine date range or 'alltime'
        period = request.query_params.get('period', 'day')
        start_time_str = request.query_params.get('start_time')
        end_time_str = request.query_params.get('end_time')
        now = datetime.now()

        start_date, end_date = None, None
        if period == 'day':
            start_date = now.replace(hour=0, minute=0, second=0, microsecond=0)
            end_date = now
        elif period == 'week':
            start_date = (now - timedelta(days=now.weekday())).replace(hour=0, minute=0, second=0, microsecond=0)
            end_date = now
        elif period == 'month':
            start_date = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            end_date = now
        elif period == 'custom' and start_time_str and end_time_str:
            start_date = parse_datetime(start_time_str)
            end_date = parse_datetime(end_time_str)
        elif period == 'alltime':
            # No date filtering needed
            pass
        else:
            # Default to 'day' if period is unrecognized
            period = 'day'
            start_date = now.replace(hour=0, minute=0, second=0, microsecond=0)
            end_date = now

        # 2. Create time filters based on period
        if period == 'alltime':
            order_time_filter = Q()
            user_order_time_filter = Q()
        else:
            order_time_filter = Q(c_at__range=(start_date, end_date))
            user_order_time_filter = Q(orders__c_at__range=(start_date, end_date))

        # 3. Efficiently fetch all orders based on the filter
        orders_in_period = Order.objects.filter(order_time_filter)

        # 4. User stats calculations
        users_stats = User.objects.annotate(
            completed_order_count=Count('orders', filter=user_order_time_filter & Q(orders__order_status='completed')),
            non_completed_order_count=Count('orders', filter=user_order_time_filter & ~Q(orders__order_status='completed')),
            pending_order_count=Count('orders', filter=user_order_time_filter & Q(orders__order_status='pending')),
            processing_order_count=Count('orders', filter=user_order_time_filter & Q(orders__order_status='processing')),
        ).values(
            'id', 'name',
            'completed_order_count', 'non_completed_order_count', 'pending_order_count', 'processing_order_count'
        )

        # 5. Location-based stats
        locations_stats = Order.objects.filter(order_time_filter).values('table__location').annotate(
            total_orders=Count('id'),
            pending_orders=Count('id', filter=Q(order_status='pending')),
            processing_orders=Count('id', filter=Q(order_status='processing')),
        ).order_by('table__location')

        # 6. Orders per user per location
        orders_per_user_per_location_stats = orders_in_period.values(
            'user__id', 'user__name', 'table__location'
        ).annotate(
            pending_orders=Count('id', filter=Q(order_status='pending')),
            processing_orders=Count('id', filter=Q(order_status='processing')),
        ).order_by('user__id', 'table__location')

        # 7. Reshape the existing data to fit the desired format.
        orders_per_user = users_stats.annotate(
            total_orders=F('completed_order_count') + F('non_completed_order_count')
        ).values('id', 'name', 'total_orders')

        pending_per_user = users_stats.filter(pending_order_count__gt=0).values(
            'id', 'name', 'pending_order_count'
        )
        
        processing_per_user = users_stats.filter(processing_order_count__gt=0).values(
            'id', 'name', 'processing_order_count'
        )

        orders_per_location = locations_stats.values(
            'table__location', 'total_orders'
        )

        pending_per_location = locations_stats.filter(pending_orders__gt=0).values(
            'table__location', 'pending_orders'
        )

        processing_per_location = locations_stats.filter(processing_orders__gt=0).values(
            'table__location', 'processing_orders'
        )

        # 8. Prepare response
        formatted_response = {
            'orders_per_user_per_location': list(orders_per_user_per_location_stats),
            'orders_per_user': list(orders_per_user),
            'pending_order_per_user': list(pending_per_user),
            'processing_order_per_user': list(processing_per_user),
            'orders_per_table_location': list(orders_per_location),
            'pending_order_per_location': list(pending_per_location),
            'processing_order_per_location': list(processing_per_location),
        }
        
        return Response(formatted_response)