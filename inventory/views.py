from django.shortcuts import render
from django.urls import reverse_lazy
from django.views.generic import ListView,DetailView,CreateView,UpdateView,DeleteView
from .models import Inventory, Table
from django.contrib.auth.mixins import LoginRequiredMixin


# Inventory Views
class InventoryListView(LoginRequiredMixin, ListView):
    model = Inventory
    template_name = "inventory/inventory_list.html"
    context_object_name = "inventories"


class InventoryDetailView(LoginRequiredMixin, DetailView):
    model = Inventory
    template_name = "inventory/inventory_detail.html"
    context_object_name = "inventory"


class InventoryCreateView(LoginRequiredMixin, CreateView):
    model = Inventory
    fields = ["name", "quantity", "unit_of_measure", "description","price"]
    template_name = "inventory/inventory_form.html"
    success_url = reverse_lazy("inventory:inventory_list")


class InventoryUpdateView(LoginRequiredMixin, UpdateView):
    model = Inventory
    fields = ["name", "quantity", "unit_of_measure", "description","price"]
    template_name = "inventory/inventory_form.html"
    success_url = reverse_lazy("inventory:inventory_list")


class InventoryDeleteView(LoginRequiredMixin, DeleteView):
    model = Inventory
    template_name = "inventory/inventory_confirm_delete.html"
    success_url = reverse_lazy("inventory:inventory_list")

# Table Views
class TableListView(LoginRequiredMixin, ListView):
    model = Table
    template_name = "inventory/table_list.html"
    context_object_name = "tables"

class TableDetailView(LoginRequiredMixin, DetailView):
    model = Table
    template_name = "inventory/table_detail.html"
    context_object_name = "table"
    
class TableCreateView(LoginRequiredMixin, CreateView):
    model = Table
    fields = ["name","location", "is_available", "capacity"]
    template_name = "inventory/table_form.html"
    success_url = reverse_lazy("inventory:table_list")

class TableUpdateView(LoginRequiredMixin, UpdateView):
    model = Table
    fields = ["table_number", "capacity"]
    template_name = "inventory/table_form.html"
    success_url = reverse_lazy("inventory:table_list")

class TableDeleteView(LoginRequiredMixin, DeleteView):
    model = Table
    template_name = "inventory/table_confirm_delete.html"
    success_url = reverse_lazy("inventory:table_list")
