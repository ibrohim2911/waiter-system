from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAdminUser
from django.db.models import Sum, F, Q
from django.utils.dateparse import parse_datetime
from order.models import Order, OrderItem
from inventory.models import Inventory
from django.contrib.auth import get_user_model
from datetime import datetime, timedelta

from drf_yasg.utils import swagger_auto_schema
class AdminReportView(APIView):
    """
    Returns admin reports for spending, profit, pure profit, waiter performance, and other stats.
    Supports filtering by day, week, month, and custom time period.
    """
    permission_classes = [IsAdminUser]

    @swagger_auto_schema(tags=['Reports'])
    def get(self, request, *args, **kwargs):
        # Get time filters from query params
        period = request.query_params.get('period', 'day')  # day, week, month, custom
        start = request.query_params.get('start')
        end = request.query_params.get('end')
        now = datetime.now()

        if period == 'day':
            start_date = now.replace(hour=0, minute=0, second=0, microsecond=0)
            end_date = now
        elif period == 'week':
            start_date = now - timedelta(days=now.weekday())
            start_date = start_date.replace(hour=0, minute=0, second=0, microsecond=0)
            end_date = now
        elif period == 'month':
            start_date = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            end_date = now
        elif period == 'custom' and start and end:
            start_date = parse_datetime(start) or now
            end_date = parse_datetime(end) or now
        else:
            start_date = now.replace(hour=0, minute=0, second=0, microsecond=0)
            end_date = now

        # Filter orders by date
        orders = Order.objects.filter(c_at__gte=start_date, c_at__lte=end_date)

        # Total spent (sum of order amounts)
        total_spent = orders.aggregate(total=Sum('amount'))['total'] or 0
        # Total pure profit (sum of subamounts)
        total_pure_profit = orders.aggregate(total=Sum('subamount'))['total'] or 0
        # Total profit (amount - subamount)
        total_profit = total_spent - total_pure_profit

        # Waiter performance: orders per waiter
        User = get_user_model()
        waiters = User.objects.filter(is_staff=False)
        waiter_stats = []
        for waiter in waiters:
            waiter_orders = orders.filter(user=waiter)
            count = waiter_orders.count()
            spent = waiter_orders.aggregate(total=Sum('amount'))['total'] or 0
            waiter_stats.append({
                'waiter_id': waiter.id,
                'username': getattr(waiter, 'username', str(waiter)),
                'order_count': count,
                'total_spent': spent
            })

        # Inventory usage (optional, can be expanded)
        inventory_stats = []
        for inv in Inventory.objects.all():
            used = OrderItem.objects.filter(menu_item__ingredients__inventory=inv, order__in=orders).aggregate(total=Sum('quantity'))['total'] or 0
            inventory_stats.append({
                'inventory_id': inv.id,
                'name': inv.name,
                'used_quantity': float(used),
                'remaining_quantity': float(inv.quantity)
            })

        return Response({
            'period': period,
            'start': start_date,
            'end': end_date,
            'total_spent': float(total_spent),
            'total_profit': float(total_profit),
            'total_pure_profit': float(total_pure_profit),
            'waiter_stats': waiter_stats,
            'inventory_stats': inventory_stats,
            'order_count': orders.count(),
        })
