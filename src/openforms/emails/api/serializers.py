from rest_framework import serializers

from openforms.api.validators import AllOrNoneRequiredFieldsValidator

from ..models import ConfirmationEmailTemplate


class ConfirmationEmailTemplateSerializer(serializers.ModelSerializer):
    class Meta:
        model = ConfirmationEmailTemplate
        fields = ("subject", "content")
        validators = [
            AllOrNoneRequiredFieldsValidator("subject", "content"),
        ]
