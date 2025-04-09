# user/models.py
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin # Import PermissionsMixin
from django.db import models
from django.utils import timezone
# Remove unused hashing imports if not needed elsewhere in this file
# from django.contrib.auth.hashers import make_password, check_password

class UserManager(BaseUserManager):
    def create_user(self, phone_number, name, password=None, **extra_fields):
        """Creates and saves a User with the given phone_number, name and password."""
        if not phone_number:
            raise ValueError('The Phone Number field must be set')
        # FIX: Add validation for name
        if not name:
            raise ValueError('The Name field must be set')

        # Normalize phone number if needed
        # phone_number = self.normalize_phone(phone_number)

        # Set default role if not provided, ensuring it's 'customer' for regular users
        extra_fields.setdefault('role', 'customer')

        user = self.model(phone_number=phone_number, name=name, **extra_fields)
        user.set_password(password) # Use the built-in method from AbstractBaseUser
        user.save(using=self._db)
        return user

    def create_superuser(self, phone_number, name, password=None, **extra_fields):
        """Creates and saves a superuser with the given phone_number, name and password."""
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        # FIX: Explicitly set role to 'admin' for superuser
        extra_fields.setdefault('role', 'admin')

        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')
        # FIX: Ensure role is admin for superuser creation consistency
        if extra_fields.get('role') != 'admin':
             raise ValueError('Superuser must have role="admin".')

        # Pass name explicitly as it's required by create_user now
        return self.create_user(phone_number, name, password, **extra_fields)

# Inherit from PermissionsMixin to get standard permission fields/methods
class User(AbstractBaseUser, PermissionsMixin):
    # FIX: Add 'customer' and ensure choices match usage
    ROLE_CHOICES = (
        ('admin', 'Admin'),
        ('waiter', 'Waiter'),
        ('kitchen', 'Kitchen Staff'), # Assuming kitchen role exists
        ('customer', 'Customer'),
        # ('superadmin', 'Superadmin'), # Remove if 'admin' with is_superuser=True covers this
        # ('accauntant', 'Accauntant'), # Correct spelling to 'accountant' if used
    )

    phone_number = models.CharField(max_length=20, unique=True) # Increased length slightly
    name = models.CharField(max_length=255)
    email = models.EmailField(unique=True, blank=True, null=True) # Optional email

    # FIX: Set default role to 'customer'
    role = models.CharField(max_length=50, choices=ROLE_CHOICES, default='customer')

    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False) # Staff can access admin site
    # is_superuser field is provided by PermissionsMixin

    # REMOVE explicit password field - AbstractBaseUser handles it
    # password = models.CharField(max_length=255)

    date_joined = models.DateTimeField(default=timezone.now)
    # Remove created_at/updated_at if date_joined is sufficient
    # created_at = models.DateTimeField(auto_now_add=True)
    # updated_at = models.DateTimeField(auto_now=True)

    objects = UserManager()

    USERNAME_FIELD = 'phone_number'
    REQUIRED_FIELDS = ['name'] # Name is required for createsuperuser command

    # FIX: Update __str__ method
    def __str__(self):
        return f"{self.name} ({self.phone_number})"

    # REMOVE set_password and check_password overrides - use built-in ones
    # def set_password(self, raw_password):
    #     self.password = make_password(raw_password)
    #
    # def check_password(self, raw_password):
    #     return check_password(raw_password, self.password)

    # REMOVE custom has_perm and has_module_perms unless absolutely necessary
    # Rely on PermissionsMixin and standard Django permissions (is_staff, is_superuser)
    # If you keep them, ensure they are correct and match your intent.
    # The simple versions below rely on staff/superuser status.

    # def has_perm(self, perm, obj=None):
    #     "Does the user have a specific permission?"
    #     # Simplest possible answer: Yes, always for active superusers
    #     if self.is_active and self.is_superuser:
    #         return True
    #     # Otherwise, rely on standard permission system (or add role checks)
    #     return self._user_has_perm(user=self, perm=perm, obj=obj) # Example using internal check

    # def has_module_perms(self, app_label):
    #     "Does the user have permissions to view the app `app_label`?"
    #     # Simplest possible answer: Yes, for active superusers or staff
    #     if self.is_active and self.is_superuser:
    #         return True
    #     return self.is_staff # Allow staff basic access
