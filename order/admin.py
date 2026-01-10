from django.contrib import admin
from .models import Order, MenuItem, OrderItem, Reservations, Printer, PrintJob
from unfold.admin import ModelAdmin
@admin.register(Printer)
class PrinterAdmin(ModelAdmin):
    list_display = ('name', 'ip_address', 'port', 'is_cashier_printer', 'is_enabled')
    search_fields = ('name', 'ip_address')
@admin.register(PrintJob)
class PrintJobAdmin(ModelAdmin):
    list_display = ('id', 'printer', 'status', 'c_at')
    list_filter = ('status', 'c_at')
    search_fields = ('printer__name',)
@admin.register(Order)
class OrderAdmin(ModelAdmin):
    list_display = ('id', 'user', 'order_status', 'subamount', 'amount', 'c_at')
    list_filter = ('order_status', 'c_at')
    search_fields = ('user__username',)


@admin.register(MenuItem)
class MenuItemAdmin(ModelAdmin):
    list_display = ('name', 'category', 'price', 'is_available', 'is_frequent',"printer")
    list_filter = ('category', 'is_available', 'is_frequent')
    search_fields = ('name', 'description')

@admin.register(OrderItem)
class OrderItemAdmin(ModelAdmin):
    list_display = ('order', 'menu_item', 'quantity')
    list_filter = ('order', 'menu_item')


@admin.register(Reservations)
class ReservationsAdmin(ModelAdmin):
    list_display = ('user', 'reservation_time', 'amount_of_customers', 'status', 'c_at')
    list_filter = ('status', 'reservation_time')
    search_fields = ('user__username',)
