from django.shortcuts import render
from django.urls import reverse_lazy
from django.views.generic import ListView,DetailView,CreateView,UpdateView,DeleteView
from .models import Order, MenuItem, OrderItem, Reservations
from django.contrib.auth.mixins import LoginRequiredMixin

# Order Views
class OrderListView(LoginRequiredMixin, ListView):
    model = Order
    template_name = "order/order_list.html"
    context_object_name = "orders"


class OrderDetailView(LoginRequiredMixin, DetailView):
    model = Order
    template_name = "order/order_detail.html"
    context_object_name = "order"


class OrderCreateView(LoginRequiredMixin, CreateView):
    model = Order
    fields = ["user", "order_status", "table"]  # Specify the fields to include in the form
    template_name = "order/order_form.html"
    success_url = reverse_lazy("order:order_list")


class OrderUpdateView(LoginRequiredMixin, UpdateView):
    model = Order
    fields = ["order_status", "table"]  # Specify the fields to include in the form
    template_name = "order/order_form.html"
    success_url = reverse_lazy("order:order_list")


class OrderDeleteView(LoginRequiredMixin, DeleteView):
    model = Order
    template_name = "order/order_delete.html"
    success_url = reverse_lazy("order:order_list")


# MenuItem Views
class MenuItemListView(LoginRequiredMixin, ListView):
    model = MenuItem
    template_name = "order/menuitem_list.html"
    context_object_name = "menu_items"


class MenuItemDetailView(LoginRequiredMixin, DetailView):
    model = MenuItem
    template_name = "order/menuitem_detail.html"
    context_object_name = "menu_item"


class MenuItemCreateView(LoginRequiredMixin, CreateView):
    model = MenuItem
    fields = ["name", "description", "price", "category", "is_available"]
    template_name = "order/menuitem_form.html"
    success_url = reverse_lazy("order:menuitem_list")


class MenuItemUpdateView(LoginRequiredMixin, UpdateView):
    model = MenuItem
    fields = ["name", "description", "price", "category", "is_available"]
    template_name = "order/menuitem_form.html"
    success_url = reverse_lazy("order:menuitem_list")


class MenuItemDeleteView(LoginRequiredMixin, DeleteView):
    model = MenuItem
    template_name = "order/menuitem_confirm_delete.html"
    success_url = reverse_lazy("order:menuitem_list")


# OrderItem Views
class OrderItemListView(LoginRequiredMixin, ListView):
    model = OrderItem
    template_name = "order/orderitem_list.html"
    context_object_name = "order_items"


class OrderItemDetailView(LoginRequiredMixin, DetailView):
    model = OrderItem
    template_name = "order/orderitem_detail.html"
    context_object_name = "order_item"


class OrderItemCreateView(LoginRequiredMixin, CreateView):
    model = OrderItem
    fields = ["order", "menu_item", "quantity"]
    template_name = "order/orderitem_form.html"
    success_url = reverse_lazy("order:orderitem_list")


class OrderItemUpdateView(LoginRequiredMixin, UpdateView):
    model = OrderItem
    fields = ["order", "menu_item", "quantity"]
    template_name = "order/orderitem_form.html"
    success_url = reverse_lazy("order:orderitem_list")


class OrderItemDeleteView(LoginRequiredMixin, DeleteView):
    model = OrderItem
    template_name = "order/orderitem_confirm_delete.html"
    success_url = reverse_lazy("order:orderitem_list")


# Reservations Views
class ReservationsListView(LoginRequiredMixin, ListView):
    model = Reservations
    template_name = "order/reservations_list.html"
    context_object_name = "reservations"


class ReservationsDetailView(LoginRequiredMixin, DetailView):
    model = Reservations
    template_name = "order/reservations_detail.html"
    context_object_name = "reservation"


class ReservationsCreateView(LoginRequiredMixin, CreateView):
    model = Reservations
    fields = ["user", "reservation_time", "amount_of_customers", "status", "table"]
    template_name = "order/reservations_form.html"
    success_url = reverse_lazy("order:reservations_list")


class ReservationsUpdateView(LoginRequiredMixin, UpdateView):
    model = Reservations
    fields = ["reservation_time", "amount_of_customers", "status", "table"]
    template_name = "order/reservations_form.html"
    success_url = reverse_lazy("order:reservations_list")


class ReservationsDeleteView(LoginRequiredMixin, DeleteView):
    model = Reservations
    template_name = "order/reservations_confirm_delete.html"
    success_url = reverse_lazy("order:reservations_list")

