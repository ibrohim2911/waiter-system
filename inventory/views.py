# inventory/views.py
from rest_framework import viewsets, permissions
from .models import Inventory, Table, InventoryUsage, MenuItemIngredient
from .serializers import (
    InventorySerializer,
    TableSerializer,
    InventoryUsageSerializer,
    MenuItemIngredientSerializer
)

class TableViewSet(viewsets.ModelViewSet):
    """ API endpoint for Tables """
    queryset = Table.objects.all().order_by('name')
    serializer_class = TableSerializer
    # Permissions: Example - Any authenticated user can manage tables
    permission_classes = [permissions.IsAuthenticated]

class InventoryViewSet(viewsets.ModelViewSet):
    """ API endpoint for Inventory items """
    queryset = Inventory.objects.all().order_by('name')
    serializer_class = InventorySerializer
    # Permissions: Example - Only admin users can manage inventory
    permission_classes = [permissions.IsAuthenticated]

class InventoryUsageViewSet(viewsets.ReadOnlyModelViewSet):
    """ API endpoint for viewing inventory usage (read-only) """
    queryset = InventoryUsage.objects.all().order_by('-c_at')
    serializer_class = InventoryUsageSerializer
    # Permissions: Example - Only admin users can view usage
    permission_classes = [permissions.IsAdminUser]

class MenuItemIngredientViewSet(viewsets.ModelViewSet):
    """ API endpoint for managing ingredients linked to menu items """
    queryset = MenuItemIngredient.objects.all()
    serializer_class = MenuItemIngredientSerializer
    # Permissions: Example - Only admin users can manage ingredients
    permission_classes = [permissions.IsAdminUser]
