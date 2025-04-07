from django.urls import path
from . import views

app_name = 'inventory'
urlpatterns = [
    # Inventory URLs
    path('inventories/', views.InventoryListView.as_view(), name='inventory_list'),
    path('inventories/<int:pk>/', views.InventoryDetailView.as_view(), name='inventory_detail'),
    path('inventories/create/', views.InventoryCreateView.as_view(), name='inventory_create'),
    path('inventories/<int:pk>/update/', views.InventoryUpdateView.as_view(), name='inventory_update'),
    path('inventories/<int:pk>/delete/', views.InventoryDeleteView.as_view(), name='inventory_delete'),
    #table urls
    path('tables/', views.TableListView.as_view(), name='table_list'),
    path('tables/<int:pk>/', views.TableDetailView.as_view(), name='table_detail'),
    path('tables/create/', views.TableCreateView.as_view(), name='table_create'),
    path('tables/<int:pk>/update/', views.TableUpdateView.as_view(), name='table_update'),
    path('tables/<int:pk>/delete/', views.TableDeleteView.as_view(), name='table_delete'),

]
