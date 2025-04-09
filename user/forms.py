# c:\Users\User\Desktop\waiter-system\user\forms.py
from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import UserCreationForm as BaseUserCreationForm
# REMOVE AuthenticationForm imports
# from django.contrib.auth.forms import AuthenticationForm as BaseAuthenticationForm
# from django.forms import CharField

User = get_user_model()

# Keep UserCreationForm - might be useful for admin or custom API endpoint
class UserCreationForm(BaseUserCreationForm):
    confirm_password = forms.CharField(widget=forms.PasswordInput)
    role = forms.ChoiceField(choices=User.ROLE_CHOICES, required=True)

    class Meta(BaseUserCreationForm.Meta):
        model = User
        fields = ('phone_number', 'name', 'email', 'role')

    def clean(self):
        """Check that the two password entries match."""
        cleaned_data = super().clean()
        password = cleaned_data.get("password")
        confirm_password = cleaned_data.get("confirm_password")

        if password and confirm_password and password != confirm_password:
            self.add_error(None, "Passwords do not match")

        return cleaned_data

    def save(self, commit=True):
        user = super().save(commit=False)
        if 'role' in self.cleaned_data:
             user.role = self.cleaned_data['role']
        if commit:
            user.save()
        return user
