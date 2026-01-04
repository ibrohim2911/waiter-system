from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAdminUser
from django.db.models import Sum, F, Q, Count
from django.utils.dateparse import parse_datetime
from order.models import Order, OrderItem, MenuItem
from inventory.models import Inventory, InventoryUsage, Table
from django.contrib.auth import get_user_model
from datetime import datetime, timedelta

# drf-yasg helpers for explicit Swagger params
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from django.utils.decorators import method_decorator


MANUAL_PARAMS = [
    openapi.Parameter(
        'period', openapi.IN_QUERY,
        description="Time period: day|week|month|alltime|custom (default: day)",
        type=openapi.TYPE_STRING,
        enum=['day', 'week', 'month', 'alltime', 'custom']
    ),
    openapi.Parameter(
        'start', openapi.IN_QUERY,
        description="Start datetime (ISO) when period=custom",
        type=openapi.TYPE_STRING, format=openapi.FORMAT_DATETIME
    ),
    openapi.Parameter(
        'end', openapi.IN_QUERY,
        description="End datetime (ISO) when period=custom",
        type=openapi.TYPE_STRING, format=openapi.FORMAT_DATETIME
    ),
    openapi.Parameter(
        'reports', openapi.IN_QUERY,
        description="Comma-separated list of report keys: revenue_by_category, hourly_revenue, revenue_by_waiter, open_orders_by_hall, dish_consumption, dish_sales, inventory_usage, consolidated_summary",
        type=openapi.TYPE_STRING,
        example="revenue_by_category,hourly_revenue,revenue_by_waiter",
        required=False
    ),
]


@method_decorator(swagger_auto_schema(manual_parameters=MANUAL_PARAMS, tags=['Reports']), name='get')
class AdminReportView(APIView):
    """
    Admin reporting API: returns a selection of reports derived from available models.

    Implemented reports (English only):
      - revenue_by_category: total revenue per menu category (gross sales)
      - hourly_revenue: revenue grouped by hour
      - revenue_by_waiter: revenue per waiter
      - open_orders_by_hall: counts and sales of non-completed orders grouped by table location
      - dish_consumption: total quantity consumed per menu item
      - dish_sales: total revenue per menu item
      - inventory_usage: total used quantity per inventory item (from InventoryUsage)
      - consolidated_summary: high-level totals

    Query params:
      - period: day|week|month|alltime|custom (default: day)
      - start, end: ISO datetimes when period=custom
      - reports: comma-separated list of reports to include (default: all implemented)
    """

    permission_classes = []

    IMPLEMENTED_REPORTS = {
        'revenue_by_category',
        'hourly_revenue',
        'revenue_by_waiter',
        'open_orders_by_hall',
        'dish_consumption',
        'dish_sales',
        'inventory_usage',
        'consolidated_summary',
    }

    def _parse_period(self, period, start, end):
        now = datetime.now()
        if period == 'alltime':
            return None, None
        elif period == 'day':
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
        return start_date, end_date

    def get(self, request, *args, **kwargs):
        period = request.query_params.get('period', 'day')
        start = request.query_params.get('start')
        end = request.query_params.get('end')
        reports_param = request.query_params.get('reports')

        if reports_param:
            requested = {r.strip() for r in reports_param.split(',') if r.strip()}
            reports = list(requested & self.IMPLEMENTED_REPORTS)
        else:
            reports = list(self.IMPLEMENTED_REPORTS)

        start_date, end_date = self._parse_period(period, start, end)

        # Base queryset for orders in range
        orders_qs = Order.objects.all()
        if start_date and end_date:
            orders_qs = orders_qs.filter(c_at__gte=start_date, c_at__lte=end_date)

        response = {
            'period': period,
            'start': start_date,
            'end': end_date,
            # Backwards-compatible top-level totals (requested)
            'total_spent': None,
            'total_profit': None,
            'total_pure_profit': None,
            'waiter_stats': [],
            'inventory_stats': [],
            'order_count': orders_qs.count(),
            'reports': {}
        }
        
        # ... (rest of the method is unchanged) ...
        # (The following code is identical to the original file but included
        # for completeness of the replacement operation)

        # Top-level totals (batch in one aggregation)
        agg_totals = orders_qs.aggregate(
            total_spent=Sum('amount'),
            total_pure_profit=Sum('subamount')
        )
        total_spent = agg_totals['total_spent'] or 0
        total_pure_profit = agg_totals['total_pure_profit'] or 0
        total_profit = (total_spent - total_pure_profit)

        response['total_spent'] = float(total_spent)
        response['total_pure_profit'] = float(total_pure_profit)
        response['total_profit'] = float(total_profit)

        # Waiter stats: batch query (one DB call instead of N+1)
        waiter_order_stats = (
            orders_qs
            .values('user__id', 'user__name')
            .annotate(
                order_count=Count('id'),
                total_spent=Sum('amount')
            )
            .order_by('-total_spent')
        )
        response['waiter_stats'] = [
            {
                'waiter_id': row['user__id'],
                'name': row['user__name'],
                'order_count': row['order_count'],
                'total_spent': float(row['total_spent'] or 0)
            }
            for row in waiter_order_stats
        ]

        # Inventory stats: batch query for used quantities (one DB call)
        inventory_usage_stats = (
            InventoryUsage.objects
            .filter(order_item__order__in=orders_qs)
            .values('inventory__id', 'inventory__name')
            .annotate(total_used=Sum('used_quantity'))
        )
        usage_map = {row['inventory__id']: row['total_used'] or 0 for row in inventory_usage_stats}
        
        # Fetch all inventory with minimal fields
        all_inventory = Inventory.objects.only('id', 'name', 'quantity')
        response['inventory_stats'] = [
            {
                'inventory_id': inv.id,
                'name': inv.name,
                'used_quantity': float(usage_map.get(inv.id, 0)),
                'remaining_quantity': float(inv.quantity)
            }
            for inv in all_inventory
        ]

        # Consolidated summary
        if 'consolidated_summary' in reports:
            gross_sales = OrderItem.objects.filter(order__in=orders_qs).annotate(
                line_total=F('quantity') * F('menu_item__price')
            ).aggregate(total=Sum('line_total'))['total'] or 0

            # Commission/profit derived from order.amount - order.subamount
            commission_total = orders_qs.aggregate(total=Sum(F('amount') - F('subamount')))['total'] or 0

            # Order item stats (total count)
            total_order_items = OrderItem.objects.count()
            # Menu item stats (total count)
            total_menu_items = MenuItem.objects.count()
            # Inventory stats (total count)
            total_inventory_items = Inventory.objects.count()
            # Table stats (total count)
            total_tables = Table.objects.count()
            # Order stats (total count)
            total_orders = Order.objects.count()

            response['reports']['consolidated_summary'] = {
                'gross_sales': float(gross_sales),
                'commission_total': float(commission_total),
                'order_count': orders_qs.count(),
                'total_order_items': total_order_items,
                'total_menu_items': total_menu_items,
                'total_inventory_items': total_inventory_items,
                'total_tables': total_tables,
                'total_orders': total_orders,
            }

        # Revenue by category
        if 'revenue_by_category' in reports:
            rev_by_cat_qs = (
                OrderItem.objects
                .filter(order__in=orders_qs)
                .values('menu_item__category')
                .annotate(total_revenue=Sum(F('quantity') * F('menu_item__price')))
                .order_by('menu_item__category')
            )
            response['reports']['revenue_by_category'] = [
                {'category': r['menu_item__category'] or 'Unspecified', 'total_revenue': float(r['total_revenue'] or 0)}
                for r in rev_by_cat_qs
            ]

        # Hourly revenue
        if 'hourly_revenue' in reports:
            from django.db.models.functions import TruncHour
            hourly = (
                OrderItem.objects
                .filter(order__in=orders_qs)
                .annotate(hour=TruncHour('order__c_at'))
                .values('hour')
                .annotate(total=Sum(F('quantity') * F('menu_item__price')))
                .order_by('hour')
            )
            response['reports']['hourly_revenue'] = [
                {'hour': r['hour'], 'total_revenue': float(r['total'] or 0)} for r in hourly
            ]

        # Revenue by waiter
        if 'revenue_by_waiter' in reports:
            User = get_user_model()
            rev_by_waiter = (
                orders_qs
                .values('user__id', 'user__name')
                .annotate(total_revenue=Sum('amount'))
                .order_by('-total_revenue')
            )
            response['reports']['revenue_by_waiter'] = [
                {'waiter_id': r['user__id'], 'name': r['user__name'], 'total_revenue': float(r['total_revenue'] or 0)}
                for r in rev_by_waiter
            ]

        # Open orders by dining hall (non-completed)
        if 'open_orders_by_hall' in reports:
            open_orders = (
                orders_qs
                .exclude(order_status='completed')
                .values('table__location')
                .annotate(open_count=Count('id'), total_subamount=Sum('subamount'))
                .order_by('table__location')
            )
            response['reports']['open_orders_by_hall'] = [
                {
                    'hall': r['table__location'] or 'Unspecified',
                    'open_orders_count': r['open_count'],
                    'open_orders_subtotal': float(r['total_subamount'] or 0),
                }
                for r in open_orders
            ]

        # Dish consumption (quantity per menu item)
        if 'dish_consumption' in reports:
            dish_cons = (
                OrderItem.objects
                .filter(order__in=orders_qs)
                .values('menu_item__id', 'menu_item__name', 'menu_item__category')
                .annotate(total_quantity=Sum('quantity'))
                .order_by('-total_quantity')
            )
            response['reports']['dish_consumption'] = [
                {
                    'menu_item_id': r['menu_item__id'],
                    'name': r['menu_item__name'],
                    'category': r['menu_item__category'],
                    'total_quantity': float(r['total_quantity'] or 0),
                }
                for r in dish_cons
            ]

        # Dish sales (revenue per menu item)
        if 'dish_sales' in reports:
            dish_sales_qs = (
                OrderItem.objects
                .filter(order__in=orders_qs)
                .values('menu_item__id', 'menu_item__name')
                .annotate(total_revenue=Sum(F('quantity') * F('menu_item__price')))
                .order_by('-total_revenue')
            )
            response['reports']['dish_sales'] = [
                {
                    'menu_item_id': r['menu_item__id'],
                    'name': r['menu_item__name'],
                    'total_revenue': float(r['total_revenue'] or 0),
                }
                for r in dish_sales_qs
            ]

        # Inventory usage
        if 'inventory_usage' in reports:
            inv_usage_qs = (
                InventoryUsage.objects
                .filter(order_item__order__in=orders_qs)
                .values('inventory__id', 'inventory__name')
                .annotate(total_used=Sum('used_quantity'))
                .order_by('-total_used')
            )
            response['reports']['inventory_usage'] = [
                {
                    'inventory_id': r['inventory__id'],
                    'name': r['inventory__name'],
                    'total_used': float(r['total_used'] or 0),
                }
                for r in inv_usage_qs
            ]

        return Response(response)
