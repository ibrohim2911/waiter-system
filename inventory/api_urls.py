# inventory/api_urls.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views # Assuming ViewSets are in views.py

router = DefaultRouter()
router.register(r'tables', views.TableViewSet, basename='table')
router.register(r'inventory', views.InventoryViewSet, basename='inventory')
# Register new ViewSets
router.register(r'inventory-usage', views.InventoryUsageViewSet, basename='inventoryusage')
router.register(r'menu-ingredients', views.MenuItemIngredientViewSet, basename='menuitemingredient')

urlpatterns = [
    path('', include(router.urls)),
]
