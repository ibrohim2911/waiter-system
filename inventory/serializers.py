# inventory/serializers.py
from rest_framework import serializers
# Import all relevant models from this app
from .models import Inventory, Table, InventoryUsage, MenuItemIngredient
# Import serializers from other apps if needed for nesting (e.g., OrderItem)
# from order.serializers import OrderItemSerializer # Example if needed

# --- Table Serializer ---
class TableSerializer(serializers.ModelSerializer):
    class Meta:
        model = Table
        fields = ['id', 'name', 'location', 'capacity', 'is_available']
        # No read_only fields needed here unless specific fields shouldn't be API-editable

# --- Inventory Serializer ---
class InventorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Inventory
        fields = ['id', 'name', 'quantity', 'unit_of_measure', 'description', 'price', 'c_at', 'u_at']
        read_only_fields = ['c_at', 'u_at'] # Creation/Update times managed by Django

# --- InventoryUsage Serializer ---
class InventoryUsageSerializer(serializers.ModelSerializer):
    # Optional: Add human-readable related fields for GET requests
    inventory_name = serializers.CharField(source='inventory.name', read_only=True)
    # Showing the OrderItem might require importing its serializer or just showing its ID/string representation
    # order_item_info = OrderItemSerializer(source='order_item', read_only=True) # Option 1: Nested Serializer (Requires order.serializers import)
    order_item_id = serializers.PrimaryKeyRelatedField(source='order_item', read_only=True) # Option 2: Just the ID

    class Meta:
        model = InventoryUsage
        fields = [
            'id',
            'inventory',      # FK ID (writable for create/update)
            'inventory_name', # Added readable field
            'order_item',     # FK ID (writable for create/update)
            'order_item_id',  # Added readable field (ID)
            # 'order_item_info', # Use if choosing Option 1 above
            'used_quantity',
            'c_at'
        ]
        # Make fields managed by signals/backend read-only
        read_only_fields = ['c_at'] # Usage record creation time

# --- MenuItemIngredient Serializer ---
class MenuItemIngredientSerializer(serializers.ModelSerializer):
    # Optional: Add human-readable related fields for GET requests
    inventory_name = serializers.CharField(source='inventory.name', read_only=True)
    menu_item_name = serializers.CharField(source='menu_item.name', read_only=True)

    class Meta:
        model = MenuItemIngredient
        fields = [
            'id',
            'menu_item',      # FK ID (writable)
            'menu_item_name', # Added readable field
            'inventory',      # FK ID (writable)
            'inventory_name', # Added readable field
            'quantity'
        ]
        # No specific read_only fields needed here unless intended
