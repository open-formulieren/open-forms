from rest_framework import serializers

from ..models import ConfirmationEmailTemplate


class ConfirmationEmailTemplateSerializer(serializers.ModelSerializer):
    class Meta:
        model = ConfirmationEmailTemplate
        fields = (
            "subject",
            "content",
        )
