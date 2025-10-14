# order/serializers.py
from django.db import transaction
from rest_framework import serializers
# Import all relevant models from this app
from .models import Order, OrderItem, MenuItem, Reservations, InventoryUsage
# Import serializers from other apps
from inventory.serializers import (
    TableSerializer,
    InventorySerializer,
    MenuItemIngredientSerializer # Ensure this is defined in inventory.serializers
)
# Import UserSerializer (ensure it exists and is correct)
try:
    # Assuming user app is correctly structured
    from user.serializers import UserSerializer
except ImportError:
    UserSerializer = None # Handle case where it might not exist yet


# --- MenuItem Serializer ---
class MenuItemSerializer(serializers.ModelSerializer):
    # Nest the ingredients using the serializer we defined in inventory.serializers
    # Keep read_only=True if ingredients are managed via MenuItemIngredient endpoint
    ingredients = MenuItemIngredientSerializer(many=True, read_only=True)

    class Meta:
        model = MenuItem
        fields = [
            'id',
            'name',
            'description',
            'price',
            'category',
            'is_available',
            'is_frequent',
            'ingredients',
            'c_at',
            'u_at'
        ]
        # is_available is determined by inventory levels via signal
        read_only_fields = ['is_available', 'c_at', 'u_at']


class OrderItemSerializer(serializers.ModelSerializer):
    item_name = serializers.CharField(source='menu_item.name', read_only=True)
    item_price = serializers.DecimalField(source='menu_item.price', read_only=True, max_digits=10, decimal_places=2)

    class Meta:
        model = OrderItem
        fields = ['id', 'order', 'menu_item', 'item_name', 'item_price', 'quantity']
        # The inventory validation and reduction logic has been moved to a post_save signal
        # on the OrderItem model (order/models.py). This ensures the logic is applied
        # consistently for both creates and updates, from any source (API, admin, etc.).
class OrderSerializer(serializers.ModelSerializer):
    # Keep items read-only here; manage OrderItems via OrderItemViewSet
    items = OrderItemSerializer(many=True, read_only=True, source='order_items')
    table_details = TableSerializer(source='table', read_only=True)
    user_name = serializers.CharField(source='user.name', read_only=True)

    # 'user' field will be automatically set based on request.user in the ViewSet
    # 'table' field allows linking to a table (ID)
    # 'order_status' allows setting the status

    class Meta:
        model = Order
        fields = [
            'id',
            'table',          # Writable FK ID
            'table_details',  # Read-only nested details
            'user',           # Read-only (set automatically)
            'user_name',      # Read-only derived name
            'c_at',
            'u_at',
            'order_status',   # Writable status
            'items',          # Read-only nested items
            'subamount',      # Read-only calculated subtotal
            'amount',         # Read-only calculated total with commission
        ]
        # Fields managed by backend or derived
        read_only_fields = ['user', 'c_at', 'u_at', 'subamount', 'amount']


# --- Reservations Serializer ---
class ReservationsSerializer(serializers.ModelSerializer):
    # Optional nested details for related objects
    table_details = TableSerializer(source='table', read_only=True)
    # Define user_details conditionally based on UserSerializer import
    user_details = UserSerializer(source='user', read_only=True) if UserSerializer else None

    class Meta:
        model = Reservations
        # Start with the base list of fields
        _fields = [
            'id',
            'user',             # Read-only (set automatically)
            # 'user_details' will be inserted here conditionally
            'reservation_time', # Writable
            'amount_of_customers',# Writable
            'status',           # Writable
            'table',            # Writable FK ID
            'table_details',    # Read-only nested details
            'c_at',
            'u_at'
        ]
        # CORRECTED: Check if UserSerializer was successfully imported
        if UserSerializer:
            # Insert 'user_details' into the list if the serializer exists
            # This refers to the *name* of the field defined above
            _fields.insert(_fields.index('user') + 1, 'user_details')

        fields = _fields # Assign the final list
        read_only_fields = ['user', 'c_at', 'u_at'] # User set automatically