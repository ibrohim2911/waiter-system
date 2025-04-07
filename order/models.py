from django.db import models
from inventory.models import Table, Inventory, InventoryUsage
from django.core.exceptions import ValidationError
from django.db.models import F
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver

ORDER_STATUS_CHOICES = [
    ('pending', 'Pending'),
    ('processing', 'Processing'),
    ('completed', 'Completed'),
    ('cancelled', 'Cancelled'),
]

MENU_CATEGORY_CHOICES = [
    ('appetizers', 'Appetizers'),
    ('mains', 'Mains'),
    ('desserts', 'Desserts'),
    ('drinks', 'Drinks'),
]

class Order(models.Model):
    user = models.ForeignKey('user.User', on_delete=models.SET_NULL, null=True)
    order_status = models.CharField(max_length=100, choices=ORDER_STATUS_CHOICES, default='pending')
    amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    c_at = models.DateTimeField(auto_now_add=True)
    u_at = models.DateTimeField(auto_now=True)
    table = models.ForeignKey(Table, on_delete=models.SET_NULL, null=True)

    def __str__(self):
        return f"Order ID: {self.id}, Status: {self.order_status}"
    
    def calculate_order_total(self):
        total = 0
        for item in self.order_items.all():
            total += item.get_total_item_amount()
        self.amount = total
        self.save()
        return self.amount

class MenuItem(models.Model):
    name = models.CharField(max_length=255, unique=True)
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
    c_at = models.DateTimeField(auto_now_add=True)
    u_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Order Item: {self.menu_item.name} (Order: {self.order.id})"

    def get_total_item_amount(self):
        return self.quantity * self.menu_item.price
    
    

class Reservations(models.Model):
    user = models.ForeignKey('user.User', on_delete=models.SET_NULL, null=True)
    reservation_time = models.DateTimeField()
    amount_of_customers = models.PositiveIntegerField()
    status = models.CharField(max_length=100, choices=ORDER_STATUS_CHOICES, default='pending')
    c_at = models.DateTimeField(auto_now_add=True)
    u_at = models.DateTimeField(auto_now=True)
    table = models.ForeignKey(Table, on_delete=models.SET_NULL, null=True)

    def __str__(self):
        return f"Reservation for {self.amount_of_customers} at {self.reservation_time} by {self.user}"

@receiver(post_save, sender=OrderItem)
def order_item_post_save(sender, instance, created, **kwargs):
    """
    This signal is triggered after an OrderItem is saved.
    """
    if created:
        _reduce_inventory(instance)
    else:
        try:
            old_item = OrderItem.objects.get(pk=instance.pk)
            quantity_diff = instance.quantity - old_item.quantity
            _adjust_inventory(instance, quantity_diff)
        except OrderItem.DoesNotExist:
            pass
@receiver(post_delete, sender=OrderItem)
def order_item_post_delete(sender, instance, **kwargs):
    """
    This signal is triggered after an OrderItem is deleted.
    """
    _increase_inventory(instance)

@receiver(post_save, sender=Order)
def order_post_save(sender, instance, created, **kwargs):
    """
    This signal is triggered after an Order is saved.
    If the order status changed to 'cancelled', it restores the inventory.
    """
    if not created:
        try:
            old_order = Order.objects.get(pk=instance.pk)
            if old_order.order_status != instance.order_status and instance.order_status == 'cancelled':
                # Order status changed to cancelled
                for order_item in instance.order_items.all():
                    related_inventories = Inventory.objects.all()  # Replace with actual related inventory logic
                    for inventory in related_inventories:
                        inventory.increase_quantity(order_item.quantity)
                        InventoryUsage.objects.filter(inventory=inventory, order_item=order_item).delete()
        except Order.DoesNotExist:
            pass

def _reduce_inventory(order_item):
    """Reduces the inventory based on the menu item and quantity."""
    for ingredient in order_item.menu_item.ingredients.all():
        try:
            ingredient.inventory.reduce_quantity(order_item.quantity * ingredient.quantity)
            # Create an InventoryUsage record
            InventoryUsage.objects.create(inventory=ingredient.inventory, order_item=order_item, used_quantity=order_item.quantity* ingredient.quantity)
        except ValidationError as e:
            # Handle insufficient inventory
            raise ValidationError(f"Insufficient inventory for {ingredient.inventory.name}: {e}")
    
def _adjust_inventory(order_item, quantity_diff):
    for ingredient in order_item.menu_item.ingredients.all():
        try:
            if quantity_diff > 0:
                ingredient.inventory.reduce_quantity(quantity_diff * ingredient.quantity)
                InventoryUsage.objects.create(inventory=ingredient.inventory, order_item=order_item, used_quantity=quantity_diff*ingredient.quantity)
            elif quantity_diff < 0:
                ingredient.inventory.increase_quantity(abs(quantity_diff) * ingredient.quantity)
                usage = InventoryUsage.objects.filter(inventory=ingredient.inventory, order_item=order_item).first()
                if usage:
                    usage.used_quantity = F('used_quantity') - (abs(quantity_diff)*ingredient.quantity)
                    usage.save()
        except ValidationError as e:
            raise ValidationError(f"Insufficient inventory for {ingredient.inventory.name}: {e}")
    
def _increase_inventory(order_item):
    """Restores inventory when OrderItem is deleted"""
    for ingredient in order_item.menu_item.ingredients.all():
        ingredient.inventory.increase_quantity(order_item.quantity * ingredient.quantity)
        InventoryUsage.objects.filter(inventory=ingredient.inventory, order_item=order_item).delete()
