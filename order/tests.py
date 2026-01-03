import decimal
from django.test import TestCase
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError

from inventory.models import Table, Inventory, MenuItemIngredient
from order.models import Order, MenuItem, OrderItem

User = get_user_model()


class OrderItemInventoryTestCase(TestCase):
    def setUp(self):
        # Create a user
        self.user = User.objects.create_user(username='testuser', password='password')

        # Create a table
        self.table = Table.objects.create(name='Table 1', capacity=4)

        # Create an order
        self.order = Order.objects.create(user=self.user, table=self.table)

        # Create menu items
        self.menu_item_1 = MenuItem.objects.create(
            name='Burger',
            price=decimal.Decimal('10.00'),
            category='mains'
        )

        # Create inventory items
        self.inventory_bun = Inventory.objects.create(
            name='Bun',
            quantity=decimal.Decimal('10.00'),
            unit_of_measure='unit'
        )
        self.inventory_patty = Inventory.objects.create(
            name='Patty',
            quantity=decimal.Decimal('5.00'),
            unit_of_measure='unit'
        )

        # Create menu item ingredients
        self.ingredient_bun = MenuItemIngredient.objects.create(
            menu_item=self.menu_item_1,
            inventory=self.inventory_bun,
            quantity=decimal.Decimal('2.00') # 2 buns per burger
        )
        self.ingredient_patty = MenuItemIngredient.objects.create(
            menu_item=self.menu_item_1,
            inventory=self.inventory_patty,
            quantity=decimal.Decimal('1.00') # 1 patty per burger
        )

    def test_create_order_item_sufficient_inventory(self):
        """
        Test that creating an OrderItem with sufficient inventory works correctly.
        """
        initial_bun_quantity = self.inventory_bun.quantity
        initial_patty_quantity = self.inventory_patty.quantity

        # Create an order item
        order_item = OrderItem.objects.create(
            order=self.order,
            menu_item=self.menu_item_1,
            quantity=decimal.Decimal('2.00') # 2 burgers
        )

        # Check that the order item was created
        self.assertEqual(OrderItem.objects.count(), 1)

        # Check that the inventory was reduced correctly
        self.inventory_bun.refresh_from_db()
        self.inventory_patty.refresh_from_db()
        self.assertEqual(self.inventory_bun.quantity, initial_bun_quantity - (order_item.quantity * self.ingredient_bun.quantity))
        self.assertEqual(self.inventory_patty.quantity, initial_patty_quantity - (order_item.quantity * self.ingredient_patty.quantity))

    def test_create_order_item_insufficient_inventory(self):
        """
        Test that creating an OrderItem with insufficient inventory fails
        and does not create the OrderItem or reduce inventory.
        """
        initial_bun_quantity = self.inventory_bun.quantity
        initial_patty_quantity = self.inventory_patty.quantity

        # Try to create an order item that requires more patties than available
        with self.assertRaises(ValidationError):
            OrderItem.objects.create(
                order=self.order,
                menu_item=self.menu_item_1,
                quantity=decimal.Decimal('6.00') # 6 burgers, but only 5 patties available
            )

        # Check that the order item was not created
        self.assertEqual(OrderItem.objects.count(), 0)

        # Check that the inventory was not reduced
        self.inventory_bun.refresh_from_db()
        self.inventory_patty.refresh_from_db()
        self.assertEqual(self.inventory_bun.quantity, initial_bun_quantity)
        self.assertEqual(self.inventory_patty.quantity, initial_patty_quantity)
