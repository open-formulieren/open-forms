from rest_framework import serializers

from openforms.api.validators import AllOrNoneRequiredFieldsValidator
from openforms.translations.api.serializers import ModelTranslationsSerializer

from ..models import ConfirmationEmailTemplate


class ConfirmationEmailTemplateSerializer(serializers.ModelSerializer):
    translations = ModelTranslationsSerializer(required=False)

    class Meta:
        model = ConfirmationEmailTemplate
        fields = (
            "subject",
            "content",
            "translations",
        )
        validators = [
            AllOrNoneRequiredFieldsValidator("subject", "content"),
        ]

    def get_model_class(self):
        return self.Meta.model
