from django import forms
from django.contrib.auth.forms import UserCreationForm as DjangoUserCreationForm  # For reference
from django.contrib.auth.forms import UserChangeForm as DjangoUserChangeForm    #For reference
from .models import User
from django.core.exceptions import ValidationError

class UserCreationForm(forms.ModelForm):
    password2 = forms.CharField(label="Confirm Password", widget=forms.PasswordInput)

    class Meta:
        model = User
        fields = ('name', 'phone_number', 'email', 'password', 'password2', 'role')

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get("password")
        password2 = cleaned_data.get("password2")

        if password and password2 and password != password2:
            raise ValidationError("Passwords do not match")

        return cleaned_data

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data["password"])
        if commit:
            user.save()
        return user

class LoginForm(forms.Form):
    phone_number = forms.CharField(max_length=20)
    password = forms.CharField(widget=forms.PasswordInput)

class UserEditForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ('name', 'phone_number', 'email', 'role')
