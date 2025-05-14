# user/serializers.py
from rest_framework import serializers
from .models import User

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'phone_number', 'name', 'email', 'role', 'is_staff', 'is_active']

class PinLoginSerializer(serializers.Serializer):
    pin = serializers.CharField(write_only=True)

    def validate_pin(self, value):
        """Check for empty pin, to raise a more specific error"""
        if not value:
            raise serializers.ValidationError("PIN cannot be empty.")
        return value
