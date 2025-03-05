from django.contrib import admin
from .models import User

@admin.register(User) # More concise way to register models
class UserAdmin(admin.ModelAdmin):
    list_display = ('name', 'phone_number', 'email', 'role', 'is_staff', 'is_active', 'is_superuser')
    list_filter = ('role', 'is_staff', 'is_active', 'is_superuser')
    fieldsets = (
        (None, {'fields': ('phone_number', 'password')}),
        ('Personal Info', {'fields': ('name', 'email')}),
        ('Permissions', {'fields': ('is_staff', 'is_superuser')}),  # No groups or permissions here
        ('Role', {'fields': ('role',)}),
        
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('name', 'phone_number', 'email', 'password', 'password2', 'role')
        }),
    )
    ordering = ('name',)

