from django.contrib import admin
from .models import Inventory, InventoryUsage

@admin.register(Inventory)
class InventoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'quantity', 'unit_of_measure', 'price')
    list_filter = ('unit_of_measure',)
    search_fields = ('name', 'description')

@admin.register(InventoryUsage)
class InventoryUsageAdmin(admin.ModelAdmin):
    list_display = ('inventory', 'order_item', 'used_quantity', 'c_at')
    list_filter = ('inventory', 'order_item')
    search_fields = ('inventory__name', 'order_item__menu_item__name') # added double underscore lookups to improve searching
