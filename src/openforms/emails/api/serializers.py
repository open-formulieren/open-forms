from rest_framework import serializers

from openforms.api.validators import AllOrNoneTruthyFieldsValidator
from openforms.translations.api.serializers import ModelTranslationsSerializer

from ..models import ConfirmationEmailTemplate


class ConfirmationEmailTemplateSerializer(serializers.ModelSerializer):
    translations = ModelTranslationsSerializer()

    class Meta:
        model = ConfirmationEmailTemplate
        fields = (
            "subject",
            "content",
            "translations",
        )
        validators = [
            AllOrNoneTruthyFieldsValidator("subject", "content"),
        ]
