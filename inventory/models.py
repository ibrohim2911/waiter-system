from django.db import models
from django.core.exceptions import ValidationError
from django.db.models.signals import post_save
from django.dispatch import receiver

class Inventory(models.Model):
    UNIT_OF_MEASURE_CHOICES = [
        ('kg', 'Kilogram'),
        ('g', 'Gram'),
        ('l', 'Liter'),
        ('ml', 'Milliliter'),
        ('pcs', 'Pieces'),
    ]

    name = models.CharField(max_length=255)
    quantity = models.DecimalField(max_digits=10, decimal_places=2)
    unit_of_measure = models.CharField(max_length=50, choices=UNIT_OF_MEASURE_CHOICES)
    description = models.TextField(blank=True, null=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    c_at = models.DateTimeField(auto_now_add=True)
    u_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

    def reduce_quantity(self, amount):
        if self.quantity >= amount:
            self.quantity -= amount
            self.save()
        else:
            raise ValidationError(f"Not enough {self.name} in stock. Available: {self.quantity}, Requested: {amount}")

    def increase_quantity(self, amount):
        self.quantity += amount
        self.save()
    
    def is_out_of_stock(self):
        return self.quantity == 0

class InventoryUsage(models.Model):
    inventory = models.ForeignKey(Inventory, on_delete=models.CASCADE)
    order_item = models.ForeignKey('order.OrderItem', on_delete=models.CASCADE)
    used_quantity = models.DecimalField(max_digits=10, decimal_places=2)
    c_at = models.DateTimeField(auto_now_add=True)
    u_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Usage of {self.inventory.name} - Quantity: {self.used_quantity}"

TABLE_LOCATION_CHOICES = [
    ('indoor', 'Indoor'),
    ('outdoor', 'Outdoor'),
    ('patio', 'Patio'),
]

class Table(models.Model):
    name = models.CharField(max_length=100)
    location = models.CharField(max_length=100, choices=TABLE_LOCATION_CHOICES)
    capacity = models.PositiveIntegerField()
    is_available = models.BooleanField(default=True)

class MenuItemIngredient(models.Model):
    menu_item = models.ForeignKey('order.MenuItem', on_delete=models.CASCADE, related_name='ingredients')
    inventory = models.ForeignKey(Inventory, on_delete=models.PROTECT)
    quantity = models.DecimalField(max_digits=10, decimal_places=2)
    
    def __str__(self):
        return f"{self.quantity} of {self.inventory.name} for {self.menu_item.name}"

@receiver(post_save, sender=Inventory)
def inventory_post_save(sender, instance, created, **kwargs):
    """
    This signal is triggered after an Inventory item is saved.
    """
    if instance.is_out_of_stock():
        # Inventory is out of stock
        for ingredient in instance.menuitemingredient_set.all():
            ingredient.menu_item.is_available = False
            ingredient.menu_item.save()
    else:
        # Inventory is in stock
        for ingredient in instance.menuitemingredient_set.all():
            ingredient.menu_item.is_available = True
            ingredient.menu_item.save()
#check table and reservations are working correctly i mean when someone uses table for order meanwhile other should be able to use it to reservations but not for ordering