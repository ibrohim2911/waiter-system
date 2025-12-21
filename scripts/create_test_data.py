import os
import sys
import pathlib
import django
from decimal import Decimal

# Ensure project root is on sys.path so `config` package is importable
project_root = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.contrib.auth import get_user_model
from inventory.models import Inventory, MenuItemIngredient
from order.models import MenuItem, Order, OrderItem

User = get_user_model()


def create_users():
    admin, created = User.objects.get_or_create(
        phone_number='0000000000',
        defaults={
            'name': 'Admin Test',
            'email': 'admin@example.com',
            'is_staff': True,
            'is_superuser': True,
            'role': 'admin'
        }
    )
    if created:
        admin.set_password('adminpass')
        admin.save()
    waiter, created = User.objects.get_or_create(
        phone_number='1111111111',
        defaults={
            'name': 'Waiter Test',
            'email': 'waiter@example.com',
            'role': 'waiter'
        }
    )
    if created:
        waiter.set_unusable_password()
        waiter.set_pin('1234')
        waiter.save()
    return admin, waiter


def create_inventory_and_menu():
    inv, _ = Inventory.objects.get_or_create(
        name='Tomato',
        defaults={'quantity': Decimal('10.00'), 'unit_of_measure': 'kg', 'price': Decimal('1.00')}
    )

    menu, _ = MenuItem.objects.get_or_create(
        name='Tomato Salad',
        defaults={'description': 'Fresh tomato salad', 'price': Decimal('5.00'), 'category': 'salads', 'is_available': True}
    )

    # Link ingredient: one menu item requires 0.5 kg tomato
    link, created = MenuItemIngredient.objects.get_or_create(menu_item=menu, inventory=inv, defaults={'quantity': Decimal('0.50')})
    if not created:
        link.quantity = Decimal('0.50')
        link.save()

    return inv, menu


def create_order_and_use_menu(waiter, menu):
    # Create an order by waiter and add 2 menu items (should use 2 * 0.5 = 1.0 kg)
    order = Order.objects.create(user=waiter, order_status='processing')
    oi = OrderItem.objects.create(order=order, menu_item=menu, quantity=Decimal('2.00'))
    return order, oi


def print_state(inv, menu, order, oi):
    print('--- STATE ---')
    print('Inventory:', inv.name, 'Quantity:', inv.quantity)
    print('MenuItem:', menu.name, 'is_available:', menu.is_available)
    from inventory.models import InventoryUsage
    usages = InventoryUsage.objects.filter(order_item=oi)
    print('InventoryUsage records for OrderItem:', usages.count())
    for u in usages:
        print('  ', u.inventory.name, u.used_quantity, 'c_at:', u.c_at)
    print('Order totals: subamount=', order.subamount, 'amount=', order.amount)


if __name__ == '__main__':
    print('Creating users...')
    admin, waiter = create_users()
    print('Creating inventory and menu...')
    inv, menu = create_inventory_and_menu()
    print('Inventory before order:', inv.quantity)
    print('Creating order and order item...')
    order, oi = create_order_and_use_menu(waiter, menu)
    # Refresh instances from DB to see updated quantities
    inv.refresh_from_db()
    menu.refresh_from_db()
    order.refresh_from_db()
    oi.refresh_from_db()
    print_state(inv, menu, order, oi)

    # Now attempt to create another order that would deplete inventory
    try:
        print('\nCreating second order to deplete inventory...')
        order2 = Order.objects.create(user=waiter, order_status='processing')
        oi2 = OrderItem.objects.create(order=order2, menu_item=menu, quantity=Decimal('18.00'))
        inv.refresh_from_db()
        menu.refresh_from_db()
        print_state(inv, menu, order2, oi2)
    except Exception as e:
        print('Expected error or validation on second order (insufficient stock):', e)

    print('\nDone.')
