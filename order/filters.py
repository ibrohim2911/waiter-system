
from django_filters import rest_framework as filters
from .models import Order

class OrderFilter(filters.FilterSet):
    order_status = filters.BaseInFilter(field_name='order_status', lookup_expr='in')
    table__location = filters.BaseInFilter(field_name='table__location', lookup_expr='in')
    user = filters.BaseInFilter(field_name='user', lookup_expr='in')
    class Meta:
        model = Order
        fields = ['order_status', 'table__location', 'user']