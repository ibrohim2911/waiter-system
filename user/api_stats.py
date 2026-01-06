
from rest_framework.views import APIView
from rest_framework.response import Response
from django.contrib.auth import get_user_model
from rest_framework.permissions import AllowAny
from django.db.models import Count, Q, Sum, F, DecimalField, Value
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from django.utils.dateparse import parse_datetime
from datetime import datetime, timedelta

from order.models import Order, OrderItem, MenuItem
from inventory.models import Inventory, Table
class UserStatsView(APIView):
    """
    Returns statistics related to users, such as earnings and order counts.
    Supports filtering by a time period using 'period' (day, week, month, alltime)
    or a custom range with 'start_time' and 'end_time'.
    Example: /api/v1/user-stats/?period=week
    """

    permission_classes = [AllowAny]  # Adjust permissions as needed

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
        
        # 1. Get time filters from query params
        period = request.query_params.get('period', 'day')  # Default to 'day'
        start_time_str = request.query_params.get('start_time')
        end_time_str = request.query_params.get('end_time')
        now = datetime.now()

        # 2. Determine the date range based on the period
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
            # For 'alltime', we don't set dates, so no time filter will be applied.
            pass
        else:
            # Default to 'day' if period is invalid
            period = 'day'
            start_date = now.replace(hour=0, minute=0, second=0, microsecond=0)
            end_date = now

        # 3. Create a Q object for the time window to use inside annotations
        time_filter = Q()
        if start_date and end_date:
            time_filter = Q(orders__c_at__range=(start_date, end_date))
    
        # 4. Define the expression for total profit (total_earned)
        profit_expression = Sum(
            F('orders__amount') - F('orders__subamount'),
            filter=time_filter & Q(orders__order_status='completed'),
            output_field=DecimalField(),
            default=Value(0)
        )

        # 5. Use annotations to calculate all stats in a single, efficient query
        user_stats = User.objects.annotate(
            # Calculate total profit
            total_earned=profit_expression,
            # Calculate the 'earned' field as 40% of the total profit
            earned=profit_expression * Value(0.40, output_field=DecimalField()),
            # Count completed orders within the time window
            completed_order_count=Count('orders', filter=time_filter & Q(orders__order_status='completed')),
            # Count non-completed orders within the time window
            non_completed_order_count=Count('orders', filter=time_filter & ~Q(orders__order_status='completed'))
        ).values(
            'id', 'name', 'phone_number', 'role', 'total_earned', 'earned',
            'completed_order_count', 'non_completed_order_count'
        )

        response_data = {
            'period': period,
            'start_date': start_date,
            'end_date': end_date,
            # Filter out users who have no stats in the given period to avoid clutter
            "user_stats": [
                user for user in user_stats 
                if user['completed_order_count'] > 0 or user['non_completed_order_count'] > 0
            ]
        }
        return Response(response_data)
