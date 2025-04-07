from django.shortcuts import render, redirect
from django.urls import reverse_lazy
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.contrib.auth.views import LoginView, LogoutView
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.contrib.auth import login
from .models import User
from django.contrib import messages
from .forms import UserCreationForm
from django.contrib.auth.decorators import login_required

# ... other imports ...

@login_required
def user_list_view(request):
    if request.user.has_perm('can_view_users'):  # Check for specific permission
        users = User.objects.all()
        return render(request, 'user_list.html', {'users': users})
    else:
        messages.error(request, "You don't have permission to view users.")
        return redirect('home')
        # or
        # return HttpResponseForbidden("You don't have permission to view users.")

@login_required
def add_user_view(request):
    if request.user.has_perm('can_add_users'):
        # Your logic to add a new user
        if request.method == 'POST':
            #add new user
            return redirect('user_list')
        else:
            return render(request, 'add_user.html')

    else:
        messages.error(request, "You don't have permission to add users.")
        return redirect('home')

@login_required
def delete_user_view(request, user_id):
    if request.user.has_perm('can_delete_users'):
        try:
            user = User.objects.get(id=user_id)
            user.delete()
            messages.success(request, f"User {user.name} deleted.")
        except User.DoesNotExist:
            messages.error(request, "User not found.")
        return redirect('user_list')
    else:
        messages.error(request, "You don't have permission to delete users.")
        return redirect('home')

# Authentication Views

class UserLoginView(LoginView):
    template_name = "user/login.html"
    success_url = reverse_lazy('order_list')

    def form_valid(self, form):
        messages.success(self.request, f'Welcome {self.request.user.name}')
        return super().form_valid(form)

    def form_invalid(self, form):
        messages.error(self.request, 'Invalid phone number or password.')
        return super().form_invalid(form)

class UserLogoutView(LoginRequiredMixin, LogoutView):
    next_page = reverse_lazy("user:login")

class UserRegistrationView(CreateView):
    form_class = UserCreationForm # Use your custom form
    template_name = "user/register.html"
    success_url = reverse_lazy("user:login")
    print(User.password)
    def form_valid(self, form):
        response = super().form_valid(form)
        login(self.request, self.object)
        return response
