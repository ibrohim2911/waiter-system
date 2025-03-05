from django.contrib import admin
from .models import Order, MenuItem, OrderItem, Reservations

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'order_status', 'amount', 'c_at')
    list_filter = ('order_status', 'c_at')
    search_fields = ('user__username',)


@admin.register(MenuItem)
class MenuItemAdmin(admin.ModelAdmin):
    list_display = ('name', 'category', 'price', 'is_available')
    list_filter = ('category', 'is_available')
    search_fields = ('name', 'description')

@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    list_display = ('order', 'menu_item', 'quantity')
    list_filter = ('order', 'menu_item')


@admin.register(Reservations)
class ReservationsAdmin(admin.ModelAdmin):
    list_display = ('user', 'reservation_time', 'amount_of_customers', 'status', 'c_at')
    list_filter = ('status', 'reservation_time')
    search_fields = ('user__username',)
