from rest_framework import serializers


class ConfirmationEmailTemplateSerializer(serializers.Serializer):
    subject = serializers.CharField(max_length=1000, required=False, allow_blank=True)
    content = serializers.CharField(required=False, allow_blank=True)
