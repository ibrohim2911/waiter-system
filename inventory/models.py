# c:\Users\User\Desktop\waiter-system\inventory\models.py
import decimal
from django.db import models, transaction
from django.db.models import F
from django.core.exceptions import ValidationError
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.conf import settings

User = settings.AUTH_USER_MODEL

class Table(models.Model):
    name = models.CharField(max_length=100)
    location = models.CharField(max_length=100, blank=True)
    capacity = models.PositiveIntegerField()
    is_available = models.BooleanField(default=True)
    commission = models.DecimalField(max_digits=5, decimal_places=2, default=decimal.Decimal('10.00'))  # Commission percentage
    # Assuming migrations for c_at/u_at are now fixed:
    # c_at = models.DateTimeField(auto_now_add=True)
    # u_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.name} (Capacity: {self.capacity})"

class Inventory(models.Model):
    name = models.CharField(max_length=255, unique=True)
    quantity = models.DecimalField(max_digits=10, decimal_places=2, default=decimal.Decimal('0.00'))
    unit_of_measure = models.CharField(max_length=50)
    description = models.TextField(blank=True, null=True)
    price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    c_at = models.DateTimeField(auto_now_add=True)
    u_at = models.DateTimeField(auto_now=True)
    bprice = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)  # Buying price
    supplier = models.CharField(max_length=255, blank=True, null=True)
    supplier_contact = models.CharField(max_length=255, blank=True, null=True)
    category = models.CharField(max_length=100, blank=True, null=True)  # Category for inventory items
    def __str__(self):
        return self.name

    def reduce_quantity(self, quantity_to_reduce):
        """Reduces the quantity atomically, ensuring it doesn't go below zero."""
        quantity_to_reduce = decimal.Decimal(str(quantity_to_reduce))
        if quantity_to_reduce <= 0:
            return

        # Use an atomic update to prevent race conditions.
        updated_rows = Inventory.objects.filter(
            pk=self.pk,
            quantity__gte=quantity_to_reduce
        ).update(quantity=F('quantity') - quantity_to_reduce)

        if updated_rows == 0:
            # Refresh to get the actual current quantity for the error message.
            self.refresh_from_db(fields=['quantity'])
            raise ValidationError(f"Insufficient stock for {self.name}. Available: {self.quantity}, Required: {quantity_to_reduce}")

        # Refresh the instance's quantity to match the database.
        self.refresh_from_db(fields=['quantity'])

    def increase_quantity(self, quantity_to_increase):
        """Increases the quantity atomically."""
        quantity_to_increase = decimal.Decimal(str(quantity_to_increase))
        if quantity_to_increase <= 0:
            return

        Inventory.objects.filter(pk=self.pk).update(quantity=F('quantity') + quantity_to_increase)
        self.refresh_from_db(fields=['quantity'])

    def is_out_of_stock(self):
        """Checks if quantity is zero or less."""
        # Refresh from DB before check for maximum accuracy within signals/methods
        # self.refresh_from_db(fields=['quantity']) # Optional: uncomment if needed, but might add overhead
        return self.quantity <= decimal.Decimal('0.00')


# --- MenuItemIngredient, InventoryUsage --- (Unchanged)
class MenuItemIngredient(models.Model):
    menu_item = models.ForeignKey('order.MenuItem', on_delete=models.CASCADE, related_name='ingredients')
    inventory = models.ForeignKey(Inventory, on_delete=models.CASCADE, related_name='used_in')
    quantity = models.DecimalField(max_digits=10, decimal_places=3)
    class Meta:
        unique_together = ('menu_item', 'inventory')
    def __str__(self):
        menu_item_name = getattr(getattr(self, 'menu_item', None), 'name', 'N/A')
        inventory_name = getattr(getattr(self, 'inventory', None), 'name', 'N/A')
        return f"{self.quantity} of {inventory_name} for {menu_item_name}"

class InventoryUsage(models.Model):
    inventory = models.ForeignKey(Inventory, on_delete=models.CASCADE, related_name='usage_records')
    order_item = models.ForeignKey('order.OrderItem', on_delete=models.CASCADE, related_name='inventory_usage')
    used_quantity = models.DecimalField(max_digits=10, decimal_places=3)
    c_at = models.DateTimeField(auto_now_add=True)
    def __str__(self):
        inventory_name = getattr(getattr(self, 'inventory', None), 'name', 'N/A')
        order_item_id = getattr(self, 'order_item_id', 'N/A')
        return f"{self.used_quantity} of {inventory_name} used by OrderItem {order_item_id}"


@receiver(post_save, sender=Inventory)
def inventory_post_save_check_menu_item_availability(sender, instance, created, **kwargs):
    """
    Updates the availability of related MenuItems based on the stock
    status of ALL their required ingredients.
    """
    try:
        from order.models import MenuItem
    except ImportError:
        print("Warning: Could not import MenuItem in inventory signal.")
        return

    # Get links where the SAVED inventory item ('instance') is used
    related_ingredient_links = MenuItemIngredient.objects.filter(inventory=instance).select_related('menu_item')
    menu_items_to_check = set(link.menu_item for link in related_ingredient_links if link.menu_item)

    print(f"\nSignal triggered by Inventory: {instance.name} (ID: {instance.pk}), New Qty: {instance.quantity}") # Debug
    print(f"Checking MenuItems: {[mi.name for mi in menu_items_to_check]}") # Debug

    for menu_item in menu_items_to_check:
        all_ingredients_available = True
        print(f"  Checking MenuItem: {menu_item.name} (Current is_available: {menu_item.is_available})") # Debug
        # Check ALL ingredients required for this menu_item
        for required_ingredient_link in menu_item.ingredients.all().select_related('inventory'):
            inventory_item_to_check = required_ingredient_link.inventory
            required_qty_for_menu_item = required_ingredient_link.quantity # Qty needed for ONE menu item

            # --- Potential Point of Failure ---
            # Use the 'instance' directly if it's the item being checked,
            # otherwise refresh the related item. This ensures we use the
            # most up-to-date quantity for the item that triggered the signal.
            current_inventory_quantity = decimal.Decimal('0.00')
            if inventory_item_to_check.pk == instance.pk:
                current_inventory_quantity = instance.quantity # Use the saved instance's quantity
                print(f"    Using 'instance' for {inventory_item_to_check.name}: Qty={current_inventory_quantity}") # Debug
            else:
                # Refresh other ingredients from DB
                try:
                     inventory_item_to_check.refresh_from_db(fields=['quantity'])
                     current_inventory_quantity = inventory_item_to_check.quantity
                     print(f"    Refreshed {inventory_item_to_check.name}: Qty={current_inventory_quantity}") # Debug
                except Exception as e:
                     print(f"    Warning: Could not refresh inventory item {inventory_item_to_check.pk} in signal: {e}")
                     all_ingredients_available = False # Assume unavailable if refresh fails
                     break

            # Check if stock is sufficient for AT LEAST ONE menu item
            # (is_out_of_stock checks <= 0, but we need >= required_qty_for_menu_item)
            # FIX: Check if current quantity is less than required quantity
            if current_inventory_quantity < required_qty_for_menu_item:
                print(f"    -> {inventory_item_to_check.name} is INSUFFICIENT (Need: {required_qty_for_menu_item}, Have: {current_inventory_quantity})") # Debug
                all_ingredients_available = False
                break # No need to check further for this menu item
            else:
                 print(f"    -> {inventory_item_to_check.name} is SUFFICIENT (Need: {required_qty_for_menu_item}, Have: {current_inventory_quantity})") # Debug


        print(f"  Result for {menu_item.name}: all_ingredients_available = {all_ingredients_available}") # Debug
        # Update menu_item availability only if it changed
        if menu_item.is_available != all_ingredients_available:
            menu_item.is_available = all_ingredients_available
            menu_item.save(update_fields=['is_available'])
            print(f"  SAVED MenuItem '{menu_item.name}' availability set to {all_ingredients_available}") # Debug
        else:
             print(f"  MenuItem '{menu_item.name}' availability unchanged ({menu_item.is_available}).") # Debug
