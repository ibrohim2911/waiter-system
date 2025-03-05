from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponseForbidden, HttpResponse
from django.contrib import messages
from django.contrib.auth.decorators import login_required, permission_required
from .forms import UserCreationForm, UserEditForm  # In admin.py and views.py

from .models import User
from django.urls import reverse
from django.core.paginator import Paginator

@login_required
@permission_required('user.can_add_users', raise_exception=True)
def user_create(request):
    """View to create new users."""
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            messages.success(request, 'User created successfully.')
            return redirect('user_list')  # Redirect to user list
        else:
          messages.error(request, 'Error when create the user, please review the information.')
    else:
        form = UserCreationForm()
    return render(request, 'user/user_create.html', {'form': form})

@login_required
@permission_required('user.can_edit_users', raise_exception=True)
def user_edit(request, user_id):
    """View to edit an existing user."""
    user = get_object_or_404(User, id=user_id)
    if request.method == 'POST':
        form = UserEditForm(request.POST, instance=user)
        if form.is_valid():
            form.save()
            messages.success(request, 'User updated successfully.')
            return redirect('user_list')  # Redirect to user list
        else:
            messages.error(request, 'Error when update the user, please review the information.')
    else:
        form = UserEditForm(instance=user)
    return render(request, 'user/user_edit.html', {'form': form, 'user': user})

@login_required
@permission_required('user.can_delete_users', raise_exception=True)
def user_delete(request, user_id):
    """View to delete an existing user."""
    user = get_object_or_404(User, id=user_id)
    if request.method == "POST":
      user.delete()
      messages.success(request, 'User deleted successfully.')
      return redirect("user_list")
    return render(request, "user/user_delete.html", {"user": user})

@login_required
@permission_required('user.can_view_reports', raise_exception=True)
def user_list(request):
    """View to list all users."""
    users = User.objects.all()
    paginator = Paginator(users, 10) # Show 10 contacts per page.
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    return render(request, 'user/user_list.html', {'page_obj': page_obj})

# Example Login view
from django.contrib.auth import authenticate, login, logout

def user_login(request):
    if request.method == 'POST':
        phone_number = request.POST.get('phone_number')
        password = request.POST.get('password')
        user = authenticate(request, phone_number=phone_number, password=password)

        if user is not None:
            login(request, user)
            messages.success(request, f'Welcome {user.name}')
            return redirect('user_list')  # Redirect to a success page
        else:
            messages.error(request, 'Invalid phone number or password.')
            return render(request, 'user/user_login.html', {'phone_number':phone_number})
    else:
        return render(request, 'user/user_login.html')

@login_required
def user_logout(request):
    logout(request)
    return redirect('user_login')
