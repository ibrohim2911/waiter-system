# c:\Users\User\Desktop\waiter-system\order\models.py
from datetime import timezone
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

PRINTER_STATUS_CHOICES = [
    ('done', 'Done'),
    ('pending', 'Pending'),
    ('canselled', 'Canselled'),
    ('error', 'Error'),
]

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
    printer = models.ForeignKey('Printer', on_delete=models.SET_NULL, null=True, blank=True, related_name='menu_items')
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

class Printer(models.Model):
    name = models.CharField(max_length=255, unique=True)
    ip_address = models.GenericIPAddressField()
    port = models.IntegerField(default=9100) # Added port
    is_cashier_printer = models.BooleanField(default=False)
    is_enabled = models.BooleanField(default=True)
    
    def __str__(self):
        return f"{self.name} ({self.ip_address})"

class PrintJob(models.Model):
    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('printing', 'Printing'),
        ('printed', 'Printed'),
        ('failed', 'Failed'),
        ('cancelled', 'Cancelled'),
    )

    printer = models.ForeignKey(Printer, on_delete=models.CASCADE)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    payload = models.TextField() # Stores the actual text to print
    error_message = models.TextField(blank=True, null=True)
    c_at = models.DateTimeField(auto_now_add=True)
    u_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Job {self.id} -> {self.printer.name} ({self.status})"
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
@receiver(post_save, sender=Order) # Replace 'yourapp' with your actual app name
def order_post_save_trigger_printer(sender, instance, created, **kwargs):
    """Prints full receipt to Cashier Printer when order is completed."""
    if not created:
        update_fields = kwargs.get('update_fields')
        # Check if order_status changed to completed
        if instance.order_status == 'completed':
            try:
                from .utils import cashier_receipt
                
                # 1. Generate Content
                content = cashier_receipt(instance.id)
                
                # 2. Find Cashier Printer
                printer = Printer.objects.filter(is_cashier_printer=True, is_enabled=True).first()
                
                if printer:
                    # 3. Create Job
                    PrintJob.objects.create(printer=printer, payload=content, status='pending')
                else:
                    logger.warning("No Cashier Printer found!")

            except Exception as e:
                logger.exception(f"Error creating cashier receipt for Order {instance.pk}: {e}")

@receiver(post_save, sender=OrderItem)
def orderitem_post_save_trigger_printer(sender, instance, created, **kwargs):
    """Prints kitchen ticket to the specific printer defined in MenuItem."""
    if created:
        try:
            from .utils import orderitem_receipt
            
            # 1. Get the printer specific to this menu item (e.g., Kitchen vs Bar)
            # Assuming MenuItem has a 'printer' ForeignKey field
            target_printer = instance.menu_item.printer 

            if target_printer and target_printer.is_enabled:
                # 2. Generate Content
                content = orderitem_receipt(instance)
                
                # 3. Create Job
                PrintJob.objects.create(printer=target_printer, payload=content, status='pending')
        
        except Exception as e:
            logger.exception(f"Error creating item receipt: {e}")

@receiver(post_delete, sender=OrderItem)
def orderitem_post_delete_trigger_printer(sender, instance, **kwargs):
    """Prints cancellation ticket when item is deleted."""
    try:
        from .utils import cancelled_orderitem_receipt
        
        target_printer = instance.menu_item.printer 

        if target_printer and target_printer.is_enabled:
            content = cancelled_orderitem_receipt(instance)
            PrintJob.objects.create(printer=target_printer, payload=content, status='pending')

    except Exception as e:
        logger.exception(f"Error creating cancel receipt: {e}")