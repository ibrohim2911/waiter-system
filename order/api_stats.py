
from rest_framework.views import APIView
from rest_framework.response import Response
from django.contrib.auth import get_user_model
from rest_framework.permissions import AllowAny
from django.db.models import Count, Q

from drf_yasg.utils import swagger_auto_schema
class OrdersPerUserAndTableView(APIView):
    """
    Returns order counts per user and per table location, excluding orders with status 'completed'.
    """

    permission_classes = [AllowAny]  # Adjust permissions as needed

    @swagger_auto_schema(tags=['Stats'])
    def get(self, request, *args, **kwargs):
        from order.models import Order, OrderItem, MenuItem
        from inventory.models import Inventory, Table
        User = get_user_model()

        # Orders per user (not completed)
        users = User.objects.annotate(
            order_count=Count('orders', filter=Q(orders__order_status__exact=None) | ~Q(orders__order_status='completed'))
        )
        non_completed_orders_per_user = [
            {
                "user_id": user.id,
                "username": getattr(user, "username", str(user)),
                "order_count": Order.objects.filter(user=user).exclude(order_status="completed").count(),
            }
            for user in users
        ]
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
                "all_earned": get_all_earned(),
                

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
