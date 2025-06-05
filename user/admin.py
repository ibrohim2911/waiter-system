# user/admin.py
from django.contrib import admin
from django.contrib.auth.hashers import make_password # Import hasher
from .models import User
from django import forms

# Custom Form to handle PIN setting in Admin
class UserAdminForm(forms.ModelForm):
    # Add fields for setting/changing PIN without showing the hash
    pin_change = forms.CharField(
        label="Change PIN",
        required=False,
        widget=forms.PasswordInput(render_value=False), # Use password widget for obscurity
        help_text="Enter a new PIN to change it. Leave blank to keep current PIN."
    )
    pin_confirm = forms.CharField(
        label="Confirm PIN",
        required=False,
        widget=forms.PasswordInput(render_value=False),
        help_text="Confirm the new PIN."
    )

    class Meta:
        model = User
        fields = '__all__' # Include all model fields

    def clean(self):
        cleaned_data = super().clean()
        pin_change = cleaned_data.get("pin_change")
        pin_confirm = cleaned_data.get("pin_confirm")

        if pin_change and pin_change != pin_confirm:
            raise forms.ValidationError("PINs do not match.")
        return cleaned_data

    def save(self, commit=True):
        user = super().save(commit=False)
        pin_change = self.cleaned_data.get("pin_change")
        if pin_change:
            # Use the model's set_pin method to handle hashing
            user.set_pin(pin_change)
        if commit:
            user.save()
            # Need to save m2m fields if form handles them (not applicable here)
            # self.save_m2m()
        return user


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    form = UserAdminForm # Use the custom form
    list_display = ('name', 'phone_number', 'email', 'role', 'has_pin_set', 'is_staff', 'is_active', 'is_superuser') # Added has_pin_set
    list_filter = ('role', 'is_staff', 'is_active', 'is_superuser')

    # Separate fieldsets for better organization
    fieldsets = (
        (None, {'fields': ('phone_number',)}), # Password handled by AbstractBaseUser admin
        ('Personal Info', {'fields': ('name', 'email')}),
        ('Role & Status', {'fields': ('role', 'is_active')}),
        ('PIN Management', {'fields': ('pin_change', 'pin_confirm')}), # Use custom form fields
        ('Permissions', {'fields': ('is_staff', 'is_superuser', 'groups', 'user_permissions')}), # Add standard permissions
    )
    # Fieldsets for adding a new user (password is required here)
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('name', 'phone_number', 'email', 'role', 'pin_change', 'pin_confirm')} # Add PIN fields to creation form too
        ),
    )
    search_fields = ('phone_number', 'name', 'email')
    ordering = ('name',)
    filter_horizontal = ('groups', 'user_permissions',) # Better widget for permissions

    # Method to display in list_display if PIN is set
    def has_pin_set(self, obj):
        return bool(obj.pin)
    has_pin_set.boolean = True # Show as checkmark icon
    has_pin_set.short_description = 'PIN Set?' # Column header
