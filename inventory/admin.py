from django.contrib import admin
from .models import Inventory, InventoryUsage, Table, MenuItemIngredient

@admin.register(Inventory)
class InventoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'quantity', 'unit_of_measure', 'price')
    list_filter = ('unit_of_measure',)
    search_fields = ('name', 'description')

@admin.register(Table)
class TableAdmin(admin.ModelAdmin):
    list_display = ('name', 'location', 'capacity', 'is_available')
    list_filter = ('location', 'is_available')
    search_fields = ('name',)

@admin.register(InventoryUsage)
class InventoryUsageAdmin(admin.ModelAdmin):
    list_display = ('inventory', 'order_item', 'used_quantity', 'c_at')
    list_filter = ('inventory', 'order_item')
    search_fields = ('inventory__name', 'order_item__menu_item__name') # added double underscore lookups to improve searching

@admin.register(MenuItemIngredient)
class MenuItemIngredientAdmin(admin.ModelAdmin):
    list_display = ('menu_item', 'inventory', 'quantity')
    list_filter = ('menu_item', 'inventory')

