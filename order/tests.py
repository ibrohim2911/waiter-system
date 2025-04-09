# c:\Users\User\Desktop\waiter-system\order\tests.py
import decimal
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from rest_framework.test import APITestCase
from rest_framework import status

from .models import Order, MenuItem, OrderItem, Reservations
try:
    from inventory.models import Inventory, Table, MenuItemIngredient, InventoryUsage
except ImportError:
    Inventory, Table, MenuItemIngredient, InventoryUsage = None, None, None, None

User = get_user_model()

class OrderModelsTests(TestCase):

    @classmethod
    def setUpTestData(cls):
        if Inventory is None or Table is None or MenuItemIngredient is None:
            raise cls.skipTest("Inventory models not available for Order model tests.")
        cls.user = User.objects.create_user(phone_number='order_user', name='Order Test', password='pw')
        cls.item1 = Inventory.objects.create(name="Flour", quantity=10.0, unit_of_measure='kg', price=1.0)
        cls.item2 = Inventory.objects.create(name="Sugar", quantity=5.0, unit_of_measure='kg', price=2.0)
        cls.menu_item = MenuItem.objects.create(name="Cake", price=15.00, category='desserts')
        MenuItemIngredient.objects.create(menu_item=cls.menu_item, inventory=cls.item1, quantity=0.5)
        MenuItemIngredient.objects.create(menu_item=cls.menu_item, inventory=cls.item2, quantity=0.3)
        cls.table = Table.objects.create(name="Order T1", location="indoor", capacity=4)

    def test_menu_item_creation(self):
        self.assertEqual(self.menu_item.name, "Cake")
        self.assertTrue(self.menu_item.is_available)

    def test_order_creation(self):
        order = Order.objects.create(user=self.user, table=self.table)
        self.assertEqual(order.user, self.user)
        self.assertEqual(order.table, self.table)
        self.assertEqual(order.order_status, 'pending')
        self.assertEqual(order.amount, decimal.Decimal('0.00'))

    def test_order_item_creation(self):
        order = Order.objects.create(user=self.user)
        order_item = OrderItem.objects.create(order=order, menu_item=self.menu_item, quantity=2)
        self.assertEqual(order_item.order, order)
        self.assertEqual(order_item.menu_item, self.menu_item)
        self.assertEqual(order_item.quantity, 2)
        self.assertEqual(order_item.get_total_item_amount(), decimal.Decimal('30.00'))

    def test_order_item_unavailable_validation(self):
        original_availability = self.menu_item.is_available
        self.menu_item.is_available = False
        self.menu_item.save()
        order = Order.objects.create(user=self.user)
        with self.assertRaises(ValidationError):
            oi = OrderItem(order=order, menu_item=self.menu_item, quantity=1)
            oi.full_clean()
        self.menu_item.is_available = original_availability
        self.menu_item.save()

    def test_reservation_creation(self):
        res_time = timezone.now() + timezone.timedelta(days=1)
        reservation = Reservations.objects.create(
            user=self.user, table=self.table, reservation_time=res_time, amount_of_customers=3
        )
        self.assertEqual(reservation.user, self.user)
        self.assertEqual(reservation.table, self.table)
        self.assertEqual(reservation.status, 'pending')

class OrderSignalTests(TestCase):

    @classmethod
    def setUpTestData(cls):
        if Inventory is None or Table is None or MenuItemIngredient is None or InventoryUsage is None:
            raise cls.skipTest("Inventory models not available for Order signal tests.")
        cls.user = User.objects.create_user(phone_number='signal_user', name='Signal Test', password='pw')
        cls.flour = Inventory.objects.create(name="Flour", quantity=10.0, unit_of_measure='kg', price=1.0)
        cls.sugar = Inventory.objects.create(name="Sugar", quantity=5.0, unit_of_measure='kg', price=2.0)
        cls.menu_item = MenuItem.objects.create(name="Cake", price=15.00, category='desserts')
        MenuItemIngredient.objects.create(menu_item=cls.menu_item, inventory=cls.flour, quantity=0.5)
        MenuItemIngredient.objects.create(menu_item=cls.menu_item, inventory=cls.sugar, quantity=0.3)
        cls.table = Table.objects.create(name="Signal T1", location="indoor", capacity=4, is_available=True)

    def setUp(self):
        # Reset quantities and table state before each test
        self.flour.quantity = decimal.Decimal('10.0')
        self.flour.save()
        self.sugar.quantity = decimal.Decimal('5.0')
        self.sugar.save()
        self.table.is_available = True
        self.table.save()
        # Create a fresh order; table availability signal will run here
        self.order = Order.objects.create(user=self.user, table=self.table, order_status='pending')
        # Clear usage records related to potentially stale orders from previous tests if necessary
        # InventoryUsage.objects.all().delete() # Use with caution

    def test_create_order_item_reduces_inventory_and_creates_usage(self):
        initial_flour_qty = self.flour.quantity # 10.0
        initial_sugar_qty = self.sugar.quantity # 5.0

        order_item = OrderItem.objects.create(order=self.order, menu_item=self.menu_item, quantity=2)

        self.flour.refresh_from_db()
        self.sugar.refresh_from_db()

        expected_flour_reduction = decimal.Decimal('1.0') # 2 * 0.5
        expected_sugar_reduction = decimal.Decimal('0.6') # 2 * 0.3

        self.assertAlmostEqual(self.flour.quantity, initial_flour_qty - expected_flour_reduction) # 10.0 - 1.0 = 9.0
        self.assertAlmostEqual(self.sugar.quantity, initial_sugar_qty - expected_sugar_reduction) # 5.0 - 0.6 = 4.4

        self.assertTrue(InventoryUsage.objects.filter(order_item=order_item, inventory=self.flour, used_quantity=expected_flour_reduction).exists())
        self.assertTrue(InventoryUsage.objects.filter(order_item=order_item, inventory=self.sugar, used_quantity=expected_sugar_reduction).exists())

    def test_update_order_item_adjusts_inventory(self):
        # Initial state: Flour=10.0, Sugar=5.0
        order_item = OrderItem.objects.create(order=self.order, menu_item=self.menu_item, quantity=2)
        # After create: Flour=9.0, Sugar=4.4
        self.flour.refresh_from_db()
        self.sugar.refresh_from_db()
        flour_after_create = self.flour.quantity
        sugar_after_create = self.sugar.quantity
        self.assertAlmostEqual(flour_after_create, decimal.Decimal('9.0'))
        self.assertAlmostEqual(sugar_after_create, decimal.Decimal('4.4'))

        # Increase quantity to 3 (requires 1.5 flour, 0.9 sugar total)
        # Adjustment needed: +0.5 flour, +0.3 sugar
        order_item.quantity = 3
        order_item.save() # Signal triggers adjustment

        self.flour.refresh_from_db()
        self.sugar.refresh_from_db()
        # Expected: Flour=9.0-0.5=8.5, Sugar=4.4-0.3=4.1
        self.assertAlmostEqual(self.flour.quantity, decimal.Decimal('8.5'), msg="Flour quantity incorrect after increase")
        self.assertAlmostEqual(self.sugar.quantity, decimal.Decimal('4.1'), msg="Sugar quantity incorrect after increase")
        # Check usage record updated
        usage_flour = InventoryUsage.objects.get(order_item=order_item, inventory=self.flour)
        usage_sugar = InventoryUsage.objects.get(order_item=order_item, inventory=self.sugar)
        self.assertAlmostEqual(usage_flour.used_quantity, decimal.Decimal('1.5')) # 3 * 0.5
        self.assertAlmostEqual(usage_sugar.used_quantity, decimal.Decimal('0.9')) # 3 * 0.3

        # Decrease quantity to 1 (requires 0.5 flour, 0.3 sugar total)
        # Adjustment needed: -1.0 flour, -0.6 sugar (restore)
        order_item.quantity = 1
        order_item.save() # Signal triggers adjustment

        self.flour.refresh_from_db()
        self.sugar.refresh_from_db()
        # Expected: Flour=8.5+1.0=9.5, Sugar=4.1+0.6=4.7
        self.assertAlmostEqual(self.flour.quantity, decimal.Decimal('9.5'), msg="Flour quantity incorrect after decrease")
        self.assertAlmostEqual(self.sugar.quantity, decimal.Decimal('4.7'), msg="Sugar quantity incorrect after decrease")
        # Check usage record updated
        usage_flour = InventoryUsage.objects.get(order_item=order_item, inventory=self.flour)
        usage_sugar = InventoryUsage.objects.get(order_item=order_item, inventory=self.sugar)
        self.assertAlmostEqual(usage_flour.used_quantity, decimal.Decimal('0.5')) # 1 * 0.5
        self.assertAlmostEqual(usage_sugar.used_quantity, decimal.Decimal('0.3')) # 1 * 0.3

    def test_delete_order_item_restores_inventory_and_deletes_usage(self):
        # Initial state: Flour=10.0, Sugar=5.0 (from setUp)
        order_item = OrderItem.objects.create(order=self.order, menu_item=self.menu_item, quantity=2)
        # After create: Flour=9.0, Sugar=4.4
        self.assertTrue(InventoryUsage.objects.filter(order_item=order_item).exists())

        order_item_pk = order_item.pk
        order_item.delete() # Signal triggers restore based on usage records

        # Ensure refresh_from_db is present before assertion
        self.flour.refresh_from_db()
        self.sugar.refresh_from_db()

        # Expected: Flour=9.0+1.0=10.0, Sugar=4.4+0.6=5.0
        self.assertAlmostEqual(self.flour.quantity, decimal.Decimal('10.0')) # Now checking the refreshed value
        self.assertAlmostEqual(self.sugar.quantity, decimal.Decimal('5.0')) # Now checking the refreshed value
        self.assertFalse(InventoryUsage.objects.filter(order_item_id=order_item_pk).exists())
    def test_order_item_save_recalculates_order_total(self):
        # Order created in setUp, amount should be 0 initially
        self.order.refresh_from_db()
        self.assertEqual(self.order.amount, decimal.Decimal('0.00'))

        OrderItem.objects.create(order=self.order, menu_item=self.menu_item, quantity=1) # Price 15.00
        self.order.refresh_from_db()
        self.assertEqual(self.order.amount, decimal.Decimal('15.00'))

        OrderItem.objects.create(order=self.order, menu_item=self.menu_item, quantity=2) # Price 30.00
        self.order.refresh_from_db()
        self.assertEqual(self.order.amount, decimal.Decimal('45.00')) # 15 + 30

    def test_order_item_delete_recalculates_order_total(self):
        oi1 = OrderItem.objects.create(order=self.order, menu_item=self.menu_item, quantity=1) # 15.00
        oi2 = OrderItem.objects.create(order=self.order, menu_item=self.menu_item, quantity=2) # 30.00
        self.order.refresh_from_db()
        self.assertEqual(self.order.amount, decimal.Decimal('45.00'))

        oi2.delete() # OrderItem.delete override triggers calculation
        self.order.refresh_from_db()
        self.assertEqual(self.order.amount, decimal.Decimal('15.00'))

    def test_cancel_order_restores_inventory(self):
        # Initial state: Flour=10.0, Sugar=5.0
        order_item = OrderItem.objects.create(order=self.order, menu_item=self.menu_item, quantity=2)
        # After create: Flour=9.0, Sugar=4.4

        self.order.order_status = 'cancelled'
        self.order.save() # Signal should trigger restore

        self.flour.refresh_from_db()
        self.sugar.refresh_from_db()
        # Expected: Flour=9.0+1.0=10.0, Sugar=4.4+0.6=5.0
        expected_flour_final = decimal.Decimal('10.0')
        expected_sugar_final = decimal.Decimal('5.0')
        self.assertAlmostEqual(self.flour.quantity, expected_flour_final, msg="Flour quantity not restored correctly on cancel.")
        self.assertAlmostEqual(self.sugar.quantity, expected_sugar_final, msg="Sugar quantity not restored correctly on cancel.")
        self.assertFalse(InventoryUsage.objects.filter(order_item=order_item).exists())

    def test_order_status_updates_table_availability(self):
        # Order created in setUp (status='pending'), table signal ran.
        self.table.refresh_from_db()
        # FIX: Assert based on state *after* setUp's order creation
        self.assertFalse(self.table.is_available, "Table should be unavailable after pending order created in setUp")

        # Change status to processing - should remain unavailable
        self.order.order_status = 'processing'
        self.order.save()
        self.table.refresh_from_db()
        self.assertFalse(self.table.is_available, "Table should remain unavailable when order is processing")

        # Create a second order on the same table
        order2 = Order.objects.create(user=self.user, table=self.table, order_status='pending')
        self.table.refresh_from_db()
        self.assertFalse(self.table.is_available, "Table should remain unavailable with multiple active orders")

        # Complete the first order (self.order) - should remain unavailable due to order2
        self.order.order_status = 'completed'
        self.order.save()
        self.table.refresh_from_db()
        self.assertFalse(self.table.is_available, "Table should remain unavailable if other active orders exist")

        # Complete the second order (order2) - should become available
        order2.order_status = 'completed'
        order2.save()
        self.table.refresh_from_db()
        self.assertTrue(self.table.is_available, "Table should become available when all active orders are completed")

        # Test cancellation makes it available if it's the only active one
        order3 = Order.objects.create(user=self.user, table=self.table, order_status='pending')
        self.table.refresh_from_db()
        self.assertFalse(self.table.is_available)
        order3.order_status = 'cancelled'
        order3.save()
        self.table.refresh_from_db()
        self.assertTrue(self.table.is_available, "Table should become available when order is cancelled")


class OrderAPITests(APITestCase):

    @classmethod
    def setUpTestData(cls):
        if Table is None or MenuItem is None or Inventory is None or MenuItemIngredient is None:
             raise cls.skipTest("Required models not available for Order API tests.")
        cls.user = User.objects.create_user(phone_number='order_api', name='Order API', password='pw', role='customer')
        cls.admin_user = User.objects.create_superuser(phone_number='order_admin', name='Order Admin', password='pw')
        cls.table = Table.objects.create(name="API Order T1", location="indoor", capacity=4, is_available=True)
        cls.menu_item = MenuItem.objects.create(name="API Cake", price=20.00, category='desserts')
        cls.ingredient = Inventory.objects.create(name="API Flour", quantity=10.0, unit_of_measure='kg', price=1)
        MenuItemIngredient.objects.create(menu_item=cls.menu_item, inventory=cls.ingredient, quantity=0.1)

        # Create order and item, signals will run reducing inventory
        cls.order = Order.objects.create(user=cls.user, table=cls.table, order_status='processing')
        cls.order_item = OrderItem.objects.create(order=cls.order, menu_item=cls.menu_item, quantity=1) # Uses 0.1 ingredient

        cls.reservation = Reservations.objects.create(user=cls.user, table=cls.table, reservation_time=timezone.now() + timezone.timedelta(hours=2), amount_of_customers=2)

        # Verify ingredient quantity after setup reduction
        cls.ingredient.refresh_from_db()
        if cls.ingredient.quantity != decimal.Decimal('9.9'):
            print(f"Warning: setUpTestData ingredient quantity is {cls.ingredient.quantity}, expected 9.9")

        cls.order_list_url = reverse('order-list')
        cls.menuitem_list_url = reverse('menuitem-list')
        cls.orderitem_list_url = reverse('orderitem-list')
        cls.reservation_list_url = reverse('reservation-list')

    # --- Order Endpoints ---
    def test_list_orders_authenticated_owner(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.get(self.order_list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['id'], self.order.id)
        self.assertEqual(response.data[0]['order_status'], 'processing')
        self.assertTrue('items' in response.data[0])
        self.assertEqual(len(response.data[0]['items']), 1)
        self.assertEqual(response.data[0]['items'][0]['id'], self.order_item.id)

    def test_list_orders_authenticated_admin(self):
        other_user = User.objects.create_user(phone_number='other', name='Other', password='pw')
        Order.objects.create(user=other_user)
        self.client.force_authenticate(user=self.admin_user)
        response = self.client.get(self.order_list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)

    def test_list_orders_unauthenticated(self):
        response = self.client.get(self.order_list_url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_create_order_authenticated(self):
        self.client.force_authenticate(user=self.user)
        self.table.is_available = True
        self.table.save()
        data = {'table': self.table.pk, 'order_status': 'pending'}
        response = self.client.post(self.order_list_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['order_status'], 'pending')
        self.assertEqual(response.data['user'], self.user.pk)
        new_order = Order.objects.get(pk=response.data['id'])
        self.assertEqual(new_order.user, self.user)
        self.table.refresh_from_db()
        self.assertFalse(self.table.is_available)

    def test_update_order_status_owner(self):
        # Ensure table is unavailable due to setup order
        self.table.is_available = False
        self.table.save()
        self.client.force_authenticate(user=self.user)
        url = reverse('order-detail', kwargs={'pk': self.order.pk})
        data = {'order_status': 'completed'}
        response = self.client.patch(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.order.refresh_from_db()
        self.assertEqual(self.order.order_status, 'completed')
        self.table.refresh_from_db()
        self.assertTrue(self.table.is_available)

    def test_update_order_table_owner(self):
        new_table = Table.objects.create(name="New Tbl", location="outdoor", capacity=2, is_available=True)
        self.client.force_authenticate(user=self.user)
        url = reverse('order-detail', kwargs={'pk': self.order.pk})
        data = {'table': new_table.pk}
        response = self.client.patch(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.order.refresh_from_db()
        self.assertEqual(self.order.table, new_table)

    def test_update_order_other_user(self):
        other_user = User.objects.create_user(phone_number='other_api', name='Other API', password='pw')
        self.client.force_authenticate(user=other_user)
        url = reverse('order-detail', kwargs={'pk': self.order.pk})
        data = {'order_status': 'completed'}
        response = self.client.patch(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_delete_order_owner(self):
        order_to_delete = Order.objects.create(user=self.user, table=self.table, order_status='pending')
        order_pk = order_to_delete.pk
        self.table.refresh_from_db()
        self.assertFalse(self.table.is_available)
        self.client.force_authenticate(user=self.user)
        url = reverse('order-detail', kwargs={'pk': order_pk})
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Order.objects.filter(pk=order_pk).exists())

    # --- OrderItem Endpoints ---
    def test_list_orderitems_owner(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.get(self.orderitem_list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['id'], self.order_item.id)

    def test_list_orderitems_other_user(self):
        other_user = User.objects.create_user(phone_number='other_oi', name='Other OI', password='pw')
        self.client.force_authenticate(user=other_user)
        response = self.client.get(self.orderitem_list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 0)

    def test_create_orderitem_owner(self):
        self.client.force_authenticate(user=self.user)
        # Reset ingredient quantity for predictable test
        self.ingredient.quantity = decimal.Decimal('10.0')
        self.ingredient.save()
        initial_qty = self.ingredient.quantity # 10.0

        data = {'order': self.order.pk, 'menu_item': self.menu_item.pk, 'quantity': 3}
        response = self.client.post(self.orderitem_list_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['quantity'], 3)
        self.assertTrue(OrderItem.objects.filter(order=self.order, quantity=3).exists())

        self.ingredient.refresh_from_db()
        expected_reduction = decimal.Decimal('0.3') # 3 * 0.1
        expected_final_qty = initial_qty - expected_reduction # 10.0 - 0.3 = 9.7

        self.assertAlmostEqual(
            self.ingredient.quantity,
            expected_final_qty,
            msg=f"Ingredient qty should be {expected_final_qty}, but was {self.ingredient.quantity}"
        )

    def test_create_orderitem_for_other_users_order(self):
        other_user = User.objects.create_user(phone_number='other_oi2', name='Other OI2', password='pw')
        other_order = Order.objects.create(user=other_user)
        self.client.force_authenticate(user=self.user)
        data = {'order': other_order.pk, 'menu_item': self.menu_item.pk, 'quantity': 1}
        response = self.client.post(self.orderitem_list_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(OrderItem.objects.filter(order=other_order).exists())
        list_response = self.client.get(self.orderitem_list_url)
        # Should only see items belonging to self.user's orders
        self.assertEqual(len(list_response.data), 1)

    def test_update_orderitem_owner(self):
        self.client.force_authenticate(user=self.user)
        url = reverse('orderitem-detail', kwargs={'pk': self.order_item.pk})
        data = {'quantity': 5}
        response = self.client.patch(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.order_item.refresh_from_db()
        self.assertEqual(self.order_item.quantity, 5)

    def test_delete_orderitem_owner(self):
        item_to_delete = OrderItem.objects.create(order=self.order, menu_item=self.menu_item, quantity=1)
        item_pk = item_to_delete.pk
        self.client.force_authenticate(user=self.user)
        url = reverse('orderitem-detail', kwargs={'pk': item_pk})
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(OrderItem.objects.filter(pk=item_pk).exists())

    # Add tests for MenuItemViewSet (Admin only CRUD)
    # Add tests for ReservationsViewSet (Authenticated user CRUD, owner filtering)

