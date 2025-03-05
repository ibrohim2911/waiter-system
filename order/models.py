from django.db import models
from django.db.models import Sum


ORDER_STATUS_CHOICES = [
    ('processing', 'Processing'),
    ('completed', 'Completed'),
    ('cancelled', 'Cancelled'),
    # Add other order statuses as needed
]

MENU_CATEGORY_CHOICES = [
    ('appetizers', 'Appetizers'),
    ('mains', 'Mains'),
    ('desserts', 'Desserts'),
    ('drinks', 'Drinks'),
    # Add other menu categories as needed
]

class Order(models.Model):
    user = models.ForeignKey('user.User', on_delete=models.CASCADE) # changed user_id to user
    order_status = models.CharField(max_length=100, choices=ORDER_STATUS_CHOICES, default='prosessing') # added default value
    amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00) # Changed to DecimalField for currency
    c_at = models.DateTimeField(auto_now_add=True)
    u_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Order ID: {self.id}, Status: {self.order_status}"

    


class MenuItem(models.Model):
    name = models.CharField(max_length=255, unique=True) # Added unique=True to prevent duplicate menu item names
    description = models.TextField(blank=True, null=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    category = models.CharField(max_length=100, choices=MENU_CATEGORY_CHOICES)
    is_available = models.BooleanField(default=True)
    c_at = models.DateTimeField(auto_now_add=True)
    u_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name


class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='order_items')
    menu_item = models.ForeignKey(MenuItem, on_delete=models.PROTECT)
    quantity = models.PositiveIntegerField()
    price = models.DecimalField(max_digits=10, decimal_places=2)  # Redundant, get from MenuItem
    c_at = models.DateTimeField(auto_now_add=True)
    u_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Order Item: {self.menu_item.name} (Order: {self.order.id})"

    def get_total_item_amount(self):
        return self.quantity * self.menu_item.price # Get price from MenuItem


class Reservations(models.Model):
    user = models.ForeignKey('user.User', on_delete=models.CASCADE) # changed user_id to user
    reservation_time = models.DateTimeField()
    amount_of_customers = models.PositiveIntegerField()
    status = models.CharField(max_length=100, choices=ORDER_STATUS_CHOICES, default='pending') # added default value, uses same choices as Order
    c_at = models.DateTimeField(auto_now_add=True)
    u_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Reservation for {self.amount_of_customers} at {self.reservation_time} by {self.user}"
