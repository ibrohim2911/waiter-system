from django.db import models

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

class InventoryUsage(models.Model):
    inventory = models.ForeignKey(Inventory, on_delete=models.CASCADE)
    order_item = models.ForeignKey('order.OrderItem', on_delete=models.CASCADE) #renamed order_item_id to order_item
    used_quantity = models.DecimalField(max_digits=10, decimal_places=2)
    c_at = models.DateTimeField(auto_now_add=True)
    u_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Usage of {self.inventory.name} - Quantity: {self.used_quantity}"

