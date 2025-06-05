# c:\Users\User\Desktop\waiter-system\order\models.py
import decimal # Import decimal
from django.db import models, transaction
# Ensure all necessary models are imported
from inventory.models import Table, Inventory, InventoryUsage, MenuItemIngredient
from django.core.exceptions import ValidationError
from django.db.models import F
from django.db.models.signals import post_save, post_delete, pre_delete
from django.dispatch import receiver
from django.conf import settings

User = settings.AUTH_USER_MODEL

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

RESERVATION_STATUS_CHOICES = [
    ('pending', 'Pending'),
    ('confirmed', 'Confirmed'),
    ('seated', 'Seated'),
    ('cancelled', 'Cancelled'),
    ('no_show', 'No Show'),
]

class Order(models.Model):
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='orders')
    order_status = models.CharField(max_length=100, choices=ORDER_STATUS_CHOICES, default='pending')
    amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    c_at = models.DateTimeField(auto_now_add=True)
    u_at = models.DateTimeField(auto_now=True)
    table = models.ForeignKey(Table, on_delete=models.SET_NULL, null=True, blank=True, related_name='orders')

    def __str__(self):
        return f"Order ID: {self.id}, Status: {self.order_status}"

    def calculate_order_total(self):
        """Calculates total based on associated order items."""
        total = decimal.Decimal('0.00') # Initialize as Decimal
        for item in self.order_items.all():
             total += item.get_total_item_amount()

        # Update only if the amount changed to avoid unnecessary saves/signal triggers
        if self.amount != total:
            self.amount = total
            self.save(update_fields=['amount'])
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
    menu_item = models.ForeignKey(MenuItem, on_delete=models.PROTECT, related_name='order_items')
    quantity = models.PositiveIntegerField()
    c_at = models.DateTimeField(auto_now_add=True)
    u_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.quantity} x {self.menu_item.name} (Order: {self.order.id})"

    def get_total_item_amount(self):
        """Calculates the total price for this line item."""
        return self.quantity * self.menu_item.price

    def clean(self):
        """Ensure menu item is available before adding."""
        super().clean()
        if self.menu_item and not self.menu_item.is_available: # Check if menu_item exists
            raise ValidationError(f"'{self.menu_item.name}' is currently not available.")

    # Keep save/delete overrides for immediate total recalculation
    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        if self.order: # Recalculate only if linked to an order
            self.order.calculate_order_total()

    def delete(self, *args, **kwargs):
        order = self.order # Store order before deleting self
        super().delete(*args, **kwargs)
        if order: # Recalculate only if it was linked to an order
            order.calculate_order_total()


class Reservations(models.Model):
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='reservations')
    reservation_time = models.DateTimeField()
    amount_of_customers = models.PositiveIntegerField()
    status = models.CharField(max_length=100, choices=RESERVATION_STATUS_CHOICES, default='pending')
    c_at = models.DateTimeField(auto_now_add=True)
    u_at = models.DateTimeField(auto_now=True)
    table = models.ForeignKey(Table, on_delete=models.SET_NULL, null=True, blank=True, related_name='reservations')

    def __str__(self):
        return f"Reservation for {self.amount_of_customers} at {self.reservation_time} by {self.user}"

    def clean(self):
        super().clean()
        # Add reservation conflict validation if needed


# --- Signal Handlers ---

# Helper function to reduce inventory and create usage record
def _reduce_inventory(order_item):
    if not order_item.menu_item: return
    for ingredient_link in order_item.menu_item.ingredients.all().select_related('inventory'):
        try:
            inventory_item = ingredient_link.inventory
            required_qty = decimal.Decimal(str(order_item.quantity)) * ingredient_link.quantity
            inventory_item.reduce_quantity(required_qty)
            InventoryUsage.objects.create(
                inventory=inventory_item,
                order_item=order_item,
                used_quantity=required_qty
            )
        except Inventory.DoesNotExist:
             print(f"Warning: Inventory item not found for ingredient link {ingredient_link.pk} during reduction.")
        except ValidationError as e:
            raise ValidationError(f"Failed OrderItem {order_item.pk}: {e}")
        except Exception as e:
             print(f"Error reducing inventory for OrderItem {order_item.pk}: {e}")

# Helper function to restore inventory and delete usage record
def _increase_inventory(order_item):
    """Restores inventory based on usage records using direct DB update."""
    if not order_item.menu_item: return
    usage_records = InventoryUsage.objects.filter(order_item=order_item)

    items_to_update = {} # {inventory_id: total_to_restore}

    # Aggregate the total quantity to restore for each inventory item
    for usage in usage_records:
        items_to_update[usage.inventory_id] = items_to_update.get(usage.inventory_id, decimal.Decimal('0.00')) + usage.used_quantity

    # Perform the database updates directly using QuerySet.update()
    try:
        # No explicit transaction needed here as QuerySet.update is atomic for supported fields
        for inventory_id, total_to_restore in items_to_update.items():
            if total_to_restore > 0:
                # Use .update() with F() expression for atomic increment
                updated_count = Inventory.objects.filter(pk=inventory_id).update(
                    quantity=F('quantity') + total_to_restore
                )
                if updated_count > 0:
                     print(f"Attempted to restore {total_to_restore} to Inventory ID {inventory_id}.") # Debug print
                else:
                     print(f"Warning: Inventory ID {inventory_id} not found during update for restore.")


        # Delete usage records after attempting restoration
        deleted_count, _ = usage_records.delete()
        print(f"Deleted {deleted_count} usage records for OrderItem {order_item.pk}.") # Debug print

    except Exception as e:
        # Log potential errors during the update or delete process
        print(f"Error during inventory restore/usage delete for OrderItem {order_item.pk}: {e}")



# @receiver(post_save, sender=OrderItem)
# def order_item_post_save_inventory_management(sender, instance, created, **kwargs):
#     """Manages inventory reduction/adjustment when an OrderItem is saved."""
#     if not instance.menu_item: return # Cannot manage inventory without a menu item

#     if created:
#         # Reduce inventory and create usage record on creation
#         _reduce_inventory(instance)
#     else:
#         # --- Refactored Update Logic ---
#         for ingredient_link in instance.menu_item.ingredients.all().select_related('inventory'):
#             try:
#                 inventory_item = ingredient_link.inventory
#                 required_ingredient_qty_per_menu_item = ingredient_link.quantity
#                 # Ensure calculations use Decimal
#                 new_total_required_qty = decimal.Decimal(str(instance.quantity)) * required_ingredient_qty_per_menu_item

#                 # Get the existing usage record or initialize if not found
#                 usage_record, usage_created = InventoryUsage.objects.get_or_create(
#                     inventory=inventory_item,
#                     order_item=instance,
#                     defaults={'used_quantity': decimal.Decimal('0.00')} # Default to 0 if just created
#                 )

#                 # Calculate the difference between new requirement and what was used before
#                 adjustment_qty = new_total_required_qty - usage_record.used_quantity

#                 if adjustment_qty != 0: # Only adjust if there's a change
#                     if adjustment_qty > 0: # Need to use more inventory
#                         inventory_item.reduce_quantity(adjustment_qty)
#                     elif adjustment_qty < 0: # Need to restore inventory
#                         inventory_item.increase_quantity(abs(adjustment_qty))

#                     # Update the usage record to reflect the new total requirement
#                     if new_total_required_qty <= 0 and not usage_created:
#                         usage_record.delete() # Remove usage if quantity becomes zero or less
#                     elif new_total_required_qty > 0 :
#                          usage_record.used_quantity = new_total_required_qty
#                          usage_record.save(update_fields=['used_quantity'])

#             except Inventory.DoesNotExist:
#                  print(f"Warning: Inventory item not found for ingredient link {ingredient_link.pk} during update.")
#             except ValidationError as e:
#                  # Re-raise validation errors (e.g., insufficient stock during adjustment)
#                  raise ValidationError(f"Failed adjusting OrderItem {instance.pk}: {e}")
#             except Exception as e:
#                  print(f"Error adjusting inventory for OrderItem {instance.pk}: {e}")
#         # --- End Refactored Update Logic ---

#     # Note: Order total calculation is handled by OrderItem.save override


# Ensure this uses post_delete
@receiver(pre_delete, sender=OrderItem)
def order_item_pre_delete_inventory_management(sender, instance, **kwargs):
    """Restores inventory BEFORE an OrderItem is deleted."""
    print(f"OrderItem {instance.pk} pre_delete signal triggered.") # Debug
    if not instance.menu_item: return
    # Get usage records BEFORE they are deleted by cascade
    usage_records = InventoryUsage.objects.filter(order_item=instance)

    items_to_update = {} # {inventory_id: total_to_restore}
    for usage in usage_records:
        items_to_update[usage.inventory_id] = items_to_update.get(usage.inventory_id, decimal.Decimal('0.00')) + usage.used_quantity

    try:
        # Use transaction.atomic for safety if multiple updates occur
        with transaction.atomic():
            for inventory_id, total_to_restore in items_to_update.items():
                if total_to_restore > 0:
                    # Use QuerySet.update() with F() for atomic increment
                    updated_count = Inventory.objects.filter(pk=inventory_id).update(
                        quantity=F('quantity') + total_to_restore
                    )
                    if updated_count > 0:
                        print(f"Attempted to restore {total_to_restore} to Inventory ID {inventory_id} (pre_delete).")
                    else:
                        print(f"Warning: Inventory ID {inventory_id} not found during update for restore (pre_delete).")
    except Exception as e:
        print(f"Error during inventory restore (pre_delete) for OrderItem {instance.pk}: {e}")
        

# Order Cancellation Inventory Restore
@receiver(post_save, sender=Order)
def order_post_save_inventory_restore_on_cancel(sender, instance, created, **kwargs):
    """Restores inventory if an existing order's status changes to 'cancelled'."""
    if not created:
        # Check if the 'order_status' field was updated
        update_fields = kwargs.get('update_fields', None)
        status_updated = update_fields is None or 'order_status' in update_fields

        if status_updated and instance.order_status == 'cancelled':
            # Fetch the previous state reliably using refresh_from_db on a separate instance
            # This is still potentially racy, but better than fetching by pk after save
            try:
                # Check if the status *was not* cancelled before this save
                # This requires tracking the previous state, which post_save doesn't easily provide.
                # A common workaround is to check if the object *just* became cancelled.
                # We'll rely on the assumption that if status is now cancelled, we restore.
                # A more robust solution uses django-dirtyfields or pre_save signal.

                print(f"Order {instance.pk} status changed to cancelled. Restoring inventory...")
                for order_item in instance.order_items.all():
                    _increase_inventory(order_item) # Use helper to restore based on usage records
                    print(f"Restored inventory related to OrderItem {order_item.pk}")

            except Exception as e:
                print(f"Error in order_post_save_inventory_restore_on_cancel signal for Order {instance.pk}: {e}")


# Table Availability Management
@receiver(post_save, sender=Order)
def order_post_save_update_table_availability(sender, instance, created, **kwargs):
    """
    Updates the associated Table's availability based on Order status.
    """
    if instance.table_id:
        try:
            table = Table.objects.get(pk=instance.table_id)
            active_order_statuses = ['pending', 'processing']

            # Check if ANY active order exists for this table
            has_any_active_order = Order.objects.filter(
                table=table,
                order_status__in=active_order_statuses
            ).exists()

            should_be_available = not has_any_active_order

            if table.is_available != should_be_available:
                table.is_available = should_be_available
                table.save(update_fields=['is_available'])
                print(f"Table {table.pk} availability set to {should_be_available} due to Order {instance.pk} status change.")

        except Table.DoesNotExist:
            print(f"Warning: Table {instance.table_id} not found for Order {instance.pk} in availability signal.")
        except Exception as e:
            print(f"Error in order_post_save_update_table_availability signal for Order {instance.pk}: {e}")

# @receiver(post_save, sender=OrderItem)
def create_inventory_usage(sender, instance, created, **kwargs):
    if not created:
        return  # Only handle creation for simplicity

    menu_item = instance.menu_item
    order_item_quantity = instance.quantity

    # For each ingredient needed for this menu item
    for ingredient in menu_item.ingredients.all():
        inventory = ingredient.inventory
        used_quantity = ingredient.quantity * decimal.Decimal(order_item_quantity)

        # Reduce inventory
        inventory.reduce_quantity(used_quantity)

        # Log usage
        InventoryUsage.objects.create(
            inventory=inventory,
            order_item=instance,
            used_quantity=used_quantity
        )