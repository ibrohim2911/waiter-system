from django.db import models
from django.contrib.auth.hashers import make_password, check_password
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager

class UserManager(BaseUserManager):
    def create_user(self, phone_number, password=None, **extra_fields):
        """Creates and saves a User with the given phone_number and password."""
        if not phone_number:
            raise ValueError('The given phone_number must be set')

        user = self.model(phone_number=phone_number, **extra_fields)
        user.set_password(password)  # This is crucial!
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

class User(AbstractBaseUser):
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
        if self.is_superuser:
            return True

        permissions_by_role = {
            'admin': ['can_add_users', 'can_edit_users', 'can_delete_users'],
            'waiter': ['can_take_orders', 'can_view_menu'],
            'superadmin': ['can_add_users', 'can_edit_users','can_delete_users']
        }

        if self.role in permissions_by_role:
            return perm in permissions_by_role[self.role]

        return False

    def has_module_perms(self, app_label):
        if self.is_superuser:
            return True

        app_permissions_by_role = {
            'admin': {'user', 'order'},
            'waiter': {'order'},
            'superadmin': {'user', 'order'}
        }
        if self.role in app_permissions_by_role:
            return app_label in app_permissions_by_role[self.role]

        return False
