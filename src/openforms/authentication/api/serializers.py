from rest_framework import serializers


class LoginLogoSerializer(serializers.Serializer):
    title = serializers.CharField(read_only=True)
    image_src = serializers.URLField(read_only=True)
    href = serializers.URLField(read_only=True)


class LoginOptionSerializer(serializers.Serializer):
    identifier = serializers.CharField(read_only=True)
    label = serializers.CharField(read_only=True)
    url = serializers.URLField(read_only=True)
    logo = LoginLogoSerializer(read_only=True, required=False)
