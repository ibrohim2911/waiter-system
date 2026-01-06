from django.contrib import admin
from .models import Order, MenuItem, OrderItem, Reservations
from unfold.admin import ModelAdmin

@admin.register(Order)
class OrderAdmin(ModelAdmin):
    list_display = ('id', 'user', 'order_status', 'subamount', 'amount', 'c_at')
    list_filter = ('order_status', 'c_at')
    search_fields = ('user__username',)


@admin.register(MenuItem)
class MenuItemAdmin(ModelAdmin):
    list_display = ('name', 'category', 'price', 'is_available', 'is_frequent')
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
