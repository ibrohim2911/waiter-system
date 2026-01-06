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
    PINs are stored in plaintext, so this backend performs a direct lookup.
    """
    def authenticate(self, request, pin=None, **kwargs):
        if not pin:
            return None

        try:
            # Direct lookup for the user by their plaintext PIN.
            # This assumes PINs are unique across all users who have them.
            return User.objects.get(pin=pin)
        except (User.DoesNotExist, User.MultipleObjectsReturned):
            # If no user is found, or multiple users share the same PIN, authentication fails.
            return None

    # get_user method is inherited from ModelBackend and should work fine.

