# c:\Users\User\Desktop\waiter-system\order\models.py
import decimal # Import decimal
import logging
from django.db import models, transaction
# Ensure all necessary models are imported
from inventory.models import Table, Inventory, InventoryUsage, MenuItemIngredient
from django.core.exceptions import ValidationError
from django.db.models import F
from django.db.models.signals import post_save, post_delete, pre_delete, pre_save
from django.dispatch import receiver
from django.conf import settings

User = settings.AUTH_USER_MODEL

logger = logging.getLogger(__name__)

ORDER_STATUS_CHOICES = [
    ('pending', 'Pending'),
    ('processing', 'Processing'),
    ('completed', 'Completed'),
]

MENU_CATEGORY_CHOICES = [
    ('salads', 'Salads'),
    ('mains', 'Mains'),
    ('deserts', 'Deserts'),
    ('drinks', 'Drinks'),
    ('appetizers', 'Appetizers'),
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
    order_status = models.CharField(max_length=100, choices=ORDER_STATUS_CHOICES, default='processing')
    amount = models.DecimalField(max_digits=10, decimal_places=2, default=decimal.Decimal('0.00'))
    subamount = models.DecimalField(max_digits=10, decimal_places=2, default=decimal.Decimal('0.00'))
    c_at = models.DateTimeField(auto_now_add=True)
    u_at = models.DateTimeField(auto_now=True)
    table = models.ForeignKey(Table, on_delete=models.SET_NULL, null=True, blank=True, related_name='orders')

    def __str__(self):
        return f"Order ID: {self.id}, Status: {self.order_status}"
    def diff(self):
        """Returns the difference between amount and subamount."""
        difference = self.amount - self.subamount
        return difference

    def calculate_order_total(self):
        """Calculates subamount (without commission) and amount (with commission) based on associated order items."""
        subtotal = decimal.Decimal('0.00')
        for item in self.order_items.all():
             subtotal += item.get_total_item_amount()

        final_total = subtotal
        commission_percentage = decimal.Decimal('0.00')

        if self.table and self.table.commission:
            commission_percentage = self.table.commission
            commission_amount = subtotal * (commission_percentage / decimal.Decimal('100.00'))
            final_total += commission_amount

        # Update fields only if they have changed
        if self.subamount != subtotal or self.amount != final_total:
            self.subamount = subtotal
            self.amount = final_total
            self.save(update_fields=['subamount', 'amount'])
        return self.amount


class CompletedOrderManager(models.Manager):
    """A custom manager that returns only completed orders."""
    def get_queryset(self):
        return super().get_queryset().filter(order_status='completed')

class CompletedOrder(Order):
    """A proxy model to represent only completed orders for stats and reporting."""
    objects = CompletedOrderManager()

    class Meta:
        proxy = True
        verbose_name = "Completed Order"
        verbose_name_plural = "Completed Orders"

    def get_profit(self):
        """Calculates the profit (commission) from this completed order."""
        return self.amount - self.subamount

class MenuItem(models.Model):
    name = models.CharField(max_length=255, unique=True)
    description = models.TextField(blank=True, null=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    category = models.CharField(max_length=100, choices=MENU_CATEGORY_CHOICES)
    is_available = models.BooleanField(default=True)
    is_frequent = models.BooleanField(default=False)
    c_at = models.DateTimeField(auto_now_add=True)
    u_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='order_items')
    menu_item = models.ForeignKey(MenuItem, on_delete=models.PROTECT, related_name='order_items')
    quantity = models.DecimalField(max_digits=10, decimal_places=2, default=decimal.Decimal('1.00'))
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

    def _manage_inventory_on_save(self, is_new):
        if not self.menu_item: return

        if is_new:
            _reduce_inventory(self)
        else:
            for ingredient_link in self.menu_item.ingredients.all().select_related('inventory'):
                try:
                    inventory_item = ingredient_link.inventory
                    required_ingredient_qty_per_menu_item = ingredient_link.quantity
                    new_total_required_qty = decimal.Decimal(str(self.quantity)) * required_ingredient_qty_per_menu_item

                    usage_record, usage_created = InventoryUsage.objects.get_or_create(
                        inventory=inventory_item,
                        order_item=self,
                        defaults={'used_quantity': decimal.Decimal('0.00')}
                    )

                    adjustment_qty = new_total_required_qty - usage_record.used_quantity

                    if adjustment_qty != 0:
                        if adjustment_qty > 0:
                            inventory_item.reduce_quantity(adjustment_qty)
                        elif adjustment_qty < 0:
                            inventory_item.increase_quantity(abs(adjustment_qty))

                        if new_total_required_qty <= 0 and not usage_created:
                            usage_record.delete()
                        elif new_total_required_qty > 0:
                            usage_record.used_quantity = new_total_required_qty
                            usage_record.save(update_fields=['used_quantity'])

                except Inventory.DoesNotExist:
                    print(f"Warning: Inventory item not found for ingredient link {ingredient_link.pk} during update.")
                except ValidationError as e:
                    raise ValidationError(f"Failed adjusting OrderItem {self.pk}: {e}")
                except Exception as e:
                    print(f"Error adjusting inventory for OrderItem {self.pk}: {e}")

    def save(self, *args, **kwargs):
        is_new = self._state.adding
        with transaction.atomic():
            super().save(*args, **kwargs)
            self._manage_inventory_on_save(is_new)
            if self.order:
                self.order.calculate_order_total()

    def delete(self, *args, **kwargs):
        order = self.order
        with transaction.atomic():
            _increase_inventory(self)
            super().delete(*args, **kwargs)
        if order:
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

@receiver(post_delete, sender=Order)
def order_post_delete_update_table_availability(sender, instance, **kwargs):
    """
    Updates the associated Table's availability when an Order is deleted.
    """
    if instance.table_id:
        try:
            # The order is already deleted, so we check for any *other* active orders on the table.
            table = Table.objects.get(pk=instance.table_id)
            active_order_statuses = ['pending', 'processing']

            has_any_active_order = Order.objects.filter(
                table=table,
                order_status__in=active_order_statuses
            ).exists()

            # If no active orders exist, the table should be available.
            if not has_any_active_order and not table.is_available:
                table.is_available = True
                table.save(update_fields=['is_available'])
                print(f"Table {table.pk} availability set to True due to Order {instance.pk} deletion.")

        except Table.DoesNotExist:
            print(f"Warning: Table {instance.table_id} not found for deleted Order {instance.pk} in availability signal.")
        except Exception as e:
            print(f"Error in order_post_delete_update_table_availability signal for Order {instance.pk}: {e}")


    # Capture the previous status before saving so post_save handlers can detect changes
    @receiver(pre_save, sender=Order)
    def order_pre_save_capture_status(sender, instance, **kwargs):
        if instance.pk:
            try:
                previous = Order.objects.get(pk=instance.pk)
                instance._previous_order_status = previous.order_status
            except Order.DoesNotExist:
                instance._previous_order_status = None
        else:
            instance._previous_order_status = None


    @receiver(post_save, sender=Order)
    def order_post_save_printer_on_status_change(sender, instance, created, **kwargs):
        """Print the printer IP whenever an Order's status changes."""
        prev = getattr(instance, '_previous_order_status', None)
        curr = instance.order_status
        # Consider only true status changes (not creation)
        if not created and prev is not None and prev != curr:
            try:
                logger.info("printer ip: 192.168.100.51")
            except Exception:
                # Never let a logging error break order save flow
                pass