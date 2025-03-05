from django.urls import path
from . import views

urlpatterns = [
    path('create/', views.user_create, name='user_create'),
    path('edit/<int:user_id>/', views.user_edit, name='user_edit'),
    path('delete/<int:user_id>/', views.user_delete, name='user_delete'),
    path('list/', views.user_list, name='user_list'),
    path('login/', views.user_login, name='user_login'),
    path('logout/', views.user_logout, name='user_logout'),
    # Add other user-related URLs here...
]
