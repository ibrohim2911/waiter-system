# c:\Users\User\Desktop\waiter-system\inventory\tests.py
import decimal
from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from rest_framework.test import APITestCase
from rest_framework import status

from .models import Inventory, Table, MenuItemIngredient, InventoryUsage
try:
    # Import order models needed for signal testing and API tests
    from order.models import MenuItem, Order, OrderItem
except ImportError:
    MenuItem, Order, OrderItem = None, None, None

User = get_user_model()

class InventoryModelTests(TestCase):

    def setUp(self):
        self.item = Inventory.objects.create(
            name="Test Ingredient", quantity=decimal.Decimal('10.0'), unit_of_measure='kg', price=5.00
        )

    def test_inventory_creation(self):
        self.assertEqual(self.item.name, "Test Ingredient")
        self.assertEqual(self.item.quantity, decimal.Decimal('10.00'))

    def test_reduce_quantity_success(self):
        self.item.reduce_quantity(decimal.Decimal('3.0'))
        self.item.refresh_from_db()
        self.assertEqual(self.item.quantity, decimal.Decimal('7.00'))

    def test_reduce_quantity_insufficient(self):
        with self.assertRaises(ValidationError):
            self.item.reduce_quantity(decimal.Decimal('11.0'))
        self.item.refresh_from_db()
        self.assertEqual(self.item.quantity, decimal.Decimal('10.00'))

    def test_increase_quantity(self):
        self.item.increase_quantity(decimal.Decimal('5.0'))
        self.item.refresh_from_db()
        self.assertEqual(self.item.quantity, decimal.Decimal('15.00'))

    def test_is_out_of_stock(self):
        self.assertFalse(self.item.is_out_of_stock())
        self.item.quantity = 0
        self.item.save()
        self.assertTrue(self.item.is_out_of_stock())

    def test_inventory_str(self):
        self.assertEqual(str(self.item), "Test Ingredient")

class TableModelTests(TestCase):
    def test_table_creation(self):
        table = Table.objects.create(name="T1", location="indoor", capacity=4)
        self.assertEqual(table.name, "T1")
        self.assertEqual(table.capacity, 4)
        self.assertTrue(table.is_available)

class InventorySignalTests(TestCase):

    @classmethod
    def setUpTestData(cls):
        if MenuItem is None:
             raise cls.skipTest("Order models not available for signal tests.")

        cls.flour = Inventory.objects.create(name="Flour", quantity=decimal.Decimal('10.0'), unit_of_measure='kg', price=1.0)
        cls.sugar = Inventory.objects.create(name="Sugar", quantity=decimal.Decimal('5.0'), unit_of_measure='kg', price=2.0)
        cls.eggs = Inventory.objects.create(name="Eggs", quantity=decimal.Decimal('12.0'), unit_of_measure='pcs', price=0.5)

        cls.cake = MenuItem.objects.create(name="Cake", price=15.0, category='desserts', is_available=True)
        cls.bread = MenuItem.objects.create(name="Bread", price=5.0, category='mains', is_available=True)

        MenuItemIngredient.objects.create(menu_item=cls.cake, inventory=cls.flour, quantity=0.5)
        MenuItemIngredient.objects.create(menu_item=cls.cake, inventory=cls.sugar, quantity=0.3)
        MenuItemIngredient.objects.create(menu_item=cls.cake, inventory=cls.eggs, quantity=2.0)
        MenuItemIngredient.objects.create(menu_item=cls.bread, inventory=cls.flour, quantity=1.0)

    def test_inventory_update_makes_menuitem_unavailable(self):
        self.cake.refresh_from_db()
        self.assertTrue(self.cake.is_available)
        self.sugar.quantity = decimal.Decimal('0.1')
        self.sugar.save()
        self.cake.refresh_from_db()
        self.bread.refresh_from_db()
        self.assertFalse(self.cake.is_available, "Cake should be unavailable when sugar is low")
        self.assertTrue(self.bread.is_available)

    def test_inventory_update_makes_menuitem_available(self):
        self.sugar.quantity = decimal.Decimal('0.1')
        self.sugar.save()
        self.cake.refresh_from_db()
        self.assertFalse(self.cake.is_available)
        self.sugar.quantity = decimal.Decimal('6.0')
        self.sugar.save()
        self.cake.refresh_from_db()
        self.assertTrue(self.cake.is_available, "Cake should become available when sugar is replenished")

    def test_inventory_update_multiple_ingredients(self):
        self.eggs.quantity = decimal.Decimal('1.0')
        self.eggs.save()
        self.cake.refresh_from_db()
        self.assertFalse(self.cake.is_available)
        self.eggs.quantity = decimal.Decimal('10.0')
        self.eggs.save()
        self.sugar.quantity = decimal.Decimal('0.1')
        self.sugar.save()
        self.cake.refresh_from_db()
        self.assertFalse(self.cake.is_available, "Cake should remain unavailable if another ingredient is low")
        self.sugar.quantity = decimal.Decimal('5.0')
        self.sugar.save()
        self.cake.refresh_from_db()
        self.assertTrue(self.cake.is_available, "Cake should become available when all ingredients are sufficient")

# --- InventoryAPITests --- (Complete)
class InventoryAPITests(APITestCase):

    @classmethod
    def setUpTestData(cls):
        if MenuItem is None or Order is None or OrderItem is None:
             raise cls.skipTest("Order models not available for API tests.")

        cls.user = User.objects.create_user(phone_number='inv_api', name='Inv API', password='pw', role='customer')
        cls.admin_user = User.objects.create_superuser(phone_number='inv_admin', name='Inv Admin', password='pw')

        cls.item1 = Inventory.objects.create(name="API Item 1", quantity=decimal.Decimal('10.0'), unit_of_measure='kg', price=5)
        cls.item2 = Inventory.objects.create(name="API Item 2", quantity=decimal.Decimal('5.0'), unit_of_measure='pcs', price=1)
        cls.table1 = Table.objects.create(name="API T1", location="indoor", capacity=4)
        cls.table2 = Table.objects.create(name="API T2", location="outdoor", capacity=2)
        cls.menu_item1 = MenuItem.objects.create(name="API Menu 1", price=10, category='mains')
        cls.menu_item2 = MenuItem.objects.create(name="API Menu 2", price=8, category='appetizers')
        cls.ingredient_link1 = MenuItemIngredient.objects.create(menu_item=cls.menu_item1, inventory=cls.item1, quantity=0.5)
        cls.ingredient_link2 = MenuItemIngredient.objects.create(menu_item=cls.menu_item1, inventory=cls.item2, quantity=1.0) # item1 uses item1 and item2

        # Create usage for testing list/detail
        cls.test_order = Order.objects.create(user=cls.user)
        cls.test_order_item = OrderItem.objects.create(order=cls.test_order, menu_item=cls.menu_item1, quantity=1)
        try:
            cls.test_usage = InventoryUsage.objects.get(order_item=cls.test_order_item, inventory=cls.item1)
        except InventoryUsage.DoesNotExist:
            cls.test_usage = None # Handle case where signal might not have run in setup

        cls.inventory_list_url = reverse('inventory-list')
        cls.table_list_url = reverse('table-list')
        cls.menuingredient_list_url = reverse('menuitemingredient-list')
        cls.inventoryusage_list_url = reverse('inventoryusage-list')

    # --- Inventory Endpoints ---
    def test_list_inventory_admin(self):
        self.client.force_authenticate(user=self.admin_user)
        response = self.client.get(self.inventory_list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Assuming no pagination for simplicity
        self.assertEqual(len(response.data), 2)
        self.assertTrue(any(item['name'] == self.item1.name for item in response.data))

    def test_list_inventory_non_admin(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.get(self.inventory_list_url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN) # Requires IsAdminUser

    def test_create_inventory_admin(self):
        self.client.force_authenticate(user=self.admin_user)
        data = {'name': 'New API Item', 'quantity': 20.5, 'unit_of_measure': 'l', 'price': 3.50}
        response = self.client.post(self.inventory_list_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(Inventory.objects.filter(name='New API Item').exists())

    def test_update_inventory_admin(self):
        self.client.force_authenticate(user=self.admin_user)
        url = reverse('inventory-detail', kwargs={'pk': self.item1.pk})
        data = {'quantity': 15.0, 'price': 6.00}
        response = self.client.patch(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.item1.refresh_from_db()
        self.assertEqual(self.item1.quantity, decimal.Decimal('15.00'))
        self.assertEqual(self.item1.price, decimal.Decimal('6.00'))

    def test_delete_inventory_admin(self):
        temp_item = Inventory.objects.create(name="ToDelete", quantity=1, unit_of_measure='pcs', price=1)
        self.client.force_authenticate(user=self.admin_user)
        url = reverse('inventory-detail', kwargs={'pk': temp_item.pk})
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Inventory.objects.filter(pk=temp_item.pk).exists())

    # --- Table Endpoints ---
    def test_list_tables_authenticated(self):
        self.client.force_authenticate(user=self.user) # Requires IsAuthenticated
        response = self.client.get(self.table_list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)
        self.assertTrue(any(t['name'] == self.table1.name for t in response.data))

    def test_list_tables_unauthenticated(self):
        response = self.client.get(self.table_list_url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN) # Or 401

    def test_create_table_authenticated(self):
        self.client.force_authenticate(user=self.user) # Assumes IsAuthenticated allows creation
        data = {'name': 'New API Table', 'location': 'outdoor', 'capacity': 6, 'is_available': True}
        response = self.client.post(self.table_list_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(Table.objects.filter(name='New API Table').exists())

    def test_update_table_authenticated(self):
        self.client.force_authenticate(user=self.user) # Assumes IsAuthenticated allows update
        url = reverse('table-detail', kwargs={'pk': self.table1.pk})
        data = {'capacity': 5, 'is_available': False}
        response = self.client.patch(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.table1.refresh_from_db()
        self.assertEqual(self.table1.capacity, 5)
        self.assertFalse(self.table1.is_available)

    def test_delete_table_authenticated(self):
        # Create a temp table to delete
        temp_table = Table.objects.create(name="Delete Me", capacity=1)
        self.client.force_authenticate(user=self.user) # Assumes IsAuthenticated allows delete
        url = reverse('table-detail', kwargs={'pk': temp_table.pk})
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Table.objects.filter(pk=temp_table.pk).exists())

    # --- MenuItemIngredient Endpoints ---
    def test_list_menuingredients_admin(self):
        self.client.force_authenticate(user=self.admin_user)
        response = self.client.get(self.menuingredient_list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2) # Two links created in setup
        self.assertEqual(response.data[0]['inventory'], self.item1.pk)

    def test_list_menuingredients_non_admin(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.get(self.menuingredient_list_url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN) # Requires IsAdminUser

    def test_create_menuingredient_admin(self):
        self.client.force_authenticate(user=self.admin_user)
        # Link item2 to menu_item2
        data = {'menu_item': self.menu_item2.pk, 'inventory': self.item2.pk, 'quantity': 2.5}
        response = self.client.post(self.menuingredient_list_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(
            MenuItemIngredient.objects.filter(menu_item=self.menu_item2, inventory=self.item2).exists()
        )

    def test_update_menuingredient_admin(self):
        self.client.force_authenticate(user=self.admin_user)
        url = reverse('menuitemingredient-detail', kwargs={'pk': self.ingredient_link1.pk})
        data = {'quantity': 0.75} # Update quantity for item1 in menu_item1
        response = self.client.patch(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.ingredient_link1.refresh_from_db()
        self.assertEqual(self.ingredient_link1.quantity, decimal.Decimal('0.750')) # Check precision

    def test_delete_menuingredient_admin(self):
        # Create a temp link to delete
        temp_link = MenuItemIngredient.objects.create(menu_item=self.menu_item2, inventory=self.item1, quantity=1)
        self.client.force_authenticate(user=self.admin_user)
        url = reverse('menuitemingredient-detail', kwargs={'pk': temp_link.pk})
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(MenuItemIngredient.objects.filter(pk=temp_link.pk).exists())

    # --- InventoryUsage Endpoints ---
    def test_list_inventoryusage_admin(self):
        if self.test_usage is None:
            self.skipTest("Skipping usage list test as setup failed to create usage record.")
        self.client.force_authenticate(user=self.admin_user)
        response = self.client.get(self.inventoryusage_list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Should contain at least the usage created in setup
        self.assertTrue(len(response.data) >= 1)
        self.assertTrue(any(u['id'] == self.test_usage.pk for u in response.data))

    def test_list_inventoryusage_non_admin(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.get(self.inventoryusage_list_url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN) # Requires IsAdminUser

    def test_retrieve_inventoryusage_admin(self):
        if self.test_usage is None:
            self.skipTest("Skipping usage retrieve test as setup failed to create usage record.")
        self.client.force_authenticate(user=self.admin_user)
        url = reverse('inventoryusage-detail', kwargs={'pk': self.test_usage.pk})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['id'], self.test_usage.pk)
        self.assertEqual(response.data['inventory'], self.item1.pk)

    def test_cannot_create_inventoryusage_via_api(self):
        self.client.force_authenticate(user=self.admin_user)
        data = {'inventory': self.item1.pk, 'used_quantity': 1.0, 'order_item': self.test_order_item.pk}
        response = self.client.post(self.inventoryusage_list_url, data, format='json')
        # ReadOnlyModelViewSet
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

    def test_cannot_update_inventoryusage_via_api(self):
        if self.test_usage is None:
            self.skipTest("Skipping usage update test as setup failed to create usage record.")
        self.client.force_authenticate(user=self.admin_user)
        url = reverse('inventoryusage-detail', kwargs={'pk': self.test_usage.pk})
        data = {'used_quantity': 5.0}
        response = self.client.patch(url, data, format='json')
        # ReadOnlyModelViewSet
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

    def test_cannot_delete_inventoryusage_via_api(self):
        if self.test_usage is None:
            self.skipTest("Skipping usage delete test as setup failed to create usage record.")
        self.client.force_authenticate(user=self.admin_user)
        url = reverse('inventoryusage-detail', kwargs={'pk': self.test_usage.pk})
        response = self.client.delete(url)
        # ReadOnlyModelViewSet
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

