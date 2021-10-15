from rest_framework import serializers

from openforms.emails.models import ConfirmationEmailTemplate


class ConfirmationEmailTemplateSerializer(serializers.ModelSerializer):
    class Meta:
        model = ConfirmationEmailTemplate
        fields = (
            "subject",
            "content",
        )
