
from rest_framework.views import APIView
from rest_framework.response import Response
from django.contrib.auth import get_user_model
from rest_framework.permissions import AllowAny
from django.db.models import Count, Q, Sum
from drf_yasg import openapi
from datetime import datetime, timedelta
from django.utils.dateparse import parse_datetime
from drf_yasg.utils import swagger_auto_schema
class OrdersPerUserAndTableView(APIView):
    """
    Returns order counts per user and per table location, excluding orders with status 'completed'.
    """

    permission_classes = [AllowAny]  # Adjust permissions as needed

    @swagger_auto_schema(tags=['Stats'],
        manual_parameters=[
                openapi.Parameter('period', openapi.IN_QUERY, description="Time period for stats (day, week, month, custom). Default is 'day'.", type=openapi.TYPE_STRING),
                openapi.Parameter("start_time", openapi.IN_QUERY, description="Start of the time window (ISO 8601 format)", type=openapi.TYPE_STRING, format=openapi.FORMAT_DATETIME),
                openapi.Parameter("end_time", openapi.IN_QUERY, description="End of the time window (ISO 8601 format)", type=openapi.TYPE_STRING, format=openapi.FORMAT_DATETIME),
            ])
    def get(self, request, *args, **kwargs):
        from order.models import Order, OrderItem, MenuItem
        from inventory.models import Inventory, Table
        User = get_user_model()

        # Orders per user (not completed)
        period = request.query_params.get('period', 'day')  # Default to 'day'
        start_time_str = request.query_params.get('start_time')
        end_time_str = request.query_params.get('end_time')
        now = datetime.now()

        # 2. Determine the date range based on the period
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
        else:
            # Default to 'day' if period is invalid or custom params are missing
            start_date = now.replace(hour=0, minute=0, second=0, microsecond=0)
            end_date = now

        # 3. Create a Q object for the time window to use inside annotations
        time_filter = Q()
        if start_date and end_date:
            time_filter = Q(orders__c_at__range=(start_date, end_date))
    
        users = User.objects.annotate(
            order_count=Count('orders', filter=Q(orders__order_status__exact=None) | ~Q(orders__order_status='completed'))
        )
        non_completed_orders_per_user = [
            {
                "user_id": user.id,
                "username": getattr(user, "username", str(user)),
                "order_count": Order.objects.filter(user=user).exclude(order_status="completed").count(),
                "amount": sum(Order.objects.filter(user=user).exclude(order_status="completed").values_list('amount', flat=True)),
            }
            for user in users
        ]
        non_completed_orders = [{
            "order_count": Order.objects.exclude(order_status="completed").count(),
            "amount":sum(Order.objects.exclude(order_status="completed").values_list('amount', flat=True))
        }]
        # for user in users:
        #     for order in Order.objects.filter(user=user, order_status="completed"):
        #         print(order.diff())
        def calculate_earned(user):
            total_earned = 0
            for order in Order.objects.filter(user=user, order_status="completed"):
                total_earned += order.diff()
            return total_earned
        # # print(Order.diff(Order.objects.filter(user__id=2).first()))
        # for order in Order.objects.filter(user__id=2):
        #     print(order.diff())
        # print(sum([order.diff() for order in Order.objects.filter(user__id=2, order_status="completed")]
        users_data = [
            {
            "user_id": user.id,
            "username": getattr(user, "username", str(user)),
            "completed_order_count": Order.objects.filter(user=user, order_status= "completed").count(),
            # make earned field that should add all related and completed orders amount
            "earned": calculate_earned(user),

            } 
        
            for user in users
        ]
        order_items_per_menu = (
            OrderItem.objects
            .values('menu_item__name')
            .annotate(order_item_count=Count('id'))
            .order_by('menu_item__name')
        )
        
        def get_all_earned():
            all_earned = 0
            for user in users:
                for order in Order.objects.filter(user=user, order_status="completed"):
                    all_earned += order.diff()
            return all_earned
            
        
        all_data = [
            {
                "overall_amount_from_commission": get_all_earned(),
                "revenue_with_taxes": sum(Order.objects.filter(order_status="completed").values_list('amount', flat=True)),

            }
            
        ]
        pending_order_per_user = [
            {
                "user_id": user.id,
                "username": getattr(user, "username", str(user)),
                "pending_order_count": Order.objects.filter(user=user, order_status="pending").count(),
                
            }
            for user in users
        ]
        processing_order_per_user = [
            {
                "user_id": user.id,
                'username': getattr(user, 'username', str(user)),
                'processing_order_count': Order.objects.filter(user=user, order_status='processing').count()
            }
            for user in users
        ]


        # Combined: orders per user per location (with status breakdown and amount)
        orders_per_user_per_location = []
        for user in users:
            loc_qs = (
                Order.objects
                .filter(user=user)
                .values('table__location')
                .annotate(
                    total=Count('id'),
                    pending=Count('id', filter=Q(order_status='pending')),
                    processing=Count('id', filter=Q(order_status='processing')),
                    completed=Count('id', filter=Q(order_status='completed')),
                    amount=Sum('amount')
                )
                .order_by('table__location')
            )

            locations = [
                {
                    'location': loc.get('table__location') or 'unknown',
                    'order_count': loc.get('total', 0),
                    'pending_count': loc.get('pending', 0),
                    'processing_count': loc.get('processing', 0),
                    'completed_count': loc.get('completed', 0),
                    'amount': float(loc.get('amount') or 0)
                }
                for loc in loc_qs
            ]

            orders_per_user_per_location.append({
                'user_id': user.id,
                'username': getattr(user, 'username', str(user)),
                'locations': locations,
            })


        # Orders per table location (not completed)
        orders_per_location = (
            Order.objects
            .exclude(order_status='completed')
            .values('table__location')
            .annotate(order_count=Count('id'))
            .order_by('table__location')
        )
        pending_orders_per_location = (
            Order.objects
            .filter(order_status='pending')
            .values('table__location')
            .annotate(order_count=Count('id'))
            .order_by('table__location')
        )
        processing_orders_per_location = (
            Order.objects
            .filter(order_status='processing')
            .values('table__location')
            .annotate(order_count=Count('id'))
            .order_by('table__location')
        )
        locations_data = list(orders_per_location)

        # Order items per menu item
        order_items_per_menu_data = list(order_items_per_menu)

        # Menu item stats
        menu_items = MenuItem.objects.annotate(order_item_count=Count('order_items'))
        menu_items_data = [
            {
                'menu_item_id': item.id,
                'name': item.name,
                'order_item_count': item.order_item_count,
                'is_available': item.is_available
            }
            for item in menu_items
        ]

        # Inventory stats
        inventory_items = Inventory.objects.all()
        inventory_data = [
            {
                'inventory_id': inv.id,
                'name': inv.name,
                'quantity': float(inv.quantity),
                'unit_of_measure': inv.unit_of_measure,
                'category': inv.category
            }
            for inv in inventory_items
        ]

        # Table stats
        tables = Table.objects.annotate(order_count=Count('orders'))
        tables_data = [
            {
                'table_id': t.id,
                'name': t.name,
                'location': t.location,
                'capacity': t.capacity,
                'order_count': t.order_count
            }
            for t in tables
        ]

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

        return Response({
            "period": period,
            "start_date": start_date,
            "end_date": end_date,
            "all_data": all_data,
            "orders_per_user_per_location": orders_per_user_per_location,
            "orders_per_user": non_completed_orders_per_user,
            "pending_order_per_user":pending_order_per_user,
            "processing_order_per_user": processing_order_per_user,
            'orders_per_table_location': locations_data,
            "pending_order_per_location":pending_orders_per_location,
            "processing_order_per_location":processing_orders_per_location,
            'order_items_per_menu_item': order_items_per_menu_data,
            "user_stats":users_data,
            'menu_items': menu_items_data,
            'inventory': inventory_data,
            'tables': tables_data,
            'totals': {
                'orders': total_orders,
                'order_items': total_order_items,
                'menu_items': total_menu_items,
                'inventory_items': total_inventory_items,
                'tables': total_tables
            }
        })
