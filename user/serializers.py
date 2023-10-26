from django.contrib.auth import get_user_model
from rest_framework import serializers


class UserSerializer(serializers.ModelSerializer):
    """Serializer for User model with password and confirm_password fields."""

    password = serializers.CharField(
        max_length=128,
        min_length=8,
        write_only=True,
        style={"input_type": "password"},
    )
    confirm_password = serializers.CharField(
        max_length=128,
        min_length=8,
        write_only=True,
        style={"input_type": "password"}
    )

    class Meta:
        model = get_user_model()
        fields = ("id", "email", "first_name", "last_name", "password", "confirm_password", "is_staff")
        read_only_fields = ("is_staff",)
        extra_kwargs = {"password": {"write_only": True, "min_length": 5}}

    def validate(self, data):
        """Validate if the passwords match."""
        if data["password"] != data["confirm_password"]:
            raise serializers.ValidationError("The passwords do not match.")
        return data

    def create(self, validated_data):
        """Create a new user with the validated data."""
        validated_data.pop("confirm_password")
        return get_user_model().objects.create_user(**validated_data)

    def update(self, instance, validated_data):
        """Update an existing user with the validated data."""
        password = validated_data.pop("password", None)
        confirm_password = validated_data.pop("confirm_password", None)

        if password and confirm_password and password == confirm_password:
            instance.set_password(password)
        elif password and confirm_password and password != confirm_password:
            raise serializers.ValidationError("The passwords do not match.")

        return super().update(instance, validated_data)
