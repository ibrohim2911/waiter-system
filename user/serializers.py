# user/serializers.py
from rest_framework import serializers
from .models import User
from django.contrib.auth.password_validation import validate_password

class UserSerializer(serializers.ModelSerializer):
    # Allow setting password and pin when creating/updating users
    password = serializers.CharField(write_only=True, required=False, allow_null=True)
    pin = serializers.CharField(write_only=True, required=False, allow_null=True)

    class Meta:
        model = User
        fields = ['id', 'phone_number', 'name', 'email', 'role', 'is_staff', 'is_active', 'password', 'pin']

    def validate_password(self, value):
        if value:
            validate_password(value)
        return value

    def create(self, validated_data):
        password = validated_data.pop('password', None)
        pin = validated_data.pop('pin', None)
        user = User(**validated_data)
        if password:
            user.set_password(password)
        else:
            user.set_unusable_password()
        # handle pin
        if pin is not None:
            user.set_pin(pin)
        user.save()
        return user

    def update(self, instance, validated_data):
        password = validated_data.pop('password', None)
        pin = validated_data.pop('pin', None)

        for attr, value in validated_data.items():
            setattr(instance, attr, value)

        if password:
            instance.set_password(password)
        if pin is not None:
            instance.set_pin(pin)

        instance.save()
        return instance

class PinLoginSerializer(serializers.Serializer):
    pin = serializers.CharField(write_only=True)

    def validate_pin(self, value):
        """Check for empty pin, to raise a more specific error"""
        if not value:
            raise serializers.ValidationError("PIN cannot be empty.")
        return value
class ChangePasswordSerializer(serializers.Serializer):
    """
    Serializer for password change endpoint.
    """
    old_password = serializers.CharField(required=True, write_only=True)
    new_password = serializers.CharField(required=True, write_only=True)
    confirm_password = serializers.CharField(required=True, write_only=True)

    def validate_new_password(self, value):
        validate_password(value)
        return value

    def validate(self, data):
        if data['new_password'] != data['confirm_password']:
            raise serializers.ValidationError({"new_password": "New passwords must match."})

        user = self.context['request'].user
        if not user.check_password(data.get('old_password')):
            raise serializers.ValidationError({"old_password": "Wrong password."})

        return data

    def save(self, **kwargs):
        user = self.context['request'].user
        user.set_password(self.validated_data['new_password'])
        user.save()
