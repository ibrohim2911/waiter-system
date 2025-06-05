# user/backends.py
from django.contrib.auth.backends import ModelBackend
from django.contrib.auth import get_user_model
from django.db.models import Q
from django.contrib.auth.hashers import check_password

User = get_user_model()

class PhonePasswordAuthBackend(ModelBackend):
    """
    Authenticates users based on phone_number and password.
    This handles standard logins, including the admin interface.
    """
    def authenticate(self, request, username=None, password=None, **kwargs):
        # 'username' here is the value passed by the login form,
        # which corresponds to AUTH_USER_MODEL.USERNAME_FIELD ('phone_number')
        phone_number = username
        try:
            user = User.objects.get(phone_number=phone_number)
            # Use the user model's check_password method
            if user.check_password(password) and self.user_can_authenticate(user):
                return user
        except User.DoesNotExist:
            # Run the default password hasher once to reduce timing attacks
            User().set_password(password)
        return None

    # get_user method is inherited from ModelBackend and should work fine.


class PinOnlyAuthBackend(ModelBackend):
    """
    Authenticates users based solely on a unique PIN.
    PIN login is restricted to 'waiter' and 'accountant' roles.
    """
    def authenticate(self, request, pin=None, **kwargs):
        if not pin: # Check for None or empty string
            return None

        # --- CRITICAL FIX: Find user by checking PIN correctly ---
        # We cannot filter directly on the hashed pin. We must iterate.
        possible_users = User.objects.filter(
            Q(role='waiter') | Q(role='accountant'),
            is_active=True
        ).exclude(pin__isnull=True).exclude(pin__exact='') # Optimization: only check users with a PIN set

        for user in possible_users:
            if user.check_pin(pin):
                # Found the user with the matching PIN
                return user

        # If loop finishes without finding a match
        # Optionally run a hasher once for timing consistency, though less critical here
        # User().set_password(pin)
        return None
        # --- End Critical Fix ---

    # get_user method is inherited from ModelBackend and should work fine.

