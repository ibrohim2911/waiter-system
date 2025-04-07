from django.urls import path
from . import views

app_name = 'user'
urlpatterns = [
    path('users/', views.user_list_view, name='user_list'),
    path('users/add/', views.add_user_view, name='add_user'),
    path('users/delete/<int:user_id>', views.delete_user_view, name='delete_user'),
    # Authentication URLs
    path('login/', views.UserLoginView.as_view(), name='login'),
    path('logout/', views.UserLogoutView.as_view(), name='logout'),
    path('register/', views.UserRegistrationView.as_view(), name='register'),
]
