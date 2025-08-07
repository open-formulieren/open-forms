from rest_framework import serializers

from ..models import User


class UserSerializer(serializers.ModelSerializer):
    full_name = serializers.CharField(source="get_full_name")

    class Meta:  # pyright: ignore[reportIncompatibleVariableOverride]
        model = User
        fields = (
            "username",
            "full_name",
            "first_name",
            "last_name",
        )
