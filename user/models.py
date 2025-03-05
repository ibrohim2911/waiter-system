from django.db import models
from django.contrib.auth.hashers import make_password, check_password
from django.core.exceptions import ValidationError
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager

class UserManager(BaseUserManager):
    def create_user(self, phone_number, password=None, **extra_fields):
        """Creates and saves a User with the given phone_number and password."""
        if not phone_number:
            raise ValueError('The given phone_number must be set')

        user = self.model(phone_number=phone_number, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, phone_number, password=None, **extra_fields):
        """Creates and saves a superuser with the given phone_number and password."""
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)

        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')

        return self.create_user(phone_number, password, **extra_fields)

ROLES = [
    ('admin', 'Admin'),
    ('waiter', 'Waiter'),
    ('superadmin', 'Superadmin'),
    ('accauntant', 'Accauntant'),
]

class User(AbstractBaseUser): #Removed PermissionsMixin
    name = models.CharField(max_length=200)
    phone_number = models.CharField(max_length=20, unique=True)
    email = models.EmailField(unique=True, blank=True, null=True)
    role = models.CharField(max_length=50, choices=ROLES, default='waiter')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    password = models.CharField(max_length=255)

    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    is_superuser = models.BooleanField(default=False)

    objects = UserManager()

    USERNAME_FIELD = 'phone_number'
    REQUIRED_FIELDS = ['name']

    def __str__(self):
        return self.name

    def set_password(self, raw_password):
        self.password = make_password(raw_password)

    def check_password(self, raw_password):
        return check_password(raw_password, self.password)

    def has_perm(self, perm, obj=None):
      """
      Check if the user has a specific permission.

      For superusers, return True (they have all permissions).
      For other users, check if the permission is in the role's permissions.
      """
      if self.is_superuser:
          return True

      # Example of how you might check permissions based on role
      # You'll need to define your permissions structure somewhere (e.g., a dictionary)
      permissions_by_role = {
          'admin': ['can_add_users', 'can_edit_users', 'can_view_reports'],
          'waiter': ['can_take_orders', 'can_view_menu'],
          'superadmin': ['can_add_users', 'can_edit_users', 'can_view_reports','can_delete_users'],
          'accauntant': ['can_view_reports', 'can_edit_reports'],
          # Add more roles and their permissions here...
      }

      if self.role in permissions_by_role:
          return perm in permissions_by_role[self.role]

      return False  # Default: no permission if role is not defined

    def has_module_perms(self, app_label): 
      """
      Check if the user has permissions to view the app.

      For superusers, return True (they can view all apps).
      For other users, you might need to define app-level permissions as well.
      """
      if self.is_superuser:
          return True

      # Example of how you might check app-level permissions
      # You'll need to define your app permissions structure (e.g., a set or dictionary)
      app_permissions_by_role = {
          'admin': {'user', 'report', 'order'}, # Example: Admin can access 'user' and 'report' apps
          'waiter': {'order'}, #Example: waiter can access the 'order' app
          'superadmin': {'user', 'report', 'order'},# Example: superadmin can access 'user' and 'report' apps
          'accauntant': {'report'}, #Example: accauntant can access the 'report' app
      }
      if self.role in app_permissions_by_role:
        return app_label in app_permissions_by_role[self.role]
      
      return False  # Default: no app permission if role is not defined



