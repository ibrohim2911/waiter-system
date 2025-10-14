# user/models.py
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.db import models
from django.utils import timezone
# Import password hashing functions
from django.contrib.auth.hashers import make_password, check_password

class UserManager(BaseUserManager):
    def create_user(self, phone_number, name, password=None, **extra_fields):
        """Creates and saves a User with the given phone_number, name and password."""
        if not phone_number:
            raise ValueError('The Phone Number field must be set')
        if not name:
            raise ValueError('The Name field must be set')

        extra_fields.setdefault('role', 'customer')

        user = self.model(phone_number=phone_number, name=name, **extra_fields)
        # Only set password if one is provided (allows creating users who might only use PIN)
        if password:
            user.set_password(password)
        else:
            # Set an unusable password if none is given initially
            # Useful for PIN-only users or users created via other means
            user.set_unusable_password()
        user.save(using=self._db)
        return user

    def create_superuser(self, phone_number, name, password=None, **extra_fields):
        """Creates and saves a superuser with the given phone_number, name and password."""
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('role', 'admin')

        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')
        if extra_fields.get('role') != 'admin':
             raise ValueError('Superuser must have role="admin".')
        # Ensure superusers always have a password
        if not password:
            raise ValueError('Superuser must have a password.')

        return self.create_user(phone_number, name, password, **extra_fields)

class User(AbstractBaseUser, PermissionsMixin):
    ROLE_CHOICES = (
        ('admin', 'Admin'),
        ('waiter', 'Waiter'),
        ('accountant', 'Accountant'),
    )

    phone_number = models.CharField(max_length=20, unique=True)
    name = models.CharField(max_length=255)
    email = models.EmailField(unique=True, blank=True, null=True)
    role = models.CharField(max_length=50, choices=ROLE_CHOICES, default='waiter')

    # --- NEW PIN FIELD ---
    # Store hashed PIN. Allow blank/null for users who don't use PIN login (customers/admins).
    pin = models.CharField(max_length=128, blank=True, null=True, verbose_name="PIN Hash")
    # ---------------------

    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    date_joined = models.DateTimeField(default=timezone.now)

    objects = UserManager()

    USERNAME_FIELD = 'phone_number'
    REQUIRED_FIELDS = ['name']

    def __str__(self):
        return f"{self.name} ({self.phone_number})"

    # --- NEW PIN METHODS ---
    def set_pin(self, raw_pin):
        """
        Hashes the raw PIN and sets it on the user.
        Never store raw PINs!
        """
        if not raw_pin:
            self.pin = None
        else:
            # Use Django's standard password hashing for the PIN
            self.pin = make_password(str(raw_pin)) # Ensure it's a string

    def check_pin(self, raw_pin):
        """
        Checks if the raw PIN matches the stored hash.
        Returns True if it matches, False otherwise.
        """
        if not self.pin or not raw_pin:
            return False
        return check_password(str(raw_pin), self.pin) # Ensure raw_pin is string
    # ----------------------

    # Note: We rely on AbstractBaseUser's set_password and check_password for the main password field.
