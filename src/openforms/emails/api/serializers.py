from rest_framework import serializers

from openforms.api.validators import AllOrNoneRequiredFieldsValidator
from openforms.translations.api.serializers import (
    DefaultTranslationValueSerializerMixin,
    ModelTranslationsSerializer,
)

from ..models import ConfirmationEmailTemplate


class ConfirmationEmailTemplateSerializer(
    DefaultTranslationValueSerializerMixin, serializers.ModelSerializer
):
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
